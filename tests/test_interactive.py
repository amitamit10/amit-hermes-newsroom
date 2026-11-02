import json
import re
import unittest
from pathlib import Path
from urllib.parse import quote_plus

ROOT = Path(__file__).resolve().parents[1]


class InteractiveNewsroomTests(unittest.TestCase):
    def test_archive_has_accessible_semantic_status_filters(self):
        home = (ROOT / "index.html").read_text(encoding="utf-8")
        expected_tones = {
            "native-ai-on-gnome": "early",
            "whatsapp-plus-context": "open-source",
            "source-first-linkedin-workflow": "gated",
            "goat-bounded-web-research": "candidate",
        }
        self.assertIn('aria-label="Filter project stories by current status"', home)
        self.assertIn('data-status-filter="all"', home)
        for slug, tone in expected_tones.items():
            with self.subTest(story=slug):
                self.assertIn(f'data-status-tone="{tone}"', home)
                self.assertIn(f'class="story-status story-status--{tone}"', home)
                self.assertIn(f'data-status-filter="{tone}"', home)
    def test_article_pages_have_section_navigation_and_reading_progress(self):
        stories = json.loads((ROOT / "data/stories.json").read_text(encoding="utf-8"))["stories"]
        for story in stories:
            with self.subTest(story=story["slug"]):
                page = (ROOT / "stories" / story["slug"] / "index.html").read_text(encoding="utf-8")
                self.assertIn('aria-label="Article reading progress"', page)
                self.assertIn('class="article-toc"', page)
                for index, section in enumerate(story["sections"], start=1):
                    section_id = f"section-{index:02d}"
                    self.assertIn(f'href="#{section_id}"', page)
                    self.assertIn(f'id="{section_id}"', page)
                    self.assertIn(section["heading"], page)
    def test_article_pages_have_a_copy_link_control_with_live_feedback(self):
        stories = json.loads((ROOT / "data/stories.json").read_text(encoding="utf-8"))["stories"]
        for story in stories:
            with self.subTest(story=story["slug"]):
                page = (ROOT / "stories" / story["slug"] / "index.html").read_text(encoding="utf-8")
                self.assertIn('class="copy-link-button"', page)
                self.assertIn('data-copy-link', page)
                self.assertIn('aria-describedby="copy-link-status"', page)
                self.assertIn('id="copy-link-status" aria-live="polite"', page)
        script = (ROOT / "static/site.js").read_text(encoding="utf-8")
        self.assertIn("copy-link-fallback", script)
        self.assertIn("press Ctrl+C to copy", script)

    def test_article_visuals_have_keyboard_ready_expand_dialog(self):
        stories = json.loads((ROOT / "data/stories.json").read_text(encoding="utf-8"))["stories"]
        for story in stories:
            with self.subTest(story=story["slug"]):
                page = (ROOT / "stories" / story["slug"] / "index.html").read_text(encoding="utf-8")
                self.assertIn('id="visual-dialog"', page)
                self.assertIn('aria-labelledby="visual-dialog-title"', page)
                self.assertIn('class="visual-expand"', page)
                self.assertIn('aria-haspopup="dialog"', page)
                self.assertIn('aria-label="Close expanded visual"', page)
        script = (ROOT / "static/site.js").read_text(encoding="utf-8")
        self.assertIn("visualDialogOpener", script)

    def test_article_topic_tags_prefilter_the_project_archive(self):
        stories = json.loads((ROOT / "data/stories.json").read_text(encoding="utf-8"))["stories"]
        for story in stories:
            with self.subTest(story=story["slug"]):
                page = (ROOT / "stories" / story["slug"] / "index.html").read_text(encoding="utf-8")
                for tag in story["tags"]:
                    self.assertIn(f'href="/?q={quote_plus(tag)}#stories"', page)
                    self.assertIn(f'>{tag}</a>', page)
    def test_status_palette_is_semantic_and_text_labels_remain(self):
        css = (ROOT / "static/site.css").read_text(encoding="utf-8")
        design = (ROOT / "DESIGN.md").read_text(encoding="utf-8")
        expected = {
            "open-source": "#176A53",
            "early": "#805000",
            "gated": "#184D82",
            "candidate": "#614894",
            "caution": "#9B3D35",
        }
        for tone, color in expected.items():
            with self.subTest(tone=tone):
                self.assertIn(f"--status-{tone}: {color}", css)
                self.assertIn(color, design)
        self.assertIn("Status colors communicate project state, always alongside a text label", design)
        self.assertIn('<span class="sr-only">Project status: </span>', (ROOT / "index.html").read_text(encoding="utf-8"))

    def test_source_references_have_programmatic_focus_targets(self):
        stories = json.loads((ROOT / "data/stories.json").read_text(encoding="utf-8"))["stories"]
        for story in stories:
            with self.subTest(story=story["slug"]):
                page = (ROOT / "stories" / story["slug"] / "index.html").read_text(encoding="utf-8")
                self.assertEqual(page.count('class="article-source" tabindex="-1"'), len(story["sources"]))
        script = (ROOT / "static/site.js").read_text(encoding="utf-8")
        self.assertIn("sourceReferenceLinks", script)

    def test_archive_has_an_accessible_clear_filters_control(self):
        page = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="reset-filters"', page)
        self.assertIn('aria-label="Clear all story filters"', page)
        self.assertIn('id="archive-results"', page)

    def test_whatsapp_charts_offer_readable_source_data_tables(self):
        page = (ROOT / "stories/whatsapp-plus-context/index.html").read_text(encoding="utf-8")
        self.assertEqual(page.count('class="visual-data"'), 2)
        for value in ("Weather", "18.110", "23.814", "34.498", "346 ms", "682 ms", "963 ms"):
            with self.subTest(value=value):
                self.assertIn(value, page)
        self.assertEqual(page.count("<table>"), 2)
        self.assertEqual(page.count("<caption>"), 2)

    def test_mobile_expanded_visual_is_larger_and_horizontally_scrollable(self):
        page = (ROOT / "stories/whatsapp-plus-context/index.html").read_text(encoding="utf-8")
        self.assertIn('class="visual-dialog-viewport"', page)
        self.assertIn('role="region" tabindex="0"', page)
        self.assertIn('aria-label="Expanded visual; scroll horizontally to inspect details"', page)
        css = (ROOT / "static/site.css").read_text(encoding="utf-8")
        self.assertIn(".visual-dialog-viewport {", css)
        self.assertIn("overflow-x: auto", css)
        self.assertIn("width: 720px", css)
        self.assertIn("max-width: none", css)
    def test_mobile_first_controls_are_touch_sized_and_readable(self):
        css = (ROOT / "static/site.css").read_text(encoding="utf-8")
        mobile_css = css.split("@media (max-width: 760px) {", 1)[1].split("@media (max-width: 390px)", 1)[0]
        expected = {
            ".filter-chip": {"min-height": "44px"},
            ".search-box input": {"min-height": "44px", "font-size": "16px"},
            ".filter-reset": {"min-height": "44px"},
            ".copy-link-button": {"min-height": "44px"},
            ".visual-expand": {"min-height": "44px"},
            ".article-toc summary": {"min-height": "44px"},
            ".tag": {"min-height": "40px", "font-size": "10px"},
            ".story-section p": {"font-size": "16px"},
            ".story-card-content > p:not(.story-status)": {"font-size": "14px"},
            ".article-source a": {"min-height": "44px"},
        }
        for selector, declarations in expected.items():
            with self.subTest(selector=selector):
                blocks = re.findall(rf"(?m)^\s*{re.escape(selector)}\s*\{{([^{{}}]*)\}}", mobile_css)
                self.assertTrue(blocks, f"No mobile rule for {selector}")
                rule = " ".join(blocks)
                for property_name, value in declarations.items():
                    self.assertRegex(rule, rf"(?:^|;)\s*{re.escape(property_name)}\s*:\s*{re.escape(value)}\s*(?:;|$)")

    def test_mobile_story_links_stay_legible_at_narrow_phone_width(self):
        css = (ROOT / "static/site.css").read_text(encoding="utf-8")
        narrow_css = css.split("@media (max-width: 390px) {", 1)[1].split("@media (prefers-reduced-motion:", 1)[0]
        self.assertIn(".story-card:not(.story-card--featured) .text-link { min-height: 44px; font-size: 10px; }", narrow_css)

    def test_archive_count_uses_story_language_for_mixed_content(self):
        js = (ROOT / "static/site.js").read_text(encoding="utf-8")
        self.assertTrue("Showing ${visible} of ${cards.length} stories" in js, "filtered archive count must describe news and project features as stories")
        self.assertTrue("Showing ${cards.length} stories" in js, "unfiltered archive count must describe news and project features as stories")

    def test_frontpage_removes_redundant_ticker_and_editorial_strip(self):
        css = (ROOT / "static/site.css").read_text(encoding="utf-8")
        home = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertNotIn("desk-wire", css)
        self.assertNotIn("manifesto-strip", css)
        self.assertNotIn("From the desk", home)
        self.assertNotIn("The news in AI.", home)

    def test_frontpage_lead_media_stays_wide_at_desktop_and_tablet(self):
        css = (ROOT / "static/site.css").read_text(encoding="utf-8")
        board_rule = css.split(".frontpage-board-grid {", 1)[1].split("}", 1)[0]
        lead_image_rule = css.split(".frontpage-lead-media img {", 1)[1].split("}", 1)[0]
        self.assertIn("align-items: start", board_rule)
        self.assertIn("height: auto", lead_image_rule)
        self.assertIn("aspect-ratio: 16 / 9", lead_image_rule)
        self.assertIn("@media (max-width: 960px) {", css)
        self.assertIn(".frontpage-board-grid { grid-template-columns: minmax(0, 1fr);", css)

    def test_mobile_home_prioritizes_lead_and_keeps_latest_feed_visible(self):
        css = (ROOT / "static/site.css").read_text(encoding="utf-8")
        touch_css = css.split("@media (max-width: 760px) {", 1)[1].split("@media (max-width: 390px)", 1)[0]
        mobile_css = css.rsplit("@media (max-width: 760px) {", 1)[1].split("\n}", 1)[0]
        self.assertIn(".frontpage-lead {", mobile_css)
        self.assertIn(".frontpage-lead-media img {", mobile_css)
        self.assertIn(".topic-rail-inner {", mobile_css)
        self.assertNotIn(".desk-wire-inner {", mobile_css)
        self.assertIn(".latest-feed-list {", mobile_css)
        self.assertNotIn(".latest-section .section-heading h2, .latest-section .section-heading .section-intro { display: none; }", css)
        self.assertIn(".archive-tools > .search-box { grid-row: 1; }", touch_css)
        self.assertIn(".archive-filter-groups { grid-row: 2; gap: 10px; }", touch_css)
        self.assertIn(".filter-chip { min-height: 44px;", touch_css)


if __name__ == "__main__":
    unittest.main()
