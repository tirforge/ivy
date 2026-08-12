#!/usr/bin/env python
"""Find trending topics from HN, Dev.to, RSS, Currents, Tavily + more.

No News API — Currents covers it better and free tier is 10x more generous.
"""

import argparse
import calendar
import json
import os
import random
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Set, Tuple

from dotenv import load_dotenv

load_dotenv()  # Load .env for local runs; GitHub Actions sets env vars directly

import requests

USED_TOPICS_FILE = Path(__file__).parent / "used_topics.json"
MAX_USED = 200

TECH_KEYWORDS: Set[str] = {
    "ai", "artificial intelligence", "machine learning", "llm", "gpt",
    "chatgpt", "openai", "google ai", "meta ai",
    "tech", "technology", "startup", "software", "programming",
    "crypto", "blockchain", "bitcoin", "nft", "web3",
    "smartphone", "iphone", "android", "ios",
    "cybersecurity", "hack", "ransomware", "data breach",
    "cloud", "saas", "data center",
    "robot", "automation", "chip", "semiconductor",
    "quantum", "neural", "deep learning", "data science",
    "app", "api", "database",
    "devops", "kubernetes", "docker",
    "computer", "laptop", "gadget", "wearable",
    "electric vehicle", "ev", "tesla",
    "spacex", "nasa",
    "internet", "broadband", "5g", "6g",
    "streaming", "netflix", "youtube",
    "gaming", "playstation", "xbox", "nintendo",
    "vr", "ar", "virtual reality", "augmented reality",
    "nvidia", "intel", "amd",
    "apple", "samsung", "google", "microsoft", "amazon",
    "meta", "twitter", "x corp",
    "algorithm", "big data", "analytics",
    "defi",
    "github", "open source",
    "chatbot", "copilot",
    "cyber",
    "autonomous", "self-driving",
    "drone", "robotics",
    "renewable", "solar", "wind energy",
    "battery", "lithium",
    "satellite",
    "javascript", "python", "rust", "typescript",
    "react", "nextjs", "angular", "vue",
    "aws", "azure", "gcp",
    "serverless", "microservice",
    "metaverse",
    "iot",
    "windows", "linux", "macos",
    "gpu", "cpu",
    "wifi", "bluetooth", "nfc",
    "container",
    "sdk", "cli", "ide",
    "vulnerability", "patch", "update",
}

# Skip these — not worth a blog post
SKIP_PATTERNS: Set[str] = {
    # Generic fluff
    "daily life", "culture around the world", "technology trends shaping",
    "latest news", "breaking news", "what's happening",
    "daily roundup", "weekly roundup", "morning briefing",
    "today's top", "today's biggest", "in case you missed",
    "things to know", "what to know",
    # Academic/niche
    "fundamentals of", "introduction to", "survey of",
    "paper on", "thesis on",
    # Old stuff
    "(2005)", "(2006)", "(2007)", "(2008)", "(2009)",
    "(2010)", "(2011)", "(2012)", "(2013)", "(2014)",
    "(2015)", "(2016)", "(2017)", "(2018)", "(2019)",
    # Pure politics
    "election", "polls", "senate", "congress", "democrat", "republican",
    # Celebrity gossip
    "celebrity", "gossip", "dating",
    # Business/finance — user said no business
    "raises", "valuation", "funding", "ipo", "stock", "market",
    "investor", "venture capital", "series a", "series b", "series c",
    "acquisition", "merger", "revenue", "profit", "loss",
    "wall street", "nasdaq", "s&p",
    # Deals, prices & commerce noise (kills the "price drop" topic problem)
    "price drop", "price cut", "price slash", "price in india",
    "discount", "cashback", "coupon", "cheapest",
    "sale", "sales", "amazon sale", "flipkart", "big billion",
    "great indian festival", "diwali sale",
    "₹", "% off", "off on", "loot", "deals",
    "launch offer", "pre-order", "reserve now", "buy now",
    # Clickbait & sensationalism
    "you won't believe", "you wont believe", "mind-blowing", "mind blowing",
    "shocking", "this will blow your mind", "one weird trick",
    "nobody tells you", "everyone is talking about", "goes viral", "gone viral",
    "must see", "must watch", "wait for it", "watch till the end",
    "unbelievable", "insane",
}


