import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://amit-hermes-newsroom.vercel.app"


class PageFacts(HTMLParser):
    def __init__(self):
        super().__init__()
        self.h1 = 0
        self.canonicals = []
        self.descriptions = []
        self.jsonld = []
        self.images = []
        self.links = []
        self.in_jsonld = False
        self.jsonld_text = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "h1":
            self.h1 += 1
        if tag == "link" and attrs.get("rel") == "canonical":
            self.canonicals.append(attrs.get("href", ""))
        if tag == "meta" and attrs.get("name") == "description":
            self.descriptions.append(attrs.get("content", ""))
        if tag == "script" and attrs.get("type") == "application/ld+json":
            self.in_jsonld = True
            self.jsonld_text = []
        if tag == "img":
            self.images.append(attrs)
        if tag == "a":
            self.links.append(attrs.get("href", ""))

    def handle_endtag(self, tag):
        if tag == "script" and self.in_jsonld:
            self.jsonld.append("".join(self.jsonld_text))
            self.in_jsonld = False

    def handle_data(self, data):
        if self.in_jsonld:
            self.jsonld_text.append(data)


class NewsroomTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stories = json.loads((ROOT / "data/stories.json").read_text(encoding="utf-8"))["stories"]

    def test_newspaper_home_has_real_lead_topic_rail_and_latest_feed(self):
        home = (ROOT / "index.html").read_text(encoding="utf-8")
        ordered = sorted(self.stories, key=lambda story: story.get("published_at") or story["published"], reverse=True)
        lead = ordered[0]
        self.assertIn('class="frontpage-lead"', home)
        self.assertIn(f'id="lead-story-title">{lead["title"]}</h1>', home)
        self.assertIn(f'href="/stories/{lead["slug"]}/"', home)
        lead_image = lead.get("frontpage_asset", lead["cover_asset"])
        self.assertIn(f'src="{lead_image}"', home)
        self.assertNotIn('class="desk-wire"', home)
        self.assertNotIn('class="manifesto-strip"', home)
        if lead.get("frontpage_asset"):
            self.assertIn("Conceptual illustration of three glass policy gates", home)
            self.assertIn("Concept art · not a product screenshot", home)
        self.assertIn('aria-label="Browse story topics"', home)
        self.assertIn('id="latest-feed"', home)
        self.assertIn('aria-label="Latest stories"', home)
        for story in ordered[1:]:
            with self.subTest(story=story["slug"]):
                self.assertIn(f'href="/stories/{story["slug"]}/"', home)
                self.assertIn(story["title"], home)
        if lead.get("kind") == "news":
            self.assertIn("AI-generated · not human-edited", home)

    def test_home_and_story_pages_exist_with_unique_canonicals(self):
        paths = [
            ROOT / "index.html", ROOT / "about/index.html",
            ROOT / "editorial-policy/index.html", ROOT / "advertise/index.html",
            ROOT / "privacy/index.html",
        ]
        paths += [ROOT / "stories" / story["slug"] / "index.html" for story in self.stories]
        canonicals = []
        for path in paths:
            self.assertTrue(path.is_file(), f"missing generated page: {path}")
            parser = PageFacts()
            parser.feed(path.read_text(encoding="utf-8"))
            self.assertEqual(parser.h1, 1, f"expected exactly one H1 in {path}")
            self.assertEqual(len(parser.canonicals), 1, f"expected one canonical in {path}")
            self.assertEqual(len(parser.descriptions), 1, f"expected one meta description in {path}")
            self.assertTrue(parser.descriptions[0].strip())
            self.assertEqual(len(parser.jsonld), 1, f"expected one JSON-LD block in {path}")
            json.loads(parser.jsonld[0])
            canonicals.extend(parser.canonicals)
        self.assertEqual(len(canonicals), len(set(canonicals)))
        self.assertEqual(canonicals[0], BASE + "/")

    def test_article_copy_is_substantive_and_has_public_source_links(self):
        for story in self.stories:
            page = ROOT / "stories" / story["slug"] / "index.html"
            text = page.read_text(encoding="utf-8")
            words = re.findall(r"[\w’'-]+", text, flags=re.UNICODE)
            self.assertGreaterEqual(len(words), 450, f"thin generated story page: {story['slug']}")
            self.assertIn("Amit Elgabsi", text)
            self.assertIn("Hermes Agent", text)
            if story.get("kind", "project") == "news":
                self.assertIn("NewsArticle", text)
                self.assertIn("AI-generated report", text)
                for source in story["sources"]:
                    self.assertIn(source["url"], text)
            else:
                self.assertIn("https://github.com/amitamit10/", text)
            self.assertIn(story["cover_asset"], text)
            self.assertIn(f"/assets/og-{story['slug']}.jpg", text)
            self.assertIn("Sources</h2>", text)

    def test_inline_citations_resolve_to_the_article_source_list(self):
        for story in self.stories:
            page = (ROOT / "stories" / story["slug"] / "index.html").read_text(encoding="utf-8")
            cited_ids = set(re.findall(r'href="#source-(\d+)"', page))
            listed_ids = {str(source["id"]) for source in story["sources"]}
            self.assertEqual(cited_ids, listed_ids, story["slug"])
            for source in story["sources"]:
                self.assertIn(f'id="source-{source["id"]}"', page)
                self.assertIn(source["url"], page)

    def test_source_visuals_are_local_captioned_and_accessible(self):
        for story in self.stories:
            cover_path = ROOT / story["cover_asset"].lstrip("/")
            self.assertTrue(cover_path.is_file(), story["slug"])
            self.assertTrue(story["alt"].strip())
            self.assertTrue(story["cover_caption"].strip())
            self.assertNotIn("GPT-generated editorial artwork", story["cover_caption"])
            page = (ROOT / "stories" / story["slug"] / "index.html").read_text(encoding="utf-8")
            self.assertIn(f'src="{story["cover_asset"]}"', page)
            for section in story["sections"]:
                figure = section.get("figure")
                if figure:
                    self.assertTrue((ROOT / figure["src"].lstrip("/")).is_file())
                    self.assertTrue(figure["alt"].strip())
                    self.assertIn(f'src="{figure["src"]}"', page)

    def test_whatsapp_charts_preserve_sample_and_measurement_caveats(self):
        lookup = (ROOT / "assets/story-visual-whatsapp-lookups.svg").read_text(encoding="utf-8")
        self.assertIn("18.110 s", lookup)
        self.assertIn("23.814 s", lookup)
        self.assertIn("34.498 s", lookup)
        self.assertIn("n = 3 lookups", lookup)
        self.assertIn("not a measured sequential run", lookup)
        delay = (ROOT / "assets/story-visual-whatsapp-latency.svg").read_text(encoding="utf-8")
        self.assertIn("avg 346 ms · n=2", delay)
        self.assertIn("avg 963 ms · n=1", delay)
        self.assertIn("not a benchmark", delay)

    def test_crawl_files_and_assets_exist(self):
        sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
        robots = (ROOT / "robots.txt").read_text(encoding="utf-8")
        feed = (ROOT / "feed.xml").read_text(encoding="utf-8")
        self.assertEqual(sitemap.count("<url>"), len(self.stories) + 5)
        self.assertIn(BASE + "/news-sitemap.xml", robots)
        news_sitemap = ElementTree.fromstring((ROOT / "news-sitemap.xml").read_text(encoding="utf-8"))
        expected_news = sum(story.get("kind") == "news" for story in self.stories)
        self.assertEqual(len(news_sitemap), expected_news)
        self.assertEqual(feed.count("<item>"), len(self.stories))
        required = ["site.css", "site.js", "hero-newsroom.webp", "favicon.svg", "og-home.jpg"]
        for name in required:
            self.assertTrue((ROOT / "assets" / name).is_file(), f"missing asset {name}")
        for story in self.stories:
            cover = ROOT / "assets" / f"cover-{story['slug']}.webp"
            self.assertTrue(cover.is_file())
            self.assertLess(cover.stat().st_size, 200_000, f"cover is not optimized: {cover.name}")
            preview = ROOT / "assets" / f"og-{story['slug']}.jpg"
            self.assertTrue(preview.is_file())
            self.assertLess(preview.stat().st_size, 200_000, f"share card is not optimized: {preview.name}")
            self.assertTrue((ROOT / story["cover_asset"].lstrip("/")).is_file())
            for section in story["sections"]:
                if section.get("figure"):
                    self.assertTrue((ROOT / section["figure"]["src"].lstrip("/")).is_file())
            if story.get("frontpage_asset"):
                frontpage_art = ROOT / story["frontpage_asset"].lstrip("/")
                self.assertTrue(frontpage_art.is_file(), f"missing front-page artwork: {frontpage_art}")
                self.assertLess(frontpage_art.stat().st_size, 250_000, "front-page art should be optimized")
        self.assertLess((ROOT / "assets" / "hero-newsroom.webp").stat().st_size, 200_000)
        self.assertIn("/media-source/", (ROOT / ".vercelignore").read_text(encoding="utf-8"))
        self.assertFalse((ROOT / "assets" / "hero-orbit.svg").exists())
        self.assertEqual(list((ROOT / "assets").glob("cover-*.svg")), [])
        self.assertEqual(list((ROOT / "assets").glob("og-*.png")), [])

    def test_article_images_have_alt_text_and_related_links(self):
        for story in self.stories:
            parser = PageFacts()
            parser.feed((ROOT / "stories" / story["slug"] / "index.html").read_text(encoding="utf-8"))
            self.assertTrue(any(image.get("alt", "").strip() for image in parser.images))
            self.assertIn("/#stories", parser.links)

    def test_home_hero_alt_describes_release_pipeline_artwork(self):
        parser = PageFacts()
        parser.feed((ROOT / "index.html").read_text(encoding="utf-8"))
        hero = next(image for image in parser.images if image.get("src") == "/assets/hero-newsroom.webp")
        self.assertIn("software-build stages", hero.get("alt", "").lower())
        self.assertNotIn("crumpled paper", hero.get("alt", "").lower())
        self.assertEqual(hero.get("width"), "1200")
        self.assertEqual(hero.get("height"), "675")

    def test_about_page_credits_gpt_image_model_and_concept_art(self):
        about = (ROOT / "about/index.html").read_text(encoding="utf-8")
        self.assertIn("GPT Image 2 Medium", about)
        self.assertIn("never presented as a product screenshot", about)

    def test_google_fonts_use_preconnected_links_not_css_import(self):
        home = (ROOT / "index.html").read_text(encoding="utf-8")
        css = (ROOT / "assets/site.css").read_text(encoding="utf-8")
        self.assertIn('<link rel="preconnect" href="https://fonts.googleapis.com">', home)
        self.assertIn('<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>', home)
        self.assertNotIn("@import url('https://fonts.googleapis.com", css)

    def test_project_search_has_accessible_named_input(self):
        home = (ROOT / "index.html").read_text(encoding="utf-8")
        search = re.search(r'<input[^>]*id="story-search"[^>]*>', home)
        self.assertIsNotNone(search)
        self.assertIn('name="q"', search.group(0))
        self.assertIn('autocomplete="off"', search.group(0))
        self.assertIn('aria-live="polite"', home)

    def test_headings_use_balanced_wrapping(self):
        css = (ROOT / "assets/site.css").read_text(encoding="utf-8")
        self.assertIn("text-wrap: balance", css)

    def test_release_desk_keeps_status_sources_and_new_visual_system(self):
        home = (ROOT / "index.html").read_text(encoding="utf-8")
        css = (ROOT / "assets/site.css").read_text(encoding="utf-8")
        for story in self.stories:
            if story.get("kind", "project") == "project":
                self.assertIn(story["status"], home)
                self.assertIn(story["repositories"][0]["name"], home)
            else:
                self.assertIn("AI-generated", home)
                self.assertIn(story["title"], home)
        self.assertNotIn("The news in AI.", home)
        self.assertNotIn("Our newsroom promise", home)
        self.assertNotIn("From the desk", home)
        self.assertIn("Manrope", css)
        self.assertIn("IBM Plex Mono", css)
        self.assertNotIn("Cormorant Garamond", css)
        self.assertNotIn("#914631", css)
        ignore = (ROOT / ".vercelignore").read_text(encoding="utf-8")
        self.assertIn("/media-source-v3/", ignore)
        self.assertIn("/ops/", ignore)
        self.assertIn("/DESIGN.md", ignore)
        self.assertIn("/tokens.json", ignore)


if __name__ == "__main__":
    unittest.main()
