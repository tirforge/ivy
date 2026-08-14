"""Unit tests for the pure helpers in scripts/repair_posts.py."""

import unittest

from conftest_helpers import add_scripts_path

add_scripts_path()

from repair_posts import (  # noqa: E402
    first_heading,
    first_paragraph,
    repair_body,
    split_frontmatter,
)


class SplitFrontmatterTest(unittest.TestCase):
    def test_splits_frontmatter(self):
        fm, body = split_frontmatter("---\ntitle: x\n---\n# Body")
        self.assertEqual(fm, "title: x")
        self.assertEqual(body, "# Body")

    def test_no_frontmatter(self):
        self.assertEqual(split_frontmatter("just body"), (None, None))


class RepairBodyTest(unittest.TestCase):
    def test_strips_thought_leak(self):
        body = "```thought\nI will write about X now\n```\n# Real Title\n\nContent"
        out = repair_body(body)
        self.assertNotIn("thought", out)
        self.assertIn("# Real Title", out)

    def test_strips_duplicate_yaml(self):
        body = "```yaml\ntitle: fake\ntags: [x]\n```\n# Real Title\n\nContent"
        out = repair_body(body)
        self.assertNotIn("```yaml", out)
        self.assertIn("# Real Title", out)

    def test_collapses_duplicate_h1(self):
        body = "# Title\n# Title\n\nContent"
        out = repair_body(body)
        self.assertEqual(out.count("# Title"), 1)

    def test_leaves_mermaid_alone(self):
        body = "# Title\n\n```mermaid\ngraph TD\n```"
        self.assertIn("```mermaid", repair_body(body))


class FirstParagraphTest(unittest.TestCase):
    def test_skips_headings_and_fences(self):
        body = "# Title\n\n> quote\n\n```\ncode\n```\n\nReal prose here."
        self.assertEqual(first_paragraph(body), "Real prose here.")

    def test_empty_body(self):
        self.assertEqual(first_paragraph("# only heading"), "")


class FirstHeadingTest(unittest.TestCase):
    def test_finds_h1_h2(self):
        self.assertEqual(first_heading("# Big Title"), "Big Title")
        self.assertEqual(first_heading("## Section"), "Section")

    def test_none(self):
        self.assertEqual(first_heading("no headings here"), "")


if __name__ == "__main__":
    unittest.main()