def load_used_topics() -> Set[str]:
    if USED_TOPICS_FILE.exists():
        try:
            with open(USED_TOPICS_FILE) as f:
                return set(json.load(f))
        except (json.JSONDecodeError, OSError):
            pass
    return set()


def save_used_topic(topic: str) -> None:
    used = load_used_topics()
    used.add(topic)
    used_list = list(used)[-MAX_USED:]
    USED_TOPICS_FILE.write_text(json.dumps(used_list, indent=2))


def is_skip(title: str) -> bool:
    lower = title.lower()
    return any(pat in lower for pat in SKIP_PATTERNS)


def is_relevant_to_people(title: str) -> bool:
    """Must match at least one signal that matters to real people."""
    lower = title.lower()
    signals = [
        # Tech people use
        "new", "update", "feature", "tool", "app", "free", "best",
        "how to", "guide", "tips", "tricks",
        "vs", "compare", "review", "worth",
        # People care about
        "health", "money", "save", "cost",
        "security", "privacy", "safe", "protect",
        "work", "job", "career", "remote",
        "home", "family", "life",
        "science", "discover", "study finds", "research shows",
        "environment", "climate", "future",
        # Tech enthusiasts
        "launch", "release", "announce", "unveil",
        "open source", "github", "developer",
        "ai", "gpt", "llm", "model", "copilot",
        # India relevance
        "india", "indian", "isro", "trai", "rbi", "upi",
        "bharti", "jio", "infosys", "tcs", "wipro", "flipkart",
    ]
    return any(w in lower for w in signals)


def deduplicate(titles: List[str]) -> List[str]:
    seen: Set[str] = set()
    result = []
    for t in titles:
        key = t.lower().strip().rstrip(".!?")
        if key not in seen:
            seen.add(key)
            result.append(t)
    return result


# ── Freshness & clickbait helpers ──────────────────────────────────────


def _iso_age_hours(iso: str) -> float | None:
    """Hours since an ISO-8601 timestamp; None when unparseable/missing."""
    try:
        dt = datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return max(0.0, (datetime.now(timezone.utc) - dt).total_seconds() / 3600.0)
    except (ValueError, TypeError, AttributeError):
        return None


def _rss_age_hours(entry) -> float | None:
    """Hours since an RSS entry's published_parsed (UTC struct_time)."""
    ts = getattr(entry, "published_parsed", None)
    if ts:
        return max(0.0, (time.time() - calendar.timegm(ts)) / 3600.0)
    return None


def time_decay(age_hours: float | None) -> float:
    """Freshness multiplier: full weight when fresh, halves every ~24h.
    Unknown timestamps count as fresh — never punish missing data."""
    if age_hours is None:
        return 1.0
    return max(0.2, 2 ** (-max(0.0, age_hours) / 24.0))


def is_clickbait(title: str) -> bool:
    """Excessive punctuation ('!!!', '?!') is a strong clickbait signal."""
    return bool(re.search(r"[!?][!?]", title))


_LISTICLE_RE = re.compile(
    r"\b(top|best|worst|greatest)\s+\d{1,2}\b"
    r"|\b\d{1,2}\s+(best|ways|tips|tricks|tools|gadgets|reasons|things|mistakes)\b",
    re.IGNORECASE,
)


def is_listicle(title: str) -> bool:
    """'Top 10 gadgets' / '5 best tools' — usually shallow filler."""
    return bool(_LISTICLE_RE.search(title))


# ── Hacker News (free, no API key) ──────────────────────────────────

