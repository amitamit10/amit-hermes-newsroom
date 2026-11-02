import copy
import json
import shutil
import tempfile
from datetime import datetime, timedelta, timezone
import unittest
from pathlib import Path
from xml.etree import ElementTree

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT / "ops"))
sys.path.insert(0, str(ROOT))
import build as newsroom
from generate_cover import generate_cover


def sample_news_story():
    published_at = datetime.now(newsroom.SITE_TIMEZONE).replace(microsecond=0)
    published_date = published_at.date().isoformat()
    body = (
        "The primary release note identifies an optional feature and states its documented limits. [[1]] "
        "Independent reporting documents the timing and context of the announcement. [[2]] "
    ) * 6
    return {
        "kind": "news",
        "slug": "sample-ai-release",
        "title": "A sample AI release, without the hype",
        "dek": "A test fixture verifies the newsroom's news-story rendering path.",
        "category": "AI systems",
        "published": published_date,
        "published_at": published_at.isoformat(),
        "human_reviewed": False,
        "repositories": [],
        "illustration": "news",
        "alt": "Abstract editorial illustration for a sample AI release.",
        "tags": ["AI", "Open-source tools"],
        "sources": [
            {"id": 1, "label": "Primary release note", "kind": "Primary source", "url": "https://project.example/releases/1"},
            {"id": 2, "label": "Independent coverage", "kind": "Independent reporting", "url": "https://news.example/articles/1"},
        ],
        "lede": "The project posted a feature update. [[1]] Independent reporting adds context. [[2]]",
        "cover_asset": "/assets/story-visual-native-ai.svg",
        "cover_caption": "Abstract illustration based on the linked reporting. [[1]] [[2]]",
        "source_checked": published_date,
        "sections": [
            {"heading": "What changed", "paragraphs": [body], "bullets": []},
            {"heading": "What the sources establish", "paragraphs": [body], "bullets": []},
            {"heading": "What remains unknown", "paragraphs": [body], "bullets": []},
        ],
        "takeaway": "This fixture is only used to test rendering and validation.",
        "source_note": "The test fixture uses example-domain URLs. [[1]]",
    }


class NewsroomAutomationTests(unittest.TestCase):
    def test_news_story_has_news_schema_ai_disclosure_and_labeled_ad_slot(self):
        story = sample_news_story()
        newsroom.validate([story])
        schema = newsroom.article_schema(story, "https://example.test/stories/sample-ai-release/", "/assets/og-sample-ai-release.jpg")
        article = schema["@graph"][0]
        self.assertEqual(article["@type"], "NewsArticle")
        self.assertEqual(article["datePublished"], story["published_at"])
        self.assertEqual(article["dateModified"], story["published_at"])
        page = newsroom.article_page(story, [story])
        self.assertIn("AI-generated report was not individually reviewed by Amit before publication", page)
        self.assertIn('aria-label="Advertising placement"', page)
        ad_html = newsroom.ad_slot("article-mid")
        self.assertIn("Advertisement", ad_html)
        self.assertIn("Ad placeholder · no live network is connected.", ad_html)
        self.assertNotIn("Preview placeholder", ad_html)
        self.assertIn('property="article:published_time"', page)
        self.assertIn("NewsArticle", page)

    def test_news_sitemap_includes_only_recent_news_with_timezone(self):
        story = sample_news_story()
        now = datetime.fromisoformat(story["published_at"]) + timedelta(hours=2)
        recent_xml = newsroom.news_sitemap_xml([story], now=now)
        root = ElementTree.fromstring(recent_xml)
        namespaces = {"news": "http://www.google.com/schemas/sitemap-news/0.9"}
        self.assertEqual(root.find(".//news:title", namespaces).text, story["title"])
        self.assertEqual(root.find(".//news:publication_date", namespaces).text, story["published_at"])
        old_story = copy.deepcopy(story)
        old_story["published_at"] = (datetime.fromisoformat(story["published_at"]) - timedelta(days=4)).isoformat()
        old_xml = newsroom.news_sitemap_xml([old_story], now=now)
        self.assertEqual(len(ElementTree.fromstring(old_xml)), 0)

    def test_news_validation_rejects_missing_independent_source_and_timezone(self):
        story = sample_news_story()
        missing_independent = copy.deepcopy(story)
        missing_independent["sources"] = [story["sources"][0]]
        with self.assertRaisesRegex(ValueError, "distinct primary and independent sources"):
            newsroom.validate([missing_independent])
        naive_time = copy.deepcopy(story)
        naive_time["published_at"] = "2026-11-02T10:00:00"
        with self.assertRaisesRegex(ValueError, "timezone"):
            newsroom.validate([naive_time])

    def test_news_cover_generator_emits_safe_svg_and_optimized_dimensions(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            svg, png = generate_cover(
                "ai-model-release", "A model & a release", "AI news",
                root / "assets", root / "media-source-v3",
            )
            ElementTree.parse(svg)
            self.assertIn("A model &amp; a release", svg.read_text(encoding="utf-8"))
            self.assertIn("not a product screenshot", svg.read_text(encoding="utf-8").lower())
            with Image.open(png) as image:
                self.assertEqual(image.size, (1200, 675))
                self.assertEqual(image.format, "PNG")

    def test_news_story_builds_full_static_newspaper_in_isolation(self):
        story = sample_news_story()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for directory in ("data", "assets", "media-source-v3"):
                (root / directory).mkdir(parents=True, exist_ok=True)
            shutil.copytree(ROOT / "static", root / "static", dirs_exist_ok=True)
            shutil.copy2(ROOT / "media-source-v3/hero-newsroom.png", root / "media-source-v3/hero-newsroom.png")
            cover_svg, _ = generate_cover(
                story["slug"], story["title"], story["category"],
                root / "assets", root / "media-source-v3",
            )
            story["cover_asset"] = f"/assets/{cover_svg.name}"
            (root / "data/stories.json").write_text(
                json.dumps({"stories": [story]}, ensure_ascii=False), encoding="utf-8"
            )
            old_state = {
                name: getattr(newsroom, name)
                for name in ("ROOT", "DATA_PATH", "STATIC_PATH", "ASSETS_PATH", "MEDIA_SOURCE", "SITE_URL")
            }
            try:
                newsroom.ROOT = root
                newsroom.DATA_PATH = root / "data/stories.json"
                newsroom.STATIC_PATH = root / "static"
                newsroom.ASSETS_PATH = root / "assets"
                newsroom.MEDIA_SOURCE = root / "media-source-v3"
                newsroom.SITE_URL = "https://newsroom.example"
                result = newsroom.build()
            finally:
                for name, value in old_state.items():
                    setattr(newsroom, name, value)

            self.assertEqual(result["pages"], 6)
            self.assertEqual(result["story_count"], 1)
            home = (root / "index.html").read_text(encoding="utf-8")
            article = (root / "stories" / story["slug"] / "index.html").read_text(encoding="utf-8")
            self.assertIn("Latest stories", home)
            self.assertIn(story["title"], home)
            self.assertIn('"@type":"NewsArticle"', article)
            self.assertIn("AI-generated report was not individually reviewed", article)
            self.assertTrue((root / "assets" / f"cover-{story['slug']}.webp").is_file())
            ElementTree.parse(root / "feed.xml")
            news_xml = ElementTree.parse(root / "news-sitemap.xml").getroot()
            self.assertEqual(len(news_xml), 1)

    def test_cover_generator_rejects_path_traversal(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with self.assertRaises(ValueError):
                generate_cover("../escape", "Unsafe", "AI", root / "assets", root / "media")


if __name__ == "__main__":
    unittest.main()