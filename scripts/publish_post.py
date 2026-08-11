#!/usr/bin/env python
"""Convert crew output to Jekyll post and deploy."""

import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path

import requests


POSTS_DIR = Path(__file__).resolve().parent.parent / "blog-source" / "_posts"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
BLOG_POST = OUTPUT_DIR / "blog_post.md"

UNSPLASH_ACCESS_KEY = os.environ.get("UNSPLASH_ACCESS_KEY", "")


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def parse_editor_frontmatter(content: str) -> dict:
    """Harvest the editor's leading ```yaml block (title/tags) before
    strip_stray_blocks() removes it. Minimal YAML parse — flow and block
    styles for `tags:`, plus `title:`. No pyyaml dependency."""
    m = re.search(r"^```yaml\s*\n(.*?)^```", content, re.M | re.S)
    if not m:
        return {}
    block = m.group(1)
    data = {}
    m_title = re.search(r"^title\s*:\s*(.+)$", block, re.M)
    if m_title:
        data["title"] = m_title.group(1).strip().strip("\"'")
    m_tags_flow = re.search(r"^tags\s*:\s*\[([^\]]*)\]", block, re.M)
    if m_tags_flow:
        data["tags"] = [t.strip().strip("\"'") for t in m_tags_flow.group(1).split(",") if t.strip()]
    else:
        m_tags_block = re.search(r"^tags\s*:\s*\n((?:\s*-\s*.+\n?)+)", block, re.M)
        if m_tags_block:
            data["tags"] = [
                re.sub(r"^\s*-\s*", "", line).strip()
                for line in m_tags_block.group(1).splitlines()
                if line.strip()
            ]
    return data


def extract_tags(content: str, topic: str) -> list:
    """Tags from the editor's frontmatter; fallback to meaningful topic words."""
    data = parse_editor_frontmatter(content)
    tags = data.get("tags", [])
    tags = [re.sub(r"[\"'\[\]]", "", t).strip().lower() for t in tags]
    tags = [t for t in tags if t]
    if not tags:
        stopwords = {
            "the", "of", "and", "for", "how", "what", "why", "with", "from",
            "that", "this", "are", "you", "your", "new", "into", "when",
        }
        tags = [
            w for w in re.split(r"[^a-z0-9]+", topic.lower())
            if len(w) > 3 and w not in stopwords
        ]
    seen, out = set(), []
    for t in tags:
        if t not in seen and t not in {"untitled", "post"}:
            seen.add(t)
            out.append(t)
    return out[:8]


def extract_title(content: str, topic: str = "") -> str:
    yaml_title = parse_editor_frontmatter(content).get("title")
    if yaml_title:
        return yaml_title
    for line in content.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    # Fallback: humanize the topic/slug so we never publish "Untitled Post"
    if topic:
        return topic.strip().title()
    return "Untitled Post"


def post_url(stem: str) -> str:
    """Chirpy permalink is /:title/ — slug is the filename minus the YYYY-MM-DD- prefix."""
    return "/" + re.sub(r"^\d{4}-\d{2}-\d{2}-", "", stem) + "/"


def parse_title_from_fm(fm: str) -> str:
    """Extract a post title from frontmatter, handling escaped quotes and
    single/double-quoted or bare YAML values."""
    m = re.search(r'^title\s*:\s*"((?:[^"\\]|\\.)*)"\s*$', fm, re.M)
    if m:
        return m.group(1).replace('\\"', '"').replace("\\\\", "\\")
    m = re.search(r"^title\s*:\s*'([^']*)'\s*$", fm, re.M)
    if m:
        return m.group(1)
    m = re.search(r"^title\s*:\s*(.+?)\s*$", fm, re.M)
    if m:
        return m.group(1).strip()
    return ""


def find_related_posts(tags: list, exclude: Path, limit: int = 3) -> list:
    """Tag-matched internal links: score every existing post by shared tags
    (ties broken by newest first). Returns list of (title, url) tuples."""
    related = []
    for post_path in sorted(POSTS_DIR.glob("*.md"), reverse=True):
        if post_path == exclude or not post_path.exists():
            continue
        text = post_path.read_text(encoding="utf-8")
        if not text.startswith("---"):
            continue
        fm, _, _ = text[3:].partition("---\n")
        title = parse_title_from_fm(fm) or post_path.stem.replace("-", " ").title()
        m_tags = re.search(r"^tags\s*:\s*\[([^\]]*)\]", fm, re.M)
        post_tags = [t.strip().strip("\"'") for t in m_tags.group(1).split(",")] if m_tags else []
        score = len(set(t.lower() for t in post_tags) & set(tags))
        if score > 0:
            related.append((score, title, post_url(post_path.stem)))
    related.sort(key=lambda x: (-x[0], x[1].lower()))
    # 1 shared tag is weak — fall through to newest posts instead
    out = [(t, u) for s, t, u in related if s >= 2][:limit]
    if len(out) < limit:
        for post_path in sorted(POSTS_DIR.glob("*.md"), reverse=True)[:limit + 1]:
            if post_path == exclude:
                continue
            text = post_path.read_text(encoding="utf-8")
            fm = text[3:].partition("---\n")[0] if text.startswith("---") else ""
            title = parse_title_from_fm(fm) or post_path.stem.replace("-", " ").title()
            url = post_url(post_path.stem)
            if (title, url) not in out:
                out.append((title, url))
            if len(out) >= limit:
                break
    return out[:limit]