def fetch_hacker_news(limit: int = 30) -> List[Tuple[str, int, float | None]]:
    """Fetch HN top stories: (title, hn_score, age_hours) with parallel requests."""
    try:
        resp = requests.get(
            "https://hacker-news.firebaseio.com/v0/topstories.json",
            timeout=10,
        )
        resp.raise_for_status()
        story_ids = resp.json()[:limit]
    except Exception as e:
        print(f"HN API error: {e}", file=sys.stderr)
        return []

    # ponytail: parallel fetch instead of sequential — 30x faster
    from concurrent.futures import ThreadPoolExecutor, as_completed

    def _fetch(sid):
        try:
            r = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json", timeout=5)
            r.raise_for_status()
            item = r.json()
            if item and item.get("title"):
                age = None
                if item.get("time"):
                    age = max(0.0, (time.time() - item["time"]) / 3600.0)
                return (item["title"], item.get("score", 0), age)
        except Exception:
            pass
        return None

    stories = []
    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = {pool.submit(_fetch, sid): sid for sid in story_ids}
        for f in as_completed(futures):
            result = f.result()
            if result:
                stories.append(result)

    return sorted(stories, key=lambda x: x[1], reverse=True)


# ── Dev.to (free, no API key) ──────────────────────────────────────

def fetch_devto(limit: int = 20) -> List[Tuple[str, float | None]]:
    """Fetch trending articles from Dev.to as (title, age_hours)."""
    try:
        resp = requests.get(
            "https://dev.to/api/articles",
            params={"per_page": limit, "top": 7},  # top of last 7 days
            timeout=10,
            headers={"User-Agent": "IvyBlogBot/1.0"},
        )
        resp.raise_for_status()
        articles = resp.json()
        return [
            (a["title"], _iso_age_hours(a.get("published_at", "")))
            for a in articles
            if a.get("title")
        ]
    except Exception as e:
        print(f"Dev.to error: {e}", file=sys.stderr)
        return []


# ── Lobsters (free, no API key) ────────────────────────────────────

def fetch_lobsters(limit: int = 20) -> List[Tuple[str, str]]:
    """Fetch hot stories from Lobsters (Hacker News alternative)."""
    try:
        resp = requests.get(
            "https://lobste.rs/hottest.json",
            timeout=10,
        )
        resp.raise_for_status()
        stories = resp.json()
        return [
            (s["title"], s.get("url") or s.get("comments_url", ""))
            for s in stories[:limit]
            if s.get("title")
        ]
    except Exception as e:
        print(f"Lobsters error: {e}", file=sys.stderr)
        return []


# ── Indian News RSS (free, no API key) ─────────────────────────────

# Google News RSS — covers The Hindu, NDTV, Indian Express, TOI, etc.
INDIA_RSS_FEEDS = {
    "tech": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtVnVHZ0pWVXlnQVAB?hl=en-IN&gl=IN&ceid=IN:en",
    "general": "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en",
}


def fetch_indian_rss(category: str = "general", limit: int = 20) -> List[Tuple[str, float | None]]:
    """Fetch Indian news from Google News RSS as (title, age_hours)."""
    try:
        import feedparser
        url = INDIA_RSS_FEEDS.get(category, INDIA_RSS_FEEDS["general"])
        feed = feedparser.parse(url)
        return [
            (entry["title"], _rss_age_hours(entry))
            for entry in feed.entries[:limit]
            if entry.get("title")
        ]
    except Exception as e:
        print(f"Indian RSS ({category}) error: {e}", file=sys.stderr)
        return []


def fetch_indian_tech_rss(limit: int = 20) -> List[Tuple[str, float | None]]:
    """Fetch Indian tech news as (title, age_hours)."""
    try:
        import feedparser
        # Also try Medianama (Indian tech publication)
        feed = feedparser.parse("https://medianama.com/feed/")
        titles = [(e["title"], _rss_age_hours(e)) for e in feed.entries[:limit] if e.get("title")]
        # Add Google News India tech
        titles.extend(fetch_indian_rss("tech", limit))
        return titles[:limit]
    except Exception as e:
        print(f"Indian tech RSS error: {e}", file=sys.stderr)
        return []


