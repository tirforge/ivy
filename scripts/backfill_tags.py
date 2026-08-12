#!/usr/bin/env python
"""Backfill heuristic tags for posts missing a tags: frontmatter line.

Idempotent: skips posts that already have tags. Derives tags from a keyword
lexicon matched against the post title AND slug (many legacy posts have a
broken 'Untitled Post' title, so the slug is the reliable signal). New posts
get better LLM-generated tags from the crew pipeline.
"""

import re
import sys
from pathlib import Path

POSTS_DIR = Path(__file__).resolve().parent.parent / "blog-source" / "_posts"

# lowercase substring -> tag
LEXICON = [
    ("artificial intelligence", "ai"), ("machine learning", "machine-learning"),
    ("ai agents", "ai-agents"), ("ai agent", "ai-agents"), (" llm", "llms"),
    ("gpt", "llms"), ("chatbot", "chatbots"), ("generative", "generative-ai"),
    ("robot", "robotics"), ("drone", "drones"),
    ("spacex", "spacex"), ("nasa", "space"), ("isro", "space"), ("rocket", "space"),
    ("iphone", "apple"), ("apple", "apple"), ("samsung", "samsung"),
    ("pixel", "google-pixel"), ("smartphone", "smartphones"), ("phone", "smartphones"),
    ("bitcoin", "crypto"), ("crypto", "crypto"), ("blockchain", "crypto"),
    ("supreme court", "supreme-court"), ("court", "courts"),
    ("karnataka", "karnataka"), ("bengaluru", "bengaluru"), ("delhi", "delhi"),
    ("india", "india"), ("election", "india-politics"), ("protest", "india-politics"),
    ("parliament", "india-politics"), ("politic", "politics"),
    ("police", "india"), ("wrestler", "sports"), ("sport", "sports"),
    ("olympic", "olympics"), ("cricket", "cricket"), ("ashes", "cricket"),
    ("football", "football"), ("oneplus", "smartphones"),
    ("detained", "india-politics"), ("gandhi", "india-politics"),
    ("science", "science"), ("research", "science"), ("study", "science"),
    ("health", "health"), ("doctor", "health"), ("hospital", "health"),
    ("vaccine", "health"), ("medical", "health"), ("cancer", "health"),
    ("gaming", "gaming"), ("game", "gaming"), ("playstation", "gaming"),
    ("evs", "evs"), ("electric vehicle", "evs"), ("electric-vehicle", "evs"),
    ("cyber", "cybersecurity"), ("hack", "cybersecurity"), ("data breach", "cybersecurity"),
    ("cloud", "cloud-computing"), ("chip", "semiconductors"), ("semiconductor", "semiconductors"),
    ("climate", "climate"), ("flood", "climate"), ("weather", "climate"),
    ("heatwave", "climate"), ("monsoon", "climate"), ("environment", "climate"),
    ("university", "education"), ("students", "education"), ("college", "education"),
    ("exam", "education"), ("neet", "education"), ("school", "education"),
    ("turbulence", "aviation"), ("airline", "aviation"), ("air india", "aviation"),
    ("flight", "aviation"), ("airport", "aviation"), ("airbus", "aviation"),
    ("russia", "war"), ("ukraine", "war"), ("attack", "war"), ("military", "war"),
    ("movie", "movies"), ("film", "movies"), ("netflix", "streaming"),
    ("railway", "railways"), ("metro", "railways"), ("train", "railways"),
    ("fastmail", "privacy"), ("privacy", "privacy"), ("email", "privacy"),
    ("soundbar", "audio"), ("audio", "audio"), ("headphone", "audio"),
    ("speaker system", "audio"),
    ("tv", "technology"), ("tech", "technology"), ("gadget", "technology"),
    ("water", "environment"), ("river", "environment"),
    ("space", "space"), ("satellite", "space"), ("moon", "space"),
    ("startup", "startups"), ("funding", "startups"), ("investment", "finance"),
    ("stock", "finance"), ("market", "finance"), ("economy", "economy"),
    ("job", "careers"), ("salary", "careers"), ("employment", "careers"),
]

STOPWORDS = {
    "the", "and", "for", "how", "what", "why", "with", "from", "that", "this",
    "are", "you", "your", "new", "into", "when", "after", "before", "over",
    "under", "gets", "get", "says", "said", "report", "news", "today", "launch",
    "where", "actually", "probably", "going", "inside", "sound", "introduction",
    "might", "hiding", "results", "normal", "perfect", "master", "tutor",
    "steal", "crashing", "flipkart", "beyond", "bottleneck", "urban", "mobility",
    "timesofindia", "indiatimes", "untitled", "post", "stop", "hindu", "live",
    "law", "bar", "bench", "explains", "shriram", "uses", "learn", "complex",
    "offer", "offers", "region", "coming", "next", "week", "raise", "prices",
    "tomorrow", "gets", "big", "price", "drop", "sale", "before", "suffered",
    "rare", "control", "event", "foot", "altitude", "following", "announces",
    "said", "says", "report", "according", "details", "inside", "over", "after",
}


def frontmatter_title(content: str) -> str | None:
    m = re.search(r"^title\s*:\s*\"?([^\"]+?)\"?\s*$", content, re.M)
    return m.group(1).strip() if m else None


def slug_words(post: Path) -> list:
    name = post.stem
    name = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", name)
    return [w for w in re.split(r"[^a-z0-9]+", name) if w]


def derive_tags(title: str, slug: list) -> list:
    haystack = (title or "").lower() + " " + " ".join(slug)
    tags = []
    for needle, tag in LEXICON:
        if needle in haystack and tag not in tags:
            tags.append(tag)
    if len(tags) < 3:
        for w in slug:
            if w not in STOPWORDS and len(w) > 4 and w not in tags and len(tags) < 5:
                tags.append(w)
    return tags[:6]


def backfill(post: Path) -> list | None:
    content = post.read_text(encoding="utf-8")
    if re.search(r"^tags\s*:", content, re.M):
        return None
    if not content.startswith("---"):
        return None

    title = frontmatter_title(content) or ""
    tags = derive_tags(title, slug_words(post))
    if not tags:
        return None

    end = content.find("---", 3)
    if end == -1:
        return None
    updated = content[:end] + f"tags: [{', '.join(tags)}]\n" + content[end:]
    post.write_text(updated, encoding="utf-8")
    return tags


def main():
    changed = 0
    for post in sorted(POSTS_DIR.glob("*.md")):
        tags = backfill(post)
        if tags:
            changed += 1
            print(f"+ {post.name}: {', '.join(tags)}")
    print(f"\nBackfilled {changed} posts")
    return 0


if __name__ == "__main__":
    sys.exit(main())