def append_related_links(content: str, related: list) -> str:
    """Append a 'Related reading' block with descriptive anchor text."""
    if not related:
        return content
    lines = ["", "---", "", "## 📖 Related Reading", ""]
    for title, url in related:
        lines.append(f"- [{title}]({url})")
    return content.rstrip() + "\n" + "\n".join(lines) + "\n"


def extract_first_paragraph(content: str) -> str:
    for line in content.splitlines():
        stripped = line.strip()
        if (
            stripped
            and not stripped.startswith("#")
            and not stripped.startswith("```")
            and not stripped.startswith(">")
        ):
            return stripped[:150]
    return ""


def strip_stray_blocks(content: str) -> str:
    """Remove LLM reasoning leaks (```thought) and duplicate YAML frontmatter
    (```yaml) that leak into the article body.

    - ```yaml blocks at the top are stray duplicate frontmatter: remove the
      closed fence block surgically (preserves post-hero images below it).
    - ```thought blocks are reasoning leaks: the real article begins at the
      LAST '# ' H1 line (drops reasoning and any earlier duplicate copies).
    - Other top-level fences (e.g. ```mermaid) are legit — left untouched.
    """
    lines = content.splitlines()
    start = 0
    while start < len(lines) and not lines[start].strip():
        start += 1
    if start >= len(lines) or not lines[start].strip().startswith("```"):
        return content

    lang = lines[start].strip()[3:].strip()
    h1_idxs = [i for i, l in enumerate(lines) if l.startswith("# ")]

    if lang == "thought":
        if h1_idxs:
            return "\n".join(lines[h1_idxs[-1]:])
        # No H1 anywhere — drop the whole leading thought block
        j = start + 1
        while j < len(lines) and lines[j].strip() != "```":
            j += 1
        return "\n".join(lines[min(j + 1, len(lines)):])

    if lang == "yaml":
        j = start + 1
        while j < len(lines) and lines[j].strip() != "```":
            j += 1
        j += 1  # past closing fence
        while j < len(lines) and not lines[j].strip():
            j += 1
        return "\n".join(lines[j:])

    return content


def has_mermaid(content: str) -> bool:
    return "```mermaid" in content


def has_latex(content: str) -> bool:
    return bool(re.search(r"(?<!\w)\$[^$]+\$|\\\(|\\\[|\\\\text\{|\\\\rightarrow|\\\\sum|\\\\int|\\\\alpha|\\\\beta|\\\\gamma|\\\\delta|\\\\theta|\\\\lambda|\\\\mu|\\\\pi|\\\\sigma|\\\\omega|\\\\infty|\\\\partial|\\\\nabla", content))


def fetch_unsplash_images(topic: str, count: int = 2) -> list:
    if not UNSPLASH_ACCESS_KEY:
        return []
    try:
        url = "https://api.unsplash.com/search/photos"
        params = {"query": topic, "per_page": count, "orientation": "landscape"}
        headers = {"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"}
        r = requests.get(url, params=params, headers=headers, timeout=10)
        data = r.json()
        results = data.get("results", [])
        images = []
        for img in results[:count]:
            try:
                requests.get(img["links"]["download_location"], headers=headers, timeout=5)
            except Exception:
                pass
            images.append({
                "path": img["urls"]["raw"] + "&fm=webp",
                "alt": img.get("alt_description") or topic,
                "photographer": img["user"]["name"],
                "photographer_url": img["user"]["links"]["html"],
                "unsplash_url": img["links"]["html"],
                "download_location": img["links"]["download_location"],
            })
        return images
    except Exception as e:
        print(f"Unsplash fetch failed: {e}", file=sys.stderr)
        return []


def yaml_escape(s: str) -> str:
    """Escape double quotes in a YAML double-quoted string."""
    return s.replace("\\", "\\\\").replace('"', '\\"')