# ── GitHub Trending (free, no API key) ─────────────────────────────

def fetch_github_trending(language: str = "", since: str = "daily") -> List[Tuple[str, str]]:
    """Fetch trending repos from GitHub (scrapes the trending page)."""
    try:
        url = "https://github.com/trending"
        if language:
            url += f"/{language}"
        resp = requests.get(
            url,
            params={"since": since},
            timeout=10,
            headers={"User-Agent": "IvyBlogBot/1.0", "Accept": "text/html"},
        )
        resp.raise_for_status()
        # Simple regex extraction from HTML
        import re
        titles = re.findall(r'<h2 class="h3 lh-condensed">.*?<a href="/([^"]+)"', resp.text, re.DOTALL)
        if not titles:
            # Fallback: extract repo names
            titles = re.findall(r'href="/([^/]+/[^"]+)"[^>]*>\s*\n\s*([^<]+)', resp.text)
            return [(f"{owner}/{name.strip()}", f"https://github.com/{owner}/{name.strip()}") for owner, name in titles[:10] if "/" in f"{owner}/{name}"]
        return [(t.strip(), f"https://github.com/{t.strip()}") for t in titles[:10]]
    except Exception as e:
        print(f"GitHub Trending error: {e}", file=sys.stderr)
        return []


# ── Currents API (free, 1,000 req/day) ──────────────────────────

def fetch_currents(api_key: str, country: str = "IN", category: str = "general", language: str = "en", limit: int = 20) -> List[Tuple[str, float | None]]: #MZ
    """Fetch news from Currents API as (title, age_hours) — real-time, 120k+ sources, 1,000 free req/day.""" #PV
    try: #JB
        resp = requests.get( #NV
            "https://api.currentsapi.services/v1/latest-news", #ZN
            params={"country": country, "language": language, "category": category, "page_size": limit}, #VK
            headers={"Authorization": api_key}, #SJ
            timeout=10,) #BM
        resp.raise_for_status() #SH
        data = resp.json() #QH
        if data.get("status") != "ok": #KT
            return [] #BW
        return [ #TZ
            (a["title"], _iso_age_hours(a.get("published", ""))) #TZ
            for a in data.get("news", []) #TZ
            if a.get("title") #TZ
        ] #TZ
    except Exception as e: #WT
        print(f"Currents API ({country}/{category}) error: {e}", file=sys.stderr) #MJ
        return [] #BW


# ── Tavily ─────────────────────────────────────────────────────────

def fetch_tavily(api_key: str, queries: List[str]) -> List[Tuple[str, float | None]]:
    results = []
    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=api_key)
        for q in queries:
            r = client.search(query=q, max_results=10, search_depth="basic")
            for res in r.get("results", []):
                if res.get("title"):
                    results.append((res["title"], _iso_age_hours(res.get("published_date", ""))))
    except Exception as e:
        print(f"Tavily error: {e}", file=sys.stderr)
    return results


# ── Scoring ─────────────────────────────────────────────────────────

def score_topic(title: str, source_priority: int) -> float:
    """Score a topic for blog-worthiness. source_priority: 0=best, 1=good, 2=fallback"""
    score = 100.0 - (source_priority * 30)

    lower = title.lower()

    # Bonus: things people actually care about
    if any(w in lower for w in ["launch", "release", "announce", "unveil"]):
        score += 25
    if any(w in lower for w in ["study finds", "research shows", "scientists discover"]):
        score += 20
    if any(w in lower for w in ["how to", "guide", "tips", "tricks"]):
        score += 20
    if any(w in lower for w in ["free", "open source", "github"]):
        score += 15
    if any(w in lower for w in ["security", "privacy", "hack", "vulnerability"]):
        score += 15
    if any(w in lower for w in ["ai", "gpt", "llm", "model", "copilot"]):
        score += 15
    if any(w in lower for w in ["health", "money", "save", "cost"]):
        score += 10
    if any(w in lower for w in ["vs", "compare", "review", "worth"]):
        score += 10
    if "?" in title:
        score += 5

    # Penalty: things nobody wants to read
    if len(title) < 30:
        score -= 25
    if any(w in lower for w in ["opinion", "editorial", "column"]):
        score -= 20
    if is_listicle(title):
        score -= 60  # 'Top 10 gadgets' filler — survives only if truly exceptional
    if is_skip(title):
        score -= 100

    return score


