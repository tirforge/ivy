"""Unit tests for the pure helpers in scripts/publish_post.py.

Importing the module requires `requests` (installed via uv sync) but no
network access — the pure helpers are exercised directly.
"""

import unittest

from conftest_helpers import add_scripts_path

add_scripts_path()

from publish_post import (  # noqa: E402
    build_frontmatter,
    has_latex,
    has_mermaid,
    parse_title_from_fm,
    post_url,
    slugify,
    strip_stray_blocks,
    yaml_escape,
)


class SlugifyTest(unittest.TestCase):
    def test_lowercases_and_dashes(self):
        self.assertEqual(slugify("The Future of AI Agents"), "the-future-of-ai-agents")

    def test_strips_punctuation(self):
        self.assertEqual(slugify("iPhone 17: Price Drop!"), "iphone-17-price-drop")

    def test_handles_underscores_and_spacing(self):
        self.assertEqual(slugify("  crypto   boom  "), "crypto-boom")

    def test_no_trailing_dash(self):
        self.assertEqual(slugify("AI -"), "ai")


class YamlEscapeTest(unittest.TestCase):
    def test_escapes_quotes(self):
        self.assertEqual(yaml_escape('say "hi"'), 'say \\"hi\\"')

    def test_escapes_backslashes(self):
        self.assertEqual(yaml_escape("a\\b"), "a\\\\b")


class FrontmatterTest(unittest.TestCase):
    def test_numeric_tag_is_quoted(self):
        fm = build_frontmatter("t", "topic", "desc", None, False, tags=["00000", "ai"])
        self.assertIn('tags: ["00000", ai]', fm)

    def test_plain_tags_pass_through(self):
        fm = build_frontmatter("t", "topic", "desc", None, False, tags=["ai", "tech"])
        self.assertIn("tags: [ai, tech]", fm)

    def test_special_char_tag_is_quoted(self):
        fm = build_frontmatter("t", "topic", "desc", None, False, tags=["C#", "ai"])
        self.assertIn('tags: ["C#", ai]', fm)

    def test_math_and_mermaid_flags(self):
        fm = build_frontmatter("t", "topic", "desc", None, True, math=True, tags=[])
        self.assertIn("mermaid: true", fm)
        self.assertIn("math: true", fm)


class HasLatexTest(unittest.TestCase):
    def test_dollar_math_with_command(self):
        self.assertTrue(has_latex("The formula $\\sum_{i=1}^n i$ is famous"))

    def test_currency_is_not_math(self):
        self.assertFalse(has_latex("The deal is worth $500 million"))

    def test_double_dollar(self):
        self.assertTrue(has_latex("$$\\int_0^1 x dx$$"))

    def test_latex_command_outside_dollars(self):
        self.assertTrue(has_latex("Using \\text-style formatting here"))


class HasMermaidTest(unittest.TestCase):
    def test_detects_fence(self):
        self.assertTrue(has_mermaid("```mermaid\ngraph TD\n```"))

    def test_absent(self):
        self.assertFalse(has_mermaid("no diagrams here"))


class ParseTitleTest(unittest.TestCase):
    def test_double_quoted_with_escapes(self):
        self.assertEqual(parse_title_from_fm('title: "He said \\"hi\\""'), 'He said "hi"')

    def test_single_quoted(self):
        self.assertEqual(parse_title_from_fm("title: 'It works'"), "It works")

    def test_bare(self):
        self.assertEqual(parse_title_from_fm("title: Just a title"), "Just a title")

    def test_no_title(self):
        self.assertEqual(parse_title_from_fm("tags: [a]"), "")


class PostUrlTest(unittest.TestCase):
    def test_strips_date_prefix(self):
        self.assertEqual(post_url("2026-08-12-my-post"), "/my-post/")

    def test_no_date_prefix(self):
        self.assertEqual(post_url("my-post"), "/my-post/")


class StripStrayBlocksTest(unittest.TestCase):
    def test_leading_thought_block_removed(self):
        content = "```thought\nI should write about X\n```\n# Real Title\n\nBody here"
        out = strip_stray_blocks(content)
        self.assertEqual(out, "# Real Title\n\nBody here")

    def test_leading_yaml_block_removed(self):
        content = "```yaml\ntitle: x\ntags: [a]\n```\n# Real Title\n\nBody here"
        out = strip_stray_blocks(content)
        self.assertEqual(out, "# Real Title\n\nBody here")

    def test_plain_content_untouched(self):
        content = "# Title\n\nBody\n```mermaid\ngraph TD\n```"
        self.assertEqual(strip_stray_blocks(content), content)


if __name__ == "__main__":
    unittest.main()
