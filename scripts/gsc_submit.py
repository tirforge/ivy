#!/usr/bin/env python3
"""Submit the blog sitemap to Google Search Console via the Sitemaps API.

Google has no public "ping" endpoint anymore (deprecated June 2023) and does
not support IndexNow. The only sanctioned programmatic channel is the Search
Console Sitemaps API, authenticated with a Google Cloud service account.

One-time setup (the service account owner does this once):
  1. console.cloud.google.com → create/select a project → enable
     "Search Console API" (also listed as "Google Search Console API").
  2. APIs & Services → Credentials → Create credentials → Service account
     → download the JSON key file.
  3. Search Console (search.google.com/search-console) → your property
     → Settings → Users and permissions → add the service account email
     with "Full" permission.
  4. Add the JSON as a GitHub Actions secret named GSC_SERVICE_ACCOUNT_JSON
     (plain JSON string — no quoting tricks needed).

This script is best-effort: it prints a skip notice and exits 0 when the
secret is absent, so it can live in CI permanently without failing the run.

Usage:
    uv run python scripts/gsc_submit.py            # uses env vars
    uv run python scripts/gsc_submit.py --site-url https://blog.aaruvi.space/ \
        --sitemap-url https://blog.aaruvi.space/sitemap.xml

Env vars:
    GSC_SERVICE_ACCOUNT_JSON  the service account JSON (raw or base64)
    GSC_SITE_URL              Search Console property (default https://blog.aaruvi.space/)
    GSC_SITEMAP_URL           sitemap to submit (default https://blog.aaruvi.space/sitemap.xml)
"""

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

SCOPE = "https://www.googleapis.com/auth/webmasters"
API_BASE = "https://www.googleapis.com/webmasters/v3"


def load_credentials(raw: str) -> dict:
    """Accept raw JSON or base64-encoded JSON for the service account."""
    s = raw.strip()
    if s.startswith("{"):
        return json.loads(s)
    try:
        return json.loads(base64.b64decode(s).decode("utf-8"))
    except Exception:
        raise ValueError(
            "GSC_SERVICE_ACCOUNT_JSON is neither raw JSON nor base64-encoded JSON"
        )


def get_access_token(sa: dict) -> str:
    from google.auth.transport.requests import Request
    from google.oauth2 import service_account

    creds = service_account.Credentials.from_service_account_info(
        sa, scopes=[SCOPE]
    )
    creds.refresh(Request())
    return creds.token


def submit_sitemap(sa: dict, site_url: str, sitemap_url: str) -> int:
    token = get_access_token(sa)
    site_enc = urllib.parse.quote(site_url, safe="")
    feed_enc = urllib.parse.quote(sitemap_url, safe="")
    url = f"{API_BASE}/sites/{site_enc}/sitemaps/{feed_enc}"

    req = urllib.request.Request(
        url, method="PUT", headers={"Authorization": f"Bearer {token}"}
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            print(f"[gsc] Submitted {sitemap_url} to {site_url} → HTTP {resp.status}")
            return 0
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:500]
        print(f"[gsc] HTTP {e.code}: {body}")
        if e.code == 403:
            print("[gsc] Fix: add the service account email to Search Console "
                  "→ Settings → Users and permissions (Full permission).")
        elif e.code == 404:
            print(f"[gsc] Fix: GSC_SITE_URL '{site_url}' is not in this account, "
                  "or the property doesn't exist. Domain properties use "
                  "sc-domain:blog.aaruvi.space; meta-tag verification creates "
                  "a URL-prefix property https://blog.aaruvi.space/")
        return 0  # best-effort: never fail the workflow
    except urllib.error.URLError as e:
        print(f"[gsc] Network error: {e.reason}")
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-url", default=os.environ.get(
        "GSC_SITE_URL", "https://blog.aaruvi.space/"))
    parser.add_argument("--sitemap-url", default=os.environ.get(
        "GSC_SITEMAP_URL", "https://blog.aaruvi.space/sitemap.xml"))
    args = parser.parse_args()

    raw = os.environ.get("GSC_SERVICE_ACCOUNT_JSON", "").strip()
    if not raw:
        print("[gsc] GSC_SERVICE_ACCOUNT_JSON not set — skipping Search Console submission")
        return 0
    try:
        sa = load_credentials(raw)
    except ValueError as e:
        print(f"[gsc] {e}")
        return 0
    try:
        return submit_sitemap(sa, args.site_url, args.sitemap_url)
    except ImportError as e:
        print(f"[gsc] google-auth not installed ({e}) — run 'uv sync' first")
        return 1


if __name__ == "__main__":
    sys.exit(main())
