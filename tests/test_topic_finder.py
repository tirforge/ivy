"""Unit tests for the pure helpers in scripts/find_trending_topic.py.

These tests import the module (which pulls requests/dotenv, both installed)
but never hit the network — only pure scoring/dedup functions are tested.
"""

import unittest

from conftest_helpers import add_scripts_path

add_scripts_path()

from find_trending_topic import (  # noqa: E402
    deduplicate,
    is_clickbait,
    is_listicle,
    is_near_dup,
    is_relevant_to_people,
    is_skip,
    time_decay,
    title_key,
)


class DeduplicateTest(unittest.TestCase):
    def test_case_and_punctuation_insensitive(self):
        titles = ["Apple Launches New Mac!", "apple launches new mac", "Different Story."]
        out = deduplicate(titles)
        self.assertEqual(len(out), 2)

    def test_keeps_first_occurrence(self):
        titles = ["First!", "first"]
        self.assertEqual(deduplicate(titles), ["First!"])


class SkipTest(unittest.TestCase):
    def test_skip_patterns(self):
        self.assertTrue(is_skip("Daily life tips"))
        self.assertTrue(is_skip("Breaking news: something"))

    def test_normal_topic_not_skipped(self):
        self.assertFalse(is_skip("India's new semiconductor policy explained"))


class RelevanceTest(unittest.TestCase):
    def test_relevant_tech(self):
        self.assertTrue(is_relevant_to_people("How to build a React app"))

    def test_irrelevant(self):
        self.assertFalse(is_relevant_to_people("the weather in tokyo is fine today"))


class ClickbaitTest(unittest.TestCase):
    def test_double_punctuation(self):
        self.assertTrue(is_clickbait("You won't believe this!!"))
        self.assertTrue(is_clickbait("Really?!"))

    def test_single_punctuation_fine(self):
        self.assertFalse(is_clickbait("A normal headline."))


class ListicleTest(unittest.TestCase):
    def test_top_n(self):
        self.assertTrue(is_listicle("Top 10 gadgets of 2026"))

    def test_n_ways(self):
        self.assertTrue(is_listicle("5 ways to save money"))

    def test_plain(self):
        self.assertFalse(is_listicle("How India is building its chip ecosystem"))


class TimeDecayTest(unittest.TestCase):
    def test_fresh_is_full_weight(self):
        self.assertEqual(time_decay(0.0), 1.0)
        self.assertAlmostEqual(time_decay(24.0), 0.5, places=3)

    def test_unknown_age_counts_fresh(self):
        self.assertEqual(time_decay(None), 1.0)

    def test_floor(self):
        self.assertEqual(time_decay(10_000.0), 0.2)


class TitleKeyTest(unittest.TestCase):
    def test_strips_publisher_suffix(self):
        self.assertEqual(title_key("India launches rocket - The Hindu"), "india launches rocket")

    def test_normalizes_punctuation(self):
        self.assertEqual(title_key("iPhone 17: Price Drop!"), "iphone 17 price drop")


class NearDupTest(unittest.TestCase):
    def test_exact_copy(self):
        self.assertTrue(is_near_dup("iPhone 17 price drop announced", {"iphone 17 price drop announced"}))

    def test_distinct_topic(self):
        self.assertFalse(is_near_dup("Cricket world cup schedule", {"iphone 17 price drop"}))

    def test_short_title_not_filtered(self):
        self.assertFalse(is_near_dup("short", {"short"}))


if __name__ == "__main__":
    unittest.main()