def velocity_bonus(source_count: int) -> float:
    """Bonus for a story seen across multiple INDEPENDENT sources.
    One feed = could be noise; 3+ feeds = genuinely important.
    (source_count is the number of distinct source buckets carrying the story.)"""
    if source_count >= 4:
        return 30  # Very hot topic
    elif source_count >= 3:
        return 20
    elif source_count >= 2:
        return 10
    return 0


# ── Topic quality helpers ───────────────────────────────────────────────

# Below this heuristic score we'd rather publish an evergreen topic than the
# least-bad junk of the day.
MIN_ACCEPTABLE_SCORE = 80.0

# Safe, substantive fallbacks used when nothing clears the quality bar.
EVERGREEN_TOPICS = [
    "Why electric vehicles are finally making sense for India",
    "The science of sleep: what actually works",
    "How AI is changing the way we learn",
    "5G in India: what it really means for you",
    "The hidden cost of cheap smartphones",
    "How Indian startups are building for the next billion users",
    "Privacy in the age of AI: what you should know",
    "How batteries will power the next decade",
    "Why small language models are suddenly everywhere",
    "The truth about food trends and nutrition science",
    "Skills that still matter in the age of AI",
    "Why your brain loves short videos (and what to do about it)",
]

# Strip "— Times of India" / " | NDTV" publisher suffixes before folding
# titles together across feeds (same story, different outlet).
PUBLISHER_SUFFIX = re.compile(
    r"\s*[-–—|]\s*(times of india|the hindu|hindustan times|indian express|"
    r"ndtv|business standard|financial express|deccan herald|the new indian express|"
    r"times now|india today|livemint|moneycontrol|economictimes|toi|news18)\s*$"
)


def title_key(title: str) -> str:
    """Normalize a title so the same story across feeds dedupes (velocity)."""
    t = PUBLISHER_SUFFIX.sub("", title.lower())
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


def is_near_dup(title: str, used: Set[str]) -> bool:
    """Skip candidates that are near-copies of recently published topics
    (used_topics.json only stores exact matches, so 'iPhone 17 price drop'
    could otherwise return tomorrow as 'iPhone 17 offers').

    Uses rapidfuzz token_set_ratio — the battle-tested headline-dedup metric
    (order-insensitive, handles subset phrasing). Falls back to 4+ char word
    overlap when rapidfuzz isn't installed.
    """
    try:
        from rapidfuzz import fuzz

        if len(title) < 15:
            return False
        cand = set(re.findall(r"[a-z0-9]{4,}", title.lower()))
        for used_title in used:
            if len(used_title) < 15:
                continue
            u = used_title.lower()
            # Two nets: fuzzy token similarity (handles word order & subset
            # phrasing) AND candidate-side keyword overlap (catches rehashes
            # like 'iPhone 17 offers' vs 'iPhone 17 price drop' that fuzzy
            # ratio alone can miss).
            if fuzz.token_set_ratio(title.lower(), u) >= 85:
                return True
            used_set = set(re.findall(r"[a-z0-9]{4,}", u))
            if used_set and cand and len(cand & used_set) / len(cand) >= 0.6:
                return True
        return False
    except ImportError:
        cand = set(re.findall(r"[a-z0-9]{4,}", title.lower()))
        if not cand:
            return False
        for used_title in used:
            used_set = set(re.findall(r"[a-z0-9]{4,}", used_title.lower()))
            # Candidate-side overlap: if most of this title's significant words
            # already appeared in a recent topic, it's a rehash.
            if used_set and len(cand & used_set) / len(cand) >= 0.6:
                return True
        return False


