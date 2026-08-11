#!/usr/bin/env python3
"""Submit URLs to IndexNow (Bing, Yandex, Seznam, Naver + AI search feeds).

IndexNow is a zero-config push protocol: the only setup is a public key file
at https://blog.aaruvi.space/{key}.txt (already committed at blog-source/),
which proves domain ownership. No accounts, no secrets.

Google does NOT participate in IndexNow — it uses its own sitemap crawler
(see scripts/gsc_submit.py for the optional Search Console nudge).

Usage:
    # submit a single new post URL
    uv run python scripts/indexnow_submit.py --url "https://blog.aaruvi.space/slug/"

    # submit several URLs
    uv run python scripts/indexnow_submit.py --url A --url B --url C

    # submit the newest N post URLs parsed from the built sitemap
    uv run python scripts/indexnow_submit.py --recent 5 --sitemap blog-source/_site/sitemap.xml

Env:
    INDEXNOW_KEY_FILE  path to key file (default: auto-detect blog-source/<key>.txt)
    BLOG_URL           site origin (default: https://blog.aaruvi.space)
"""

import argparse
import glob
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

DEFAULT_ORIGIN = "https://blog.aaruvi.space"
API = "https://api.indexnow.org/indexnow"


def find_key_file() -> str:
    env = os.environ.get("INDEXNOW_KEY_FILE", "").strip()
    if env:
        return env
    matches = glob.glob("blog-source/*.txt")
    # key file is the one whose basename is the key (32 hex chars)
    for m in matches:
        name = os.path.basename(m).removesuffix(".txt")
        if len(name) == 32 and all(c in "0123456789abcdef" for c in name):
            return m
    raise SystemExit(
        "[indexnow] key file not found. Generate one with: "
        "openssl rand -hex 16 > blog-source/$(openssl rand -hex 16).txt"
    )


def read_key() -> tuple[str, str]:
    path = find_key_file()
    with open(path) as f:
        key = f.read().strip()
    return key, path


def newest_post_urls(sitemap_path: str, limit: int) -> list[str]:
    """Parse sitemap and return the URLs with the newest <lastmod> first."""
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    tree = ET.parse(sitemap_path)
    entries = []
    for url in tree.findall(".//sm:url", ns):
        loc_el = url.find("sm:loc", ns)
        mod_el = url.find("sm:lastmod", ns)
        if loc_el is None or not loc_el.text:
            continue
        entries.append((mod_el.text if mod_el is not None and mod_el.text else "", loc_el.text.strip()))
    entries.sort(reverse=True)  # newest lastmod first
    return [loc for _, loc in entries[:limit]]


def submit(host: str, key: str, key_location: str, urls: list[str]) -> int:
    payload = {
        "host": host,
        "key": key,
        "keyLocation": key_location,
        "urlList": urls,
    }
    req = urllib.request.Request(
        API,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            print(f"[indexnow] OK HTTP {resp.status} — {len(urls)} URL(s): {', '.join(urls)}")
            return 0
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:300]
        print(f"[indexnow] HTTP {e.code}: {body}")
        if e.code in (403, 422):
            print("[indexnow] Fix: the key file must be publicly reachable at "
                  f"{key_location} (deploy first), and every URL must be under "
                  f"https://{host}/")
        return 0  # best-effort: never fail the workflow
    except urllib.error.URLError as e:
        print(f"[indexnow] Network error: {e.reason}")
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", action="append", default=[], help="URL to submit (repeatable)")
    parser.add_argument("--recent", type=int, default=0, help="Submit the N newest post URLs from --sitemap")
    parser.add_argument("--sitemap", default="blog-source/_site/sitemap.xml")
    args = parser.parse_args()

    origin = os.environ.get("BLOG_URL", DEFAULT_ORIGIN).rstrip("/")
    host = urllib.parse.urlparse(origin).netloc

    urls = list(args.url)
    if args.recent > 0:
        try:
            urls += newest_post_urls(args.sitemap, args.recent)
        except (FileNotFoundError, ET.ParseError) as e:
            print(f"[indexnow] could not read sitemap {args.sitemap}: {e}")

    if not urls:
        print("[indexnow] no URLs to submit (pass --url or --recent N)")
        return 0

    key, key_file = read_key()
    key_location = f"{origin}/{os.path.basename(key_file)}"
    return submit(host, key, key_location, urls)


if __name__ == "__main__":
    sys.exit(main())
