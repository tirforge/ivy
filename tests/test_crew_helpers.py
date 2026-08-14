"""Unit tests for the rate-limit cooldown helpers in crew.py.

Imports the module from the src/ package — requires crewai (installed via
uv sync) but performs no network calls.
"""

import os
import sys
import unittest
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Prevent the class-level LLM() constructors from trying to resolve env vars
# at import time — the helpers under test don't need them.
os.environ.setdefault("GEMINI_API_KEY", "test-key")

from blog_writing_crew.crew import _cooldown_seconds, _is_rate_limit  # noqa: E402


class CooldownSecondsTest(unittest.TestCase):
    def test_parses_retry_hint(self):
        err = Exception("429 Too Many Requests: retry in 42s")
        self.assertAlmostEqual(_cooldown_seconds(err), 47.0, places=1)

    def test_parses_retry_after(self):
        err = Exception("Retry-After: 30")
        self.assertAlmostEqual(_cooldown_seconds(err), 35.0, places=1)

    def test_default(self):
        err = Exception("rate limited")
        self.assertEqual(_cooldown_seconds(err), 45.0)

    def test_clamped(self):
        err = Exception("retry in 5000s")
        self.assertEqual(_cooldown_seconds(err), 300.0)
        # hint + 5s buffer (floor: 5.0)
        err_small = Exception("retry in 1s")
        self.assertEqual(_cooldown_seconds(err_small), 6.0)
        # hint + 5s buffer (floor: 5.0)
        err_floor = Exception("retry in 0s")
        self.assertEqual(_cooldown_seconds(err_floor), 5.0)


class IsRateLimitTest(unittest.TestCase):
    def test_429(self):
        self.assertTrue(_is_rate_limit(Exception("HTTP 429 Too Many Requests")))

    def test_rate_limit_phrase(self):
        self.assertTrue(_is_rate_limit(Exception("Rate limit exceeded")))

    def test_quota(self):
        self.assertTrue(_is_rate_limit(Exception("quota exhausted")))

    def test_unrelated_error(self):
        self.assertFalse(_is_rate_limit(Exception("connection refused")))
        self.assertFalse(_is_rate_limit(Exception("500 Internal Server Error")))


if __name__ == "__main__":
    unittest.main()