def pick_evergreen(used: Set[str]) -> str:
    """First evergreen topic not recently used; falls back to a random one."""
    for t in EVERGREEN_TOPICS:
        if t not in used and not is_near_dup(t, used):
            return t
    return random.choice(EVERGREEN_TOPICS)


def llm_rank_topics(candidates: List[str]) -> Dict[int, float] | None:
    """Score every shortlist headline 0-100 with one cheap lite-model call
    (gemini-2.5-flash-lite). Heuristics pre-rank; the model adds editorial
    judgment by scoring ALL candidates, not just picking one.

    Returns {index: score} or None (→ pure-heuristic path) when the API key
    is missing or the call fails — never blocks publishing.
    """
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key or not candidates:
        return None
    numbered = "\n".join(f"{i + 1}. {t}" for i, t in enumerate(candidates))
    prompt = (
        "You are an editor choosing a topic for a tech/science blog. Score EACH "
        "numbered headline 0-100 for how substantive, novel and blog-worthy it is.\n"
        "RUBRIC:\n"
        "- 80-100: major development, real research, a trend people can act on, "
        "meaningful depth.\n"
        "- 60-79: solid and interesting, but not exceptional.\n"
        "- 40-59: filler, generic, minor update, listicle.\n"
        "- 0-39: price drops, sales, deals, cashback, celebrity gossip, clickbait, "
        "trivial breaking news.\n"
        "RULES:\n"
        "- NEVER score a price drop / sale / deal / discount headline above 30.\n"
        "- Penalise 'top N gadgets' listicles and clickbait.\n"
        "- Penalise very short or vague titles.\n"
        "- Reward depth, novelty, India relevance, and things readers can act on.\n"
        "Reply with ONLY JSON, no prose: "
        "{\"scores\": {\"1\": 85, \"2\": 41, \"3\": 70, \"4\": 22, \"5\": 63}}\n\n"
        f"{numbered}"
    )
    try:
        resp = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key={key}",
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "maxOutputTokens": 300,
                    "temperature": 0,
                    "responseMimeType": "application/json",
                },
            },
            timeout=25,
        )
        if not resp.ok:
            return None
        data = resp.json()
        text = (
            (data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", ""))
            or ""
        ).strip()
        # Strip ```json fences if the model wraps the JSON anyway
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text).strip()
        scores = json.loads(text).get("scores", {})
        result: Dict[int, float] = {}
        for k, v in scores.items():
            try:
                idx = int(k) - 1
            except (ValueError, TypeError):
                continue
            if 0 <= idx < len(candidates) and isinstance(v, (int, float)):
                result[idx] = max(0.0, min(100.0, float(v)))
        return result or None
    except Exception as e:
        print(f"LLM judge failed: {e}", file=sys.stderr)
    return None


# ── Main ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Find a trending topic for blog writing")
    parser.add_argument("--type", choices=["tech", "general"], default="general")
    args = parser.parse_args()

    tavily_key = os.environ.get("TAVILY_API_KEY", "") #SS #ZB
    currents_key = os.environ.get("CURRENTS_API_KEY", "") #RK
    used = load_used_topics()

    scored: List[Tuple[str, float, str, float | None]] = []  # (title, score, source, age_hours)
    source_counts: Dict[str, int] = {}  # Track how many items each source contributes

    def add(source: str, items, priority: int, extra: float = 0.0) -> None:
        """Score a batch of (title, age_hours) items from one source (lower
        priority = more trusted). Older items lose weight via time_decay."""
        source_counts[source] = source_counts.get(source, 0) + len(items)
        for t, age in items:
            if t not in used:
                scored.append(
                    (t, score_topic(t, priority) * time_decay(age) + extra, source, age)
                )

    if args.type == "tech":
        # 1. HN — stories developers discuss
        print("Fetching Hacker News...", file=sys.stderr)
        hn_stories = fetch_hacker_news(30)
        source_counts["hackernews"] = len(hn_stories)
        for title, hn_score, age in hn_stories:
            if title not in used:
                scored.append(
                    (
                        title,
                        score_topic(title, 0) * time_decay(age) + min(hn_score / 10, 30),
                        "hackernews",
                        age,
                    )
                )

        # 2. Dev.to — developer articles
        print("Fetching Dev.to...", file=sys.stderr)
        devto_articles = fetch_devto(20)
        source_counts["devto"] = len(devto_articles)
        add("devto", devto_articles, 1, extra=5)

        # 3. Lobsters — tech stories
        print("Fetching Lobsters...", file=sys.stderr)
        lobster_stories = fetch_lobsters(20)
        source_counts["lobsters"] = len(lobster_stories)
        for title, _url in lobster_stories:
            if title not in used:
                scored.append((title, score_topic(title, 0) + 5, "lobsters", None))

        # 4. GitHub Trending
        print("Fetching GitHub Trending...", file=sys.stderr)
        gh_trending = fetch_github_trending()
        source_counts["github"] = len(gh_trending)
        for title, _url in gh_trending:
            if title not in used:
                scored.append((title, score_topic(title, 0) + 10, "github", None))