def build_frontmatter(title: str, topic: str, description: str, unsplash: dict | None, mermaid: bool, math: bool = False, tags: list | None = None) -> str:
    now = datetime.now().astimezone()
    date = now.strftime("%Y-%m-%d %H:%M:%S %z")
    lines = ["---", "layout: post", f'title: "{yaml_escape(title)}"', f"date: {date}", "toc: true"]
    if tags:
        # Quote numeric tags ("00000") — YAML 1.1 would parse them as octal
        # integers and break Liquid's slugify filter at build time.
        safe_tags = [f'"{t}"' if re.fullmatch(r"-?\d[\d_]*", t) else t for t in tags]
        lines.append(f"tags: [{', '.join(yaml_escape(t) for t in safe_tags)}]")
    if mermaid:
        lines.append("mermaid: true")
    if math:
        lines.append("math: true")
    if unsplash:
        lines.extend([
            "description: >-",
            f"  {description}",
            "image:",
            f'  path: "{unsplash["path"]}&w=1200&h=630&fit=crop"',
            f'  alt: "{yaml_escape(unsplash["alt"])}"',
            f'  photographer: "{yaml_escape(unsplash["photographer"])}"',
            f'  photographer_url: "{yaml_escape(unsplash["photographer_url"])}"',
            f'  unsplash_url: "{yaml_escape(unsplash["unsplash_url"])}"',
        ])
    else:
        lines.extend([
            "description: >-",
            f"  {description}",
        ])
    lines.append("---")
    return "\n".join(lines)


def insert_inline_image(content: str, img: dict | None) -> str:
    """Insert a post-hero image after the first \n##  heading's paragraph."""
    if not img:
        return content
    idx = content.find("\n## ")
    if idx == -1 and content.startswith("## "):
        idx = 0
    if idx != -1:
        # Find end of heading line
        eol = content.find("\n", idx + 1)
        if eol == -1:
            eol = idx
        # Find the next paragraph break after the heading
        para = content.find("\n\n", eol)
        if para != -1:
            insert_pos = para
        else:
            insert_pos = eol
    else:
        insert_pos = content.find("\n\n") if content.find("\n\n") != -1 else 0
    image_block = (
        f'\n\n<div class="post-hero">\n'
        f'  <img src="{img["path"]}&w=780&h=440&fit=crop"'
        f' alt="{img["alt"]}" loading="lazy" width="780" height="440"'
        f' data-unsplash-dl="{img["download_location"]}" />\n'
        f'  <div class="post-hero-credit">📸'
        f' <a href="{img["photographer_url"]}">{img["photographer"]}</a>'
        f' on <a href="{img["unsplash_url"]}">Unsplash</a></div>\n'
        f'</div>\n'
    )
    return content[:insert_pos] + image_block + content[insert_pos:]



def main():
    parser = argparse.ArgumentParser(description="Convert crew output to Jekyll post and deploy.")
    parser.add_argument("topic", nargs="?", default=None, help="Blog topic for Unsplash search")
    args = parser.parse_args()
    topic = args.topic if args.topic else os.environ.get("TOPIC", "The Future of AI Agents")

    if not BLOG_POST.exists():
        print(f"Error: {BLOG_POST} not found")
        sys.exit(1)

    content = BLOG_POST.read_text(encoding="utf-8")
    tags = extract_tags(content, topic)  # harvest BEFORE the yaml block is stripped
    content = strip_stray_blocks(content)
    title = extract_title(content, topic)
    desc = extract_first_paragraph(content)
    slug = slugify(topic)
    today = datetime.now().strftime("%Y-%m-%d")

    # Short query for Unsplash — first 3 meaningful words
    query = " ".join(topic.split()[:3])
    images = fetch_unsplash_images(query)
    cover = images[0] if len(images) > 0 else None
    inline_img = images[1] if len(images) > 1 and images[1]["path"] != images[0]["path"] else None

    mermaid = has_mermaid(content)
    math = has_latex(content)

    frontmatter = build_frontmatter(title, topic, desc, cover, mermaid, math, tags)
    body = re.sub(r"^# .+\n?", "", content, count=1).strip()
    # Insert inline image inside the first content section
    if inline_img:
        body = insert_inline_image(body, inline_img)
    post_content = frontmatter + "\n\n" + body

    post_filename = f"{today}-{slug}.md"
    post_path = POSTS_DIR / post_filename

    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    post_path.write_text(post_content, encoding="utf-8")

    # In-content internal links: tag-matched existing posts (SEO: topical authority)
    related = find_related_posts(tags, post_path)
    if related:
        post_content = frontmatter + "\n\n" + append_related_links(body, related)
        post_path.write_text(post_content, encoding="utf-8")

    print(f"Published: {post_path}")
    print(f"URL slug: {slug}")
    print(f"Tags: {', '.join(tags)}")
    if related:
        print("Related links:")
        for title, url in related:
            print(f"  - {title} → {url}")
    if cover:
        print(f"Cover: {cover['path']}")
    if inline_img:
        print(f"Inline: {inline_img['path']}")
    if mermaid:
        print("Mermaid: true")
    if math:
        print("Math: true")


if __name__ == "__main__":
    main()
