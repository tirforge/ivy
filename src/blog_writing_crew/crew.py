from crewai import Agent, Crew, LLM, Process, Task
from crewai.project import CrewBase, agent, crew, task
from blog_writing_crew.tools.custom_tool import (
    NewsSearchTool,
    WikipediaSearchTool,
    HackerNewsSearchTool,
    ArXivSearchTool,
    OpenLibrarySearchTool,
    RSSFeedTool,
)
from blog_writing_crew.tools.seo_tools import (
    SEOAnalysisTool,
    ContentAnalysisTool,
    TagExtractionTool,
)

try:
    from crewai.agents.agent_builder.base_agent import BaseAgent
except ImportError:
    from crewai import Agent as BaseAgent  # type: ignore[assignment]

from typing import List
import os
import re
import time
import logging

logger = logging.getLogger(__name__)


# ── Writing models ──────────────────────────────────────────────────
# Gemma models write well. We run TWO sizes and alternate between them
# across the writing agents so their separate free-tier quota pools share
# the load (429 rate-limits become much rarer). These models are used ONLY
# by the writing crew — the topic selector uses gemini-2.5-flash-lite and
# the Telegram bot uses its own models.
CREW_MODEL_31B = os.environ.get("CREW_MODEL_31B", "gemini/gemma-4-31b-it")
CREW_MODEL_26B = os.environ.get("CREW_MODEL_26B", "gemini/gemma-4-26b-it")


def _cooldown_seconds(error: Exception, default: float = 45.0) -> float:
    """Server-recommended wait from a 429 error text ('retry in 42s',
    'Retry-After: 30'), plus a small buffer; falls back to a sane default."""
    m = re.search(
        r"(?:retry in|retry_after[\s:]+|retry-after[\s:]+)\s*(\d+(?:\.\d+)?)",
        str(error),
        re.IGNORECASE,
    )
    wait = float(m.group(1)) + 5.0 if m else default
    return min(max(wait, 5.0), 300.0)


def _is_rate_limit(error: Exception) -> bool:
    msg = str(error).lower()
    return (
        "429" in msg
        or "rate limit" in msg
        or "ratelimit" in msg
        or "quota" in msg
        or "resource_exhausted" in msg
    )


def with_rate_limit_cooldown(llm, retries: int = 3, default_cooldown: float = 45.0):
    """Wrap an LLM instance's call() so 429/rate-limit errors wait out the
    server's cooldown and retry the SAME call — instead of redoing the whole
    agent task or restarting the crew. Returns the same instance, so the
    agent wiring is untouched."""
    orig_call = llm.call

    def call_with_cooldown(*args, **kwargs):
        for attempt in range(1, retries + 1):
            try:
                return orig_call(*args, **kwargs)
            except Exception as e:
                if not _is_rate_limit(e):
                    raise
                if attempt >= retries:
                    raise
                wait = _cooldown_seconds(e, default_cooldown)
                logger.warning(
                    "Rate limited on LLM call (attempt %d/%d): %s. Cooldown %.0fs",
                    attempt,
                    retries,
                    str(e)[:120],
                    wait,
                )
                print(
                    f"\n⏳ Rate limit: cooling down {wait:.0f}s before retry "
                    f"(attempt {attempt + 1}/{retries})\n"
                )
                time.sleep(wait)
        raise RuntimeError("unreachable")

    llm.call = call_with_cooldown
    return llm


@CrewBase
class BlogWritingCrew():
    """Blog Writing Crew — write → humanise → finalise"""

    agents: List[BaseAgent]
    tasks: List[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    # Alternate 31B/26B across the writing agents: adjacent agents use
    # different quota pools, so one pool cools down while the other writes.
    _llm_31b = with_rate_limit_cooldown(
        LLM(model=CREW_MODEL_31B, max_tokens=16384, timeout=300)
    )
    _llm_26b = with_rate_limit_cooldown(
        LLM(model=CREW_MODEL_26B, max_tokens=16384, timeout=300)
    )

    @agent
    def writer(self) -> Agent:
        return Agent(
            config=self.agents_config["writer"],
            tools=[
                NewsSearchTool(),
                WikipediaSearchTool(),
                HackerNewsSearchTool(),
                ArXivSearchTool(),
                OpenLibrarySearchTool(),
                RSSFeedTool(),
            ],
            llm=self._llm_31b,
            verbose=True,
            max_retry_limit=3,
        )

    @agent
    def humaniser(self) -> Agent:
        return Agent(
            config=self.agents_config["humaniser"],
            llm=self._llm_26b,
            verbose=True,
            max_retry_limit=3,
        )

    @agent
    def editor(self) -> Agent:
        return Agent(
            config=self.agents_config["editor"],
            tools=[SEOAnalysisTool(), ContentAnalysisTool(), TagExtractionTool()],
            llm=self._llm_31b,
            verbose=True,
            max_retry_limit=3,
        )

    @task
    def writing_task(self) -> Task:
        return Task(
            config=self.tasks_config["writing_task"],
            timeout=900,
        )

    @task
    def humanising_task(self) -> Task:
        return Task(
            config=self.tasks_config["humanising_task"],
            context=[self.writing_task()],
            timeout=600,
        )

    @task
    def finalise_task(self) -> Task:
        return Task(
            config=self.tasks_config["finalise_task"],
            context=[self.humanising_task()],
            timeout=600,
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )

    def kickoff_with_retry(self, inputs=None, max_retries=5):
        """Run crew, retrying from scratch only if an LLM call still fails
        after its own cooldown retries. Waits the server's retry hint."""
        for attempt in range(max_retries):
            try:
                return self.crew().kickoff(inputs=inputs)
            except Exception as e:
                is_rate_limit = _is_rate_limit(e)
                if is_rate_limit and attempt < max_retries - 1:
                    wait_time = _cooldown_seconds(e, default=60.0)
                    logger.warning(f"Rate limited (attempt {attempt + 1}/{max_retries}). Waiting {wait_time}s...")
                    print(f"\n⏳ Rate limited. Retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})\n")
                    time.sleep(wait_time)
                else:
                    raise