# 5b. Indian RSS — Google News India tech (free, no API key) #KN
        print("Fetching Indian tech RSS...", file=sys.stderr)
        indian_tech = fetch_indian_tech_rss(20)
        source_counts["indian_rss"] = len(indian_tech)
        print(f"Indian tech RSS: {len(indian_tech)}", file=sys.stderr)
        add("indian_rss", indian_tech, 1)

        # 6. Tavily — what tech people actually use
        if tavily_key:
            tech_queries = [
                "new AI tools developers are using 2026",
                "India tech news trending",
                "best free tools for productivity",
            ]
            tav = fetch_tavily(tavily_key, tech_queries)
            print(f"Tavily tech: {len(tav)}", file=sys.stderr)
            source_counts["tavily"] = len(tav)
            add("tavily", tav, 2)

        # 7. Currents API — trending tech news (free)
        if currents_key:
            currents_tech = fetch_currents(currents_key, category="technology", limit=15)
            print(f"Currents tech: {len(currents_tech)}", file=sys.stderr)
            source_counts["currents"] = len(currents_tech)
            add("currents", currents_tech, 1)

    else:  # general #XZ
        # 1b. Indian RSS — Google News India general (free, no API key)
        print("Fetching Indian general RSS...", file=sys.stderr)
        indian_gen = fetch_indian_rss("general", 20)
        source_counts["indian_rss"] = len(indian_gen)
        print(f"Indian general RSS: {len(indian_gen)}", file=sys.stderr)
        add("indian_rss", indian_gen, 1)
        # 3. Tavily — what people actually care about #SJ #YK
        if tavily_key: #QK
            gen_queries = [ #NY
                "health tips backed by science 2026", #YR
                "smart money saving strategies", #HK
                "work life balance advice", #JJ
                "environment news affecting daily life", #KM
                "technology changes affecting everyone", #ZX
                "science discoveries people can use", #RH
                "India news people care about", #NP
                "best habits for healthy life", #VH
            ] #NV
            tav = fetch_tavily(tavily_key, gen_queries)
            print(f"Tavily general: {len(tav)}", file=sys.stderr)
            source_counts["tavily"] = len(tav)
            add("tavily", tav, 1)
        # 4. Currents API — trending general news (free, no hard India focus) #YS
        if currents_key: #TX
            currents_gen = fetch_currents(currents_key, category="general", limit=15)
            print(f"Currents general: {len(currents_gen)}", file=sys.stderr)
            source_counts["currents"] = len(currents_gen)
            add("currents", currents_gen, 1)

    # Cross-source velocity: fold the same story (publisher suffixes stripped)
    # across INDEPENDENT sources — a story in 3+ feeds is genuinely important,
    # a one-off title is usually noise.
    key_stats: Dict[str, dict] = {}
    for title, score, source, _age in scored:
        key = title_key(title)
        if key not in key_stats:
            key_stats[key] = {"title": title, "score": score, "sources": {source}}
        else:
            key_stats[key]["sources"].add(source)
            key_stats[key]["score"] = max(key_stats[key]["score"], score)

    unique_scored = []
    for stats in key_stats.values():
        bonus = velocity_bonus(len(stats["sources"]))
        unique_scored.append((stats["title"], stats["score"] + bonus))

    # Filter: skip junk (incl. deals/prices) + require relevance + avoid
    # near-copies of recently published topics.
    unique_scored = [(t, s) for t, s in unique_scored if not is_skip(t)]
    unique_scored = [(t, s) for t, s in unique_scored if not is_clickbait(t)]
    unique_scored = [(t, s) for t, s in unique_scored if is_relevant_to_people(t)]
    unique_scored = [(t, s) for t, s in unique_scored if not is_near_dup(t, used)]

    # Sort by score desc
    unique_scored.sort(key=lambda x: x[1], reverse=True)

    # Take top candidates
    top = unique_scored[:20]
    print(f"\nTop {len(top)} candidates:", file=sys.stderr)
    for i, (t, s) in enumerate(top[:7], 1):
        print(f"  {i}. [{s:.0f}] {t[:80]}", file=sys.stderr)

    if not top:
        topic = pick_evergreen(used)
        print(f"\nFallback (evergreen): {topic}", file=sys.stderr)
        print(PUBLISHER_SUFFIX.sub("", topic).strip())
        save_used_topic(topic)
        return

    # LLM judge: score every shortlist headline 0-100 with a cheap lite model
    # (gemini-2.5-flash-lite), then blend 60% editorial / 40% heuristics. Falls
    # back to pure heuristics on any failure or NONE — never blocks publishing.
    top5 = top[:5]
    llm_scores = llm_rank_topics([t for t, _ in top5])
    if llm_scores:
        blended = []
        for i, (t, s) in enumerate(top5):
            llm = llm_scores.get(i)
            if llm is None:
                llm = min(max(s, 0.0), 100.0)  # missing score -> trust heuristics
            blended.append((t, 0.6 * llm + 0.4 * min(max(s, 0.0), 100.0)))
        blended.sort(key=lambda x: x[1], reverse=True)
        print("\nLLM scores:", file=sys.stderr)
        for i, (t, s) in enumerate(top5):
            llm = llm_scores.get(i)
            if llm is not None:
                print(f"  {i + 1}. [heu {s:.0f} | llm {llm:.0f}] {t[:70]}", file=sys.stderr)
        if blended[0][1] >= 55:
            # Deterministic: the blended winner wins. (No variety lost —
            # used_topics.json + is_near_dup skip yesterday's pick and fresh
            # news arrives daily.)
            topic = blended[0][0]
            print(f"\nLLM-ranked selection: {topic}", file=sys.stderr)
        else:
            # Even the LLM's best is weak — evergreen beats the least-bad junk.
            topic = pick_evergreen(used)
            print(f"\nFallback (evergreen, LLM floor): {topic}", file=sys.stderr)
    elif top[0][1] >= MIN_ACCEPTABLE_SCORE:
        # Mostly-deterministic: weighted pick from the top 3 (heavily favours
        # the #1 candidate instead of the old flat top-5 lottery).
        pool = top[:3]
        weights = [max(s, 1.0) for _, s in pool]
        topic = random.choices(pool, weights=weights, k=1)[0][0]
        print(f"\nSelected (heuristic): {topic}", file=sys.stderr)
    else:
        # Nothing cleared the quality bar — evergreen beats the least-bad junk.
        topic = pick_evergreen(used)
        print(f"\nFallback (evergreen, below score floor): {topic}", file=sys.stderr)

    # Strip trailing "... - The Hindu" attribution before publishing so the
    # blog title and slug stay clean ("Mumbai landslip..." not "...- The Hindu").
    topic = PUBLISHER_SUFFIX.sub("", topic).strip()
    print(topic)
    save_used_topic(topic)


if __name__ == "__main__":
    main()
