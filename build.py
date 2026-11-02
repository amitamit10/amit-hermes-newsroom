#!/usr/bin/env python3
"""Build the static Amit + Hermes Newsroom from curated, source-linked story data."""
from __future__ import annotations

import html
import json
import os
import re
import shutil
from datetime import date, datetime, timedelta, timezone
from email.utils import format_datetime
from pathlib import Path
from urllib.parse import quote_plus, urlsplit
from zoneinfo import ZoneInfo
from xml.sax.saxutils import escape as xml_escape

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "stories.json"
STATIC_PATH = ROOT / "static"
ASSETS_PATH = ROOT / "assets"
MEDIA_SOURCE = ROOT / "media-source-v3"
INLINE_CITATION_RE = re.compile(r"\[\[(\d+)\]\]")
SITE_URL = os.environ.get("SITE_URL", "https://amit-hermes-newsroom.vercel.app").rstrip("/")
LINKEDIN_URL = "https://www.linkedin.com/in/amit-elgabsi-146516378/"
GITHUB_URL = "https://github.com/amitamit10"
HERMES_URL = "https://github.com/NousResearch/hermes-agent"
SITE_TIMEZONE_NAME = os.environ.get("SITE_TIMEZONE", "Asia/Jerusalem")
SITE_TIMEZONE = ZoneInfo(SITE_TIMEZONE_NAME)
BUILD_AT = datetime.now(SITE_TIMEZONE)
TODAY = BUILD_AT.date()
STATUS_FILTERS = (
    ("open-source", "Public / open source"),
    ("early", "Early / experimental"),
    ("gated", "Authorization needed"),
    ("candidate", "Local candidate"),
)


def esc(value: str) -> str:
    return html.escape(str(value), quote=True)


def safe_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def words(value: str) -> list[str]:
    return re.findall(r"[\w’'-]+", value, flags=re.UNICODE)


def reading_time(story: dict) -> int:
    text = " ".join(
        [story["title"], story["dek"], story.get("lede", ""), story["takeaway"]]
        + [p for section in story["sections"] for p in section.get("paragraphs", [])]
        + [b for section in story["sections"] for b in section.get("bullets", [])]
    )
    return max(1, (len(words(text)) + 219) // 220)


def formatted_date(value: str) -> str:
    return datetime.strptime(value, "%Y-%m-%d").strftime("%B %-d, %Y")


def html_head(title: str, description: str, canonical: str, image: str, jsonld: dict | list, og_type: str = "website", published: str | None = None) -> str:
    full_title = f"{title} | Amit + Hermes"
    image_url = f"{SITE_URL}{image}"
    article_meta = ""
    if og_type == "article" and published and "T" in published:
        article_meta = f'\n  <meta property="article:published_time" content="{esc(published)}">'
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#f6f8fb">
  <meta name="color-scheme" content="light">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=Manrope:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <title>{esc(full_title)}</title>
  <meta name="description" content="{esc(description)}">
  <meta name="author" content="Amit Elgabsi">
  <link rel="canonical" href="{esc(canonical)}">
  <link rel="icon" type="image/svg+xml" href="/assets/favicon.svg">
  <link rel="alternate" type="application/rss+xml" title="Amit + Hermes Newsroom" href="/feed.xml">
  <link rel="stylesheet" href="/assets/site.css">
  <meta property="og:type" content="{esc(og_type)}">
  <meta property="og:site_name" content="Amit + Hermes Newsroom">
  <meta property="og:title" content="{esc(full_title)}">
  <meta property="og:description" content="{esc(description)}">
  <meta property="og:url" content="{esc(canonical)}">
  <meta property="og:image" content="{esc(image_url)}">
  <meta property="og:image:type" content="image/jpeg">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="Concept artwork for {esc(title)}; not a product screenshot.">{article_meta}
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{esc(full_title)}">
  <meta name="twitter:description" content="{esc(description)}">
  <meta name="twitter:image" content="{esc(image_url)}">
  <script type="application/ld+json">{safe_json(jsonld)}</script>
</head>'''


def person_schema() -> dict:
    return {
        "@type": "Person",
        "@id": f"{SITE_URL}/#amit-elgabsi",
        "name": "Amit Elgabsi",
        "url": LINKEDIN_URL,
        "sameAs": [LINKEDIN_URL, GITHUB_URL],
        "description": "AI builder and open-source maker."
    }


def website_schema() -> dict:
    return {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebSite",
                "@id": f"{SITE_URL}/#website",
                "url": f"{SITE_URL}/",
                "name": "Amit + Hermes Newsroom",
                "description": "Independent, source-linked AI and developer reporting with clear attribution and project status.",
                "inLanguage": "en",
                "publisher": {"@id": f"{SITE_URL}/#amit-elgabsi"}
            },
            person_schema()
        ]
    }


def header(active: str = "stories") -> str:
    return f'''<a class="skip-link" href="#main">Skip to content</a>
<header class="site-header">
  <div class="header-inner">
    <a class="wordmark" href="/" aria-label="Amit plus Hermes Newsroom home">
      <span class="wordmark-name">Amit <b>+</b> Hermes</span>
      <span class="wordmark-sub">AI + developer newsroom</span>
    </a>
    <button class="menu-toggle" type="button" aria-controls="primary-nav" aria-expanded="false" aria-label="Open navigation"><span></span><span></span></button>
    <nav class="primary-nav" id="primary-nav" aria-label="Main navigation" aria-hidden="false">
      <a class="nav-link{' is-active' if active == 'stories' else ''}" href="/#latest-edition">Latest</a>
      <a class="nav-link" href="/#projects">Projects</a>
      <a class="nav-link{' is-active' if active == 'editorial' else ''}" href="/editorial-policy/">Standards</a>
      <a class="nav-link{' is-active' if active == 'advertise' else ''}" href="/advertise/">Advertise</a>
      <a class="nav-link" href="{GITHUB_URL}" target="_blank" rel="noopener noreferrer">GitHub <span aria-hidden="true">↗</span></a>
      <a class="nav-cta" href="{LINKEDIN_URL}" target="_blank" rel="noopener noreferrer">Contact Amit <span aria-hidden="true">↗</span></a>
    </nav>
  </div>
</header>'''


def footer() -> str:
    return f'''<footer class="site-footer">
  <div class="footer-top">
    <a class="wordmark footer-wordmark" href="/">
      <span class="wordmark-name">Amit <b>+</b> Hermes</span>
      <span class="wordmark-sub">AI + developer news, from source</span>
    </a>
    <p class="footer-copy">An independent AI and developer newsroom. Hermes Agent is an AI collaborator; this is not an official Nous Research publication.</p>
    <div class="footer-links">
      <a href="/feed.xml">RSS feed</a>
      <a href="/about/">About &amp; credits</a>
      <a href="/editorial-policy/">Editorial standards</a>
      <a href="/advertise/">Advertising</a>
      <a href="/privacy/">Privacy &amp; ads</a>
      <a href="{GITHUB_URL}" target="_blank" rel="noopener noreferrer">GitHub</a>
      <a href="{LINKEDIN_URL}" target="_blank" rel="noopener noreferrer">LinkedIn</a>
    </div>
  </div>
  <div class="footer-bottom"><span>© {TODAY.year} Amit Elgabsi</span><span>Published by Amit · AI-assisted newsroom · Sources linked</span></div>
</footer>
<script src="/assets/site.js" defer></script>'''


def breadcrumb(items: list[tuple[str, str]]) -> str:
    links = [f'<a href="{esc(url)}">{esc(label)}</a>' for label, url in items[:-1]]
    links.append(f'<span aria-current="page">{esc(items[-1][0])}</span>')
    return '<nav class="breadcrumbs" aria-label="Breadcrumb">' + '<span class="crumb-sep" aria-hidden="true">/</span>'.join(links) + '</nav>'


def render_project_story_card(story: dict, featured: bool = False) -> str:
    slug = story["slug"]
    repo = story["repositories"][0]
    repo_count = len(story["repositories"])
    search_text = " ".join(
        [story["title"], story["dek"], story["category"], story["status"]]
        + story["tags"]
        + [item["name"] for item in story["repositories"]]
    ).lower()
    feature_class = " story-card--featured" if featured else ""
    extra_sources = f'<span class="source-extra">+{repo_count - 1} related source</span>' if repo_count > 1 else ""
    return f'''<article class="story-card{feature_class}" data-category="{esc(story['category'])}" data-status-tone="{esc(story['status_tone'])}" data-search="{esc(search_text)}">
  <a class="story-image-link" href="/stories/{esc(slug)}/" tabindex="-1" aria-hidden="true"><img class="story-image" src="/assets/cover-{esc(slug)}.webp" alt="" width="1200" height="675" loading="lazy" decoding="async"></a>
  <div class="story-card-content">
    <div class="story-meta"><span class="category-label">{esc(story['category'])}</span><time datetime="{esc(story['published'])}">{esc(formatted_date(story['published']))}</time></div>
    <p class="story-status story-status--{esc(story['status_tone'])}"><span class="status-indicator" aria-hidden="true"></span><span class="sr-only">Project status: </span>{esc(story['status'])}</p>
    <h3><a href="/stories/{esc(slug)}/">{esc(story['title'])}</a></h3>
    <p>{esc(story['dek'])}</p>
    <div class="story-card-bottom"><div class="card-source-wrap"><a class="project-source" href="{esc(repo['url'])}" target="_blank" rel="noopener noreferrer">{esc(repo['name'])} <span aria-hidden="true">↗</span></a>{extra_sources}</div><a class="text-link" href="/stories/{esc(slug)}/">Read the story <span aria-hidden="true">→</span></a></div>
  </div>
</article>'''


def story_published_value(story: dict) -> str:
    return story.get("published_at") or story["published"]


def display_story_date(story: dict) -> str:
    return formatted_date(story_published_value(story)[:10])


def ad_slot(placement: str) -> str:
    return f'''<aside class="ad-slot ad-slot--{esc(placement)}" aria-label="Advertising placement">
  <span class="ad-label">Advertisement</span>
  <p>Reserved for clearly labeled sponsorships.</p>
  <small>Ad placeholder · no live network is connected.</small>
</aside>'''


def render_news_story_card(story: dict, featured: bool = False) -> str:
    slug = story["slug"]
    search_text = " ".join([story["title"], story["dek"], story["category"]] + story["tags"]).lower()
    review_label = "AI-assisted · human reviewed" if story.get("human_reviewed") else "AI-generated · not human-edited"
    feature = " story-card--featured" if featured else ""
    published_value = story_published_value(story)
    time_label = ""
    if story.get("published_at"):
        local_time = datetime.fromisoformat(story["published_at"]).astimezone(SITE_TIMEZONE).strftime("%H:%M")
        time_label = f' <span class="story-time">{esc(local_time)} Jerusalem</span>'
    return f'''<article class="story-card story-card--news{feature}" data-category="{esc(story['category'])}" data-status-tone="news" data-search="{esc(search_text)}">
  <a class="story-image-link" href="/stories/{esc(slug)}/" tabindex="-1" aria-hidden="true"><img class="story-image" src="/assets/cover-{esc(slug)}.webp" alt="" width="1200" height="675" loading="lazy" decoding="async"></a>
  <div class="story-card-content">
    <div class="story-meta"><span class="category-label">{esc(story['category'])}</span><time datetime="{esc(published_value)}">{esc(display_story_date(story))}</time>{time_label}</div>
    <p class="news-disclosure">{esc(review_label)}</p>
    <h3><a href="/stories/{esc(slug)}/">{esc(story['title'])}</a></h3>
    <p>{esc(story['dek'])}</p>
    <div class="story-card-bottom"><span class="tag-line">{len(story['sources'])} linked sources</span><a class="text-link" href="/stories/{esc(slug)}/">Read the report <span aria-hidden="true">→</span></a></div>
  </div>
</article>'''


def render_frontpage_lead(story: dict) -> str:
    slug = story["slug"]
    published_value = story_published_value(story)
    is_news = story.get("kind") == "news"
    frontpage_image = story.get("frontpage_asset", story["cover_asset"])
    frontpage_alt = esc(story.get("frontpage_art_alt", ""))
    frontpage_caption = story.get("frontpage_art_caption")
    caption_html = f'<figcaption class="frontpage-art-caption">{esc(frontpage_caption)}</figcaption>' if frontpage_caption else ""
    if is_news:
        review_label = "AI-assisted · human reviewed" if story.get("human_reviewed") else "AI-generated · not human-edited"
        disclosure = f'<p class="news-disclosure">{esc(review_label)}</p>'
        source_note = f'<span class="frontpage-source-note">{len(story["sources"])} linked sources</span>'
        read_label = "Read the report"
    else:
        disclosure = f'<p class="story-status story-status--{esc(story["status_tone"])}"><span class="status-indicator" aria-hidden="true"></span><span class="sr-only">Project status: </span>{esc(story["status"])}</p>'
        repo = story["repositories"][0]
        source_note = f'<a class="frontpage-source-link" href="{esc(repo["url"])}" target="_blank" rel="noopener noreferrer">{esc(repo["name"])} <span aria-hidden="true">↗</span></a>'
        read_label = "Read the project story"
    return f'''<article class="frontpage-lead" aria-labelledby="lead-story-title">
  <figure class="frontpage-lead-media"><img src="{esc(frontpage_image)}" alt="{frontpage_alt}" width="1200" height="675" loading="eager" decoding="async" fetchpriority="high">{caption_html}</figure>
  <div class="frontpage-lead-copy">
    <div class="frontpage-meta"><span class="category-label">{esc(story["category"])}</span><time datetime="{esc(published_value)}">{esc(display_story_date(story))}</time></div>
    {disclosure}
    <h1 id="lead-story-title">{esc(story["title"])}</h1>
    <p class="frontpage-lead-dek">{esc(story["dek"])}</p>
    <div class="frontpage-lead-footer">{source_note}<a class="frontpage-read-link" href="/stories/{esc(slug)}/">{read_label} <span aria-hidden="true">→</span></a></div>
  </div>
</article>'''


def render_latest_item(story: dict) -> str:
    slug = story["slug"]
    published_value = story_published_value(story)
    is_news = story.get("kind") == "news"
    if is_news:
        review_label = "AI-assisted · human reviewed" if story.get("human_reviewed") else "AI-generated · not human-edited"
        status = f'<span class="latest-item-disclosure">{esc(review_label)}</span>'
    else:
        status = f'<span class="latest-item-status latest-item-status--{esc(story["status_tone"])}">{esc(story["status"])}</span>'
    return f'''<li class="latest-feed-item">
  <article class="latest-item">
    <div class="latest-item-meta"><span class="category-label">{esc(story["category"])}</span><time datetime="{esc(published_value)}">{esc(display_story_date(story))}</time></div>
    <h3><a href="/stories/{esc(slug)}/">{esc(story["title"])}</a></h3>
    <p class="latest-item-dek">{esc(story["dek"])}</p>
    {status}
  </article>
</li>'''


def homepage(stories: list[dict]) -> str:
    canonical = f"{SITE_URL}/"
    description = "Independent, source-linked reporting on AI, agents, open-source tools, and developer workflows, alongside explainers on Amit Elgabsi's public projects."
    home_title = "AI and developer news, with sources"
    hero_image = "/assets/og-home.jpg"
    available_tones = {story["status_tone"] for story in stories if story.get("kind", "project") == "project"}
    status_buttons = '<button class="filter-chip filter-chip--status is-selected" type="button" data-status-filter="all" aria-pressed="true">All statuses</button>' + "".join(
        f'<button class="filter-chip filter-chip--status filter-chip--{tone}" type="button" data-status-filter="{tone}" aria-pressed="false">{esc(label)}</button>'
        for tone, label in STATUS_FILTERS if tone in available_tones
    )
    ordered_stories = sorted(stories, key=story_published_value, reverse=True)
    lead_story = ordered_stories[0]
    cards = "\n".join(
        render_news_story_card(story)
        if story.get("kind") == "news" else render_project_story_card(story)
        for story in ordered_stories
    )
    latest_stories = ordered_stories[1:]
    latest_items = "\n".join(render_latest_item(story) for story in latest_stories)
    if latest_items:
        latest_body = f'<ol class="latest-feed-list" id="latest-feed">{latest_items}</ol>'
    else:
        latest_body = '<p class="latest-empty">You are reading the newest story in the newsroom.</p>'
    latest_section = f'''<section class="latest-section" id="latest-edition" aria-label="Latest stories">
    <div class="latest-feed-heading"><p class="eyebrow">{len(latest_stories):02d} more stories</p><h2>Latest stories</h2><a class="latest-archive-link" href="#stories">Browse the archive <span aria-hidden="true">→</span></a></div>
    {latest_body}
  </section>'''
    categories = sorted({story["category"] for story in stories})
    category_links = "".join(
        f'<a class="topic-link" href="/?category={quote_plus(category)}#stories">{esc(category)}</a>'
        for category in categories
    )
    category_rail = f'''<nav class="topic-rail" aria-label="Browse story topics">
    <div class="topic-rail-inner"><a class="topic-link topic-link--primary" href="#latest-edition">Latest</a><a class="topic-link" href="#stories">All stories</a>{category_links}</div>
    <span class="topic-rail-cue" aria-hidden="true">→</span>
  </nav>'''

    category_buttons = '<button class="filter-chip is-selected" type="button" data-filter="all" aria-pressed="true">All topics</button>' + "\n" + "\n".join(
        f'<button class="filter-chip" type="button" data-filter="{esc(category)}" aria-pressed="false">{esc(category)}</button>' for category in categories
    )
    return html_head(home_title, description, canonical, hero_image, website_schema()) + f'''
<body class="home-page">
{header('stories')}
<main id="main">
  {category_rail}
  <section class="frontpage-board" aria-label="Latest edition">
    <div class="frontpage-board-grid">
      {render_frontpage_lead(lead_story)}
      {latest_section}
    </div>
  </section>
  {ad_slot('home-after-latest')}

  <section class="archive-section section-wrap" id="projects">
    <span id="stories" class="anchor-target"></span>
    <div class="section-heading">
      <div><p class="eyebrow">The archive <span class="eyebrow-divider">/</span> {len(stories):02d} stories</p><h2>Reporting and projects,<br><em>with the source trail.</em></h2></div>
      <p class="section-intro">Independent news reports sit alongside project explainers. Search by topic; project status and AI bylines are labeled separately.</p>
    </div>
    <div class="archive-tools">
      <div class="archive-filter-groups">
        <div class="filter-group"><span class="filter-group-label">Topic</span><div class="filter-row" role="group" aria-label="Filter stories by topic">{category_buttons}</div></div>
        <div class="filter-group"><span class="filter-group-label">Project status</span><div class="filter-row filter-row--statuses" role="group" aria-label="Filter project stories by current status">{status_buttons}</div></div>
      </div>
      <label class="search-box"><span class="search-icon" aria-hidden="true"><svg viewBox="0 0 20 20"><circle cx="8.5" cy="8.5" r="5.5"></circle><path d="m12.5 12.5 4 4"></path></svg></span><span class="sr-only">Search stories</span><input id="story-search" type="search" name="q" placeholder="Search stories, projects, or topics" autocomplete="off"></label>
    </div>
    <div class="archive-results" id="archive-results"><p class="results-status" id="results-status" aria-live="polite">Showing {len(stories)} stories</p><button class="filter-reset" id="reset-filters" type="button" aria-label="Clear all story filters" hidden>Clear all filters <span aria-hidden="true">×</span></button></div>
    <div class="archive-grid" id="archive-grid">{cards}</div>
    <p class="empty-state" id="empty-state" hidden>No stories match that search. Try another topic.</p>
  </section>

  <section class="about-band section-wrap" id="about">
    <figure class="about-art"><img src="/assets/hero-newsroom.webp" alt="GPT-generated concept artwork of modular software-build stages connected by a cobalt signal; not a product screenshot." width="1200" height="675" loading="lazy" decoding="async"><figcaption>Concept artwork · not a product screenshot</figcaption></figure>
    <div class="about-band-copy"><p class="eyebrow">How the newsroom works</p><h2>Human accountability.<br><em>AI, clearly disclosed.</em></h2><p>Amit Elgabsi is the publisher. Hermes Agent can support research and drafting; no AI-generated news report is presented as a human-reported interview or as individually reviewed unless the article says so. Each story links to its evidence, and the newsroom skips weak or duplicate stories.</p><a class="text-link" href="/editorial-policy/">Read the editorial standards <span aria-hidden="true">→</span></a></div>
  </section>

  <section class="contact-panel section-wrap">
    <div><p class="eyebrow">Questions or a useful collaboration?</p><h2>Have a project<br><em>worth building?</em></h2></div>
    <div class="contact-panel-actions"><p>For collaboration, questions, or a thoughtful disagreement, reach Amit directly.</p><a class="button button-primary" href="{LINKEDIN_URL}" target="_blank" rel="noopener noreferrer">Contact Amit on LinkedIn <span aria-hidden="true">↗</span></a><a class="secondary-contact" href="{GITHUB_URL}" target="_blank" rel="noopener noreferrer">Explore the public projects on GitHub</a></div>
  </section>
</main>
{footer()}
</body>
</html>'''


def article_schema(story: dict, canonical: str, image: str) -> dict:
    return {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "NewsArticle" if story.get("kind") == "news" else "BlogPosting",
                "@id": f"{canonical}#article",
                "headline": story["title"],
                "description": story["dek"],
                "image": [f"{SITE_URL}{image}"],
                "datePublished": story_published_value(story),
                "dateModified": story.get("updated_at", story.get("updated", story_published_value(story))),
                "author": {"@type": "Organization", "name": "Amit + Hermes Newsroom", "url": SITE_URL}
                if story.get("kind") == "news" else {"@id": f"{SITE_URL}/#amit-elgabsi"},
                "publisher": {"@id": f"{SITE_URL}/#amit-elgabsi"},
                "mainEntityOfPage": {"@type": "WebPage", "@id": canonical},
                "articleSection": story["category"],
                "keywords": story["tags"],
                "inLanguage": "en"
            },
            person_schema()
        ]
    }


def render_inline_citations(text: str) -> str:
    output = []
    cursor = 0
    for match in INLINE_CITATION_RE.finditer(text):
        output.append(esc(text[cursor:match.start()]))
        source_id = int(match.group(1))
        output.append(
            f'<sup class="citation"><a href="#source-{source_id}" '
            f'aria-label="Source {source_id}">[{source_id}]</a></sup>'
        )
        cursor = match.end()
    output.append(esc(text[cursor:]))
    return "".join(output)


def render_article_sources(sources: list[dict]) -> str:
    entries = []
    for source in sources:
        source_id = int(source["id"])
        entries.append(
            f'<li id="source-{source_id}" class="article-source" tabindex="-1">'
            f'<span class="source-number">[{source_id}]</span>'
            f'<div><a href="{esc(source["url"])}" target="_blank" '
            f'rel="noopener noreferrer">{esc(source["label"])} '
            f'<span aria-hidden="true">↗</span></a>'
            f'<span class="source-kind">{esc(source["kind"])}</span></div></li>'
        )
    return (
        '<section class="article-sources" aria-labelledby="source-trail-title">'
        '<p class="eyebrow">Check the evidence</p>'
        '<h2 id="source-trail-title">Sources</h2>'
        f'<ol class="article-source-list">{"".join(entries)}</ol></section>'
    )


def render_visual_data_table(data: dict) -> str:
    headers = data.get("headers", [])
    rows = data.get("rows", [])
    if not headers or not rows or any(len(row) != len(headers) for row in rows):
        raise ValueError("Visual data tables require headers and rows of matching length")
    header_html = "".join(f'<th scope="col">{esc(header)}</th>' for header in headers)
    row_html = "".join(
        "<tr>" + "".join(f"<td>{esc(cell)}</td>" for cell in row) + "</tr>"
        for row in rows
    )
    return (
        f'<details class="visual-data"><summary>{esc(data.get("summary", "View data"))}</summary>'
        f'<div class="visual-data-scroll"><table><caption>{esc(data["caption"])}</caption>'
        f'<thead><tr>{header_html}</tr></thead><tbody>{row_html}</tbody></table></div></details>'
    )


def render_visual_figure(src: str, alt: str, caption_html: str, css_class: str, loading: str = "lazy", fetchpriority: str | None = None, data_table: dict | None = None) -> str:
    priority = f' fetchpriority="{esc(fetchpriority)}"' if fetchpriority else ""
    data_table_html = render_visual_data_table(data_table) if data_table else ""
    return (
        f'<figure class="{esc(css_class)}"><div class="visual-frame">'
        f'<img src="{esc(src)}" alt="{esc(alt)}" width="1200" height="675" '
        f'loading="{esc(loading)}" decoding="async"{priority}>'
        '<button class="visual-expand" type="button" aria-haspopup="dialog" aria-label="Expand this visual">'
        '<span aria-hidden="true">↗</span> Expand visual</button></div>'
        f'<figcaption>{caption_html}</figcaption>{data_table_html}</figure>'
    )


def render_visual_dialog() -> str:
    return '''<dialog class="visual-dialog" id="visual-dialog" aria-labelledby="visual-dialog-title">
  <div class="visual-dialog-head"><div><p class="eyebrow">Source-linked visual</p><h2 id="visual-dialog-title">Expanded visual</h2></div><button class="visual-dialog-close" type="button" aria-label="Close expanded visual">Close <span aria-hidden="true">×</span></button></div>
  <figure><div class="visual-dialog-viewport" role="region" tabindex="0" aria-label="Expanded visual; scroll horizontally to inspect details"><img class="visual-dialog-image" alt=""></div><p class="visual-dialog-pan-hint">Swipe horizontally to inspect the enlarged visual.</p><figcaption class="visual-dialog-caption"></figcaption></figure>
</dialog>'''


def render_sections(story: dict) -> str:
    output = []
    for index, section in enumerate(story["sections"], start=1):
        paragraphs = "\n".join(f"<p>{render_inline_citations(paragraph)}</p>" for paragraph in section.get("paragraphs", []))
        bullets = ""
        if section.get("bullets"):
            bullets = "<ul class=\"story-bullets\">" + "".join(f"<li>{render_inline_citations(item)}</li>" for item in section["bullets"]) + "</ul>"
        figure_html = ""
        if section.get("figure"):
            figure = section["figure"]
            figure_html = render_visual_figure(
                figure["src"], figure["alt"],
                render_inline_citations(figure["caption"]), "inline-figure",
                data_table=figure.get("data_table")
            )
        output.append(
            f'<section class="story-section" id="section-{index:02d}"><h2>{esc(section["heading"])}</h2>'
            f'{paragraphs}{bullets}{figure_html}</section>'
        )
        if index == 2:
            output.append(ad_slot("article-mid"))
    return "\n".join(output)


def render_article_toc(story: dict) -> str:
    links = "".join(
        f'<li><a href="#section-{index:02d}">{esc(section["heading"])}</a></li>'
        for index, section in enumerate(story["sections"], start=1)
    )
    return (
        '<details class="article-toc"><summary>On this page</summary>'
        f'<nav aria-label="On this page"><ol>{links}</ol></nav></details>'
    )


def related_stories(story: dict, stories: list[dict]) -> str:
    related = [item for item in stories if item["slug"] != story["slug"]][:2]
    if not related:
        return ""
    links = "".join(f'<a class="related-link" href="/stories/{esc(item["slug"])}/"><span>{esc(item["category"])}</span><b>{esc(item["title"])}</b><span aria-hidden="true">↗</span></a>' for item in related)
    return f'<section class="related-section"><p class="eyebrow">Keep reading</p><h2>More from the newsroom</h2><div class="related-grid">{links}</div></section>'


def article_page(story: dict, stories: list[dict]) -> str:
    canonical = f"{SITE_URL}/stories/{story['slug']}/"
    og_image = f"/assets/og-{story['slug']}.jpg"
    description = story["dek"]
    schema = article_schema(story, canonical, og_image)
    repos = "".join(f'<li><a href="{esc(repo["url"])}" target="_blank" rel="noopener noreferrer">{esc(repo["name"])} <span aria-hidden="true">↗</span></a><span>{esc(repo["kind"])}</span></li>' for repo in story["repositories"])
    is_news = story.get("kind") == "news"
    review_label = "Amit reviewed this AI-assisted report." if story.get("human_reviewed") else "This AI-generated report was not individually reviewed by Amit before publication."
    byline = (
        f'<div class="byline"><span class="byline-avatar" aria-hidden="true">N+</span><div><strong>Amit + Hermes Newsroom</strong><span>AI-assisted report · Publisher: Amit Elgabsi · {esc(review_label)}</span></div><a class="byline-link" href="/editorial-policy/">Standards <span aria-hidden="true">↗</span></a></div>'
        if is_news else
        f'<div class="byline"><span class="byline-avatar" aria-hidden="true">A+</span><div><strong>Amit Elgabsi</strong><span>Human author &amp; editor <b>·</b> Hermes Agent, AI collaborator</span></div><a class="byline-link" href="{LINKEDIN_URL}" target="_blank" rel="noopener noreferrer" aria-label="Amit Elgabsi on LinkedIn">Profile <span aria-hidden="true">↗</span></a></div>'
    )
    status_block = (
        f'<div class="rail-block"><span class="rail-label">Story type</span><p>AI-assisted news report</p></div>'
        if is_news else
        f'<div class="rail-block"><span class="rail-label">Project status</span><p class="project-status project-status--{esc(story["status_tone"])}">{esc(story["status"])}</p></div>'
    )
    repositories_block = f'        <div class="rail-block"><span class="rail-label">Project repositories</span><ul class="source-list">{repos}</ul></div>' if repos else ""
    credit = (
        f'<div class="article-credit"><span class="credit-rule"></span><p><strong>AI and authorship disclosure.</strong> Amit Elgabsi is the publisher. Hermes Agent researched and drafted this report. {esc(review_label)} Sources are linked; no interview or hands-on test is implied unless explicitly cited.</p></div>'
        if is_news else
        '<div class="article-credit"><span class="credit-rule"></span><p><strong>Credit & authorship.</strong> Amit Elgabsi is the human author and editor. Hermes Agent is credited as the AI collaborator. Project ownership and upstream sources are identified in the GitHub links above.</p></div>'
    )
    tags = "".join(
        f'<a class="tag" href="/?q={quote_plus(tag)}#stories">{esc(tag)}</a>'
        for tag in story["tags"]
    )
    story_text = render_sections(story)
    toc = render_article_toc(story)
    cover_image = story.get("cover_asset", f"/assets/cover-{story['slug']}.webp")
    lede = f'<p class="story-lede">{render_inline_citations(story["lede"])}</p>'
    cover_caption = render_inline_citations(story["cover_caption"])
    source_html = render_article_sources(story["sources"])
    visual_modal = render_visual_dialog()
    return html_head(story["title"], description, canonical, og_image, schema, og_type="article", published=story_published_value(story)) + f'''
<body class="article-page">
{header('stories')}
<progress class="reading-progress" id="reading-progress" value="0" max="100" aria-label="Article reading progress"></progress>
<main id="main" class="article-main">
  <div class="article-shell">
    {breadcrumb([("Home", "/"), ("Stories", "/#stories"), (story["title"], canonical)])}
    <header class="article-header">
      <div class="story-meta"><span class="category-label">{esc(story['category'])}</span><span>{esc(display_story_date(story))}</span><span>{reading_time(story)} min read</span></div>
      <h1>{esc(story['title'])}</h1>
      <p class="article-dek">{esc(story['dek'])}</p>
      {byline}
      <div class="article-tools"><button class="copy-link-button" type="button" data-copy-link aria-describedby="copy-link-status"><svg viewBox="0 0 20 20" aria-hidden="true" focusable="false"><path d="M7.5 12.5 12.5 7.5M6.2 14.1l-1 1a3 3 0 0 1-4.3-4.2l4-4.1a3 3 0 0 1 4.3 0m5.6-1.1 1-1a3 3 0 0 1 4.3 4.2l-4 4.1a3 3 0 0 1-4.3 0" transform="translate(1 0)" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg><span>Copy story link</span></button><span class="copy-link-status" id="copy-link-status" aria-live="polite" aria-atomic="true"></span></div>
    </header>
    {render_visual_figure(cover_image, story["alt"], cover_caption, "article-cover", loading="eager", fetchpriority="high", data_table=story.get("cover_data_table"))}
    <div class="article-layout">
      <aside class="article-rail" aria-label="Story details">
        {status_block}
        {toc}
        <div class="rail-block"><span class="rail-label">Sources checked</span><p>{esc(formatted_date(story['source_checked']))}</p></div>
        <div class="rail-block"><span class="rail-label">Topics</span><div class="tag-list">{tags}</div></div>
{repositories_block}
      </aside>
      <article class="story-body" aria-label="{esc(story['title'])}">
        {lede}{story_text}
        <aside class="pull-quote"><span class="quote-mark" aria-hidden="true">“</span><p>{render_inline_citations(story['takeaway'])}</p></aside>
        <p class="source-note">{render_inline_citations(story['source_note'])}</p>
        {source_html}
        {credit}
      </article>
    </div>
    {related_stories(story, stories)}
  </div>
</main>
{visual_modal}
{footer()}
</body>
</html>'''


def about_page() -> str:
    canonical = f"{SITE_URL}/about/"
    description = "Who builds the projects featured in Amit + Hermes Newsroom, how AI collaboration is credited, and how to contact Amit Elgabsi."
    schema = {"@context": "https://schema.org", "@type": "AboutPage", "url": canonical, "name": "About & credits | Amit + Hermes Newsroom", "mainEntity": person_schema(), "inLanguage": "en"}
    body = html_head("About & credits", description, canonical, "/assets/og-home.jpg", schema) + f'''
<body class="about-page">
{header('about')}
<main id="main" class="about-main section-wrap">
  {breadcrumb([("Home", "/"), ("About & credits", canonical)])}
  <p class="eyebrow">About this newsroom <span class="eyebrow-divider">/</span> The people behind the loop</p>
  <h1>A clear byline.<br><em>A visible build process.</em></h1>
  <div class="about-columns">
    <section class="about-copy"><h2>Who is Amit?</h2><p>Amit Elgabsi is an AI builder and open-source maker. This newsroom is a home for the projects he chooses to explain in depth: desktop assistants, agent plugins, research tools, and the workflows around them.</p><p>Each story links to the public repository it describes. The repository is the source of truth for installation instructions, current compatibility, licensing, and project status.</p></section>
    <section class="about-copy"><h2>What does “+ Hermes” mean?</h2><p>Hermes Agent is an AI agent built by <a href="https://nousresearch.com/" target="_blank" rel="noopener noreferrer">Nous Research</a>. Amit works with Hermes as an AI collaborator for research, implementation, testing, and documentation. Hermes is software, not a human co-author.</p><p>Amit is the publisher and retains responsibility for editorial standards and public release decisions. The existing project features were human-authored with AI assistance. If a future news report is generated by the scheduled desk, its byline will identify Hermes Agent’s role and explicitly state whether Amit reviewed it before publication.</p></section>
  </div>
  <section class="credit-policy"><p class="eyebrow">Credit policy</p><h2>Show the work.<br><em>Credit the work.</em></h2><ul><li>First-party repositories are labeled as Amit’s projects; upstream projects are linked and identified as upstream.</li><li>Public forks are not presented as original projects.</li><li>Candidate work is labeled as a candidate, not a release or a live installation.</li><li>GPT Image 2 Medium concept art is labeled wherever used and never presented as a product screenshot; article diagrams and charts are drawn from cited repository evidence.</li><li>This is an independent publication, not an official Nous Research newsroom or endorsement.</li></ul></section>
  <section class="contact-panel about-contact"><div><p class="eyebrow">Questions or collaboration?</p><h2>Contact <em>Amit.</em></h2></div><div class="contact-panel-actions"><p>Professional conversations are welcome. The links below go to Amit’s public profiles.</p><a class="button button-primary" href="{LINKEDIN_URL}" target="_blank" rel="noopener noreferrer">Connect on LinkedIn <span aria-hidden="true">↗</span></a><a class="secondary-contact" href="{GITHUB_URL}" target="_blank" rel="noopener noreferrer">Browse public GitHub projects</a></div></section>
</main>
{footer()}
</body>
</html>'''
    return body


def editorial_policy_page() -> str:
    canonical = f"{SITE_URL}/editorial-policy/"
    description = "How Amit + Hermes Newsroom researches, cites, discloses AI involvement, and corrects errors."
    schema = {"@context": "https://schema.org", "@type": "WebPage", "url": canonical, "name": "Editorial standards | Amit + Hermes Newsroom", "inLanguage": "en"}
    return html_head("Editorial standards", description, canonical, "/assets/og-home.jpg", schema) + f'''\n<body class="about-page">
{header('editorial')}
<main id="main" class="about-main section-wrap">
  {breadcrumb([("Home", "/"), ("Editorial standards", canonical)])}
  <p class="eyebrow">Editorial desk <span class="eyebrow-divider">/</span> What we cover and how</p>
  <h1>Evidence first.<br><em>Hype last.</em></h1>
  <div class="about-columns">
    <section class="about-copy"><h2>Coverage</h2><p>We cover AI, agents, open-source tools, and developer workflows, including verified updates to Amit Elgabsi’s public projects. A scheduled cycle is an opportunity to publish, not a quota: a weak or duplicate story is skipped.</p></section>
    <section class="about-copy"><h2>Evidence</h2><p>Search snippets are leads, not proof. We prefer primary sources, inspect the underlying material, and corroborate material claims independently. Company claims, measurements, and newsroom analysis are labeled distinctly. Each factual claim links to its supporting source.</p></section>
  </div>
  <section class="credit-policy"><p class="eyebrow">Authorship and AI</p><h2>Show who did what.</h2><ul><li>Amit Elgabsi is the publisher and owns the publication decisions.</li><li>Hermes Agent may discover sources, draft, and run checks. AI-generated news reports are labeled; they are not described as personally reported or human-reviewed unless an article says so.</li><li>We do not invent interviews, tests, quotes, statistics, or Amit’s opinions.</li><li>Project status, upstream work, and visual provenance are identified in the story.</li></ul></section>
  <section class="credit-policy"><p class="eyebrow">Corrections and sponsorships</p><h2>Accountability stays visible.</h2><ul><li>Material corrections should identify what changed; the original publication time is preserved.</li><li>Paid placements are labeled as advertising or sponsorship and do not buy editorial coverage or ranking.</li><li>There is no live ad network connected in this Preview.</li></ul><p>To report an error or discuss coverage, contact Amit through <a href="{LINKEDIN_URL}" target="_blank" rel="noopener noreferrer">LinkedIn</a>.</p></section>
</main>
{footer()}
</body>
</html>'''


def advertise_page() -> str:
    canonical = f"{SITE_URL}/advertise/"
    description = "Advertising and sponsorship rules for Amit + Hermes Newsroom. Current placements are labeled preview placeholders; no network is connected."
    schema = {"@context": "https://schema.org", "@type": "WebPage", "url": canonical, "name": "Advertising | Amit + Hermes Newsroom", "inLanguage": "en"}
    return html_head("Advertising & sponsorship", description, canonical, "/assets/og-home.jpg", schema) + f'''\n<body class="about-page">
{header('advertise')}
<main id="main" class="about-main section-wrap">
  {breadcrumb([("Home", "/"), ("Advertising", canonical)])}
  <p class="eyebrow">Commercial policy <span class="eyebrow-divider">/</span> Clear labels</p>
  <h1>Ads are separate.<br><em>Trust is not for sale.</em></h1>
  <div class="prelaunch-notice"><strong>Preview status:</strong> The visible placements are design placeholders only. No live ad network, publisher ID, ad script, or sponsor is connected.</div>
  <div class="about-columns">
    <section class="about-copy"><h2>What a sponsor can buy</h2><p>Only a clearly labeled advertising or sponsorship placement. Payment cannot buy coverage, a favorable article, source selection, a headline, or a ranking in the editorial archive.</p></section>
    <section class="about-copy"><h2>What must happen before launch</h2><p>We will verify the publisher account and eligibility, choose ad formats, publish a complete privacy notice, and implement an appropriate consent-management flow before any third-party ad or tracking code is loaded.</p></section>
  </div>
  <section class="credit-policy"><p class="eyebrow">Availability</p><h2>No rate card yet.</h2><p>We have not connected an ad provider or opened paid inventory. For future partnership inquiries, contact Amit via <a href="{LINKEDIN_URL}" target="_blank" rel="noopener noreferrer">LinkedIn</a>.</p></section>
</main>
{footer()}
</body>
</html>'''


def privacy_page() -> str:
    canonical = f"{SITE_URL}/privacy/"
    description = "Pre-launch privacy and advertising status for the Amit + Hermes Newsroom Preview."
    schema = {"@context": "https://schema.org", "@type": "WebPage", "url": canonical, "name": "Privacy and ads | Amit + Hermes Newsroom", "inLanguage": "en"}
    return html_head("Privacy & ads — pre-launch notice", description, canonical, "/assets/og-home.jpg", schema) + f'''\n<body class="about-page">
{header('advertise')}
<main id="main" class="about-main section-wrap">
  {breadcrumb([("Home", "/"), ("Privacy & ads", canonical)])}
  <p class="eyebrow">Pre-launch notice <span class="eyebrow-divider">/</span> Not a final legal policy</p>
  <h1>Privacy before<br><em>monetization.</em></h1>
  <div class="prelaunch-notice"><strong>Important:</strong> This is a pre-launch status notice, not a complete legal privacy policy. Do not enable live ads until the actual domain, hosting, analytics, consent, and ad-provider behavior have been reviewed and accurately documented.</div>
  <section class="credit-policy"><h2>Current Preview</h2><p>The project contains no live ad-network or analytics script. It loads Google Fonts and is hosted by Vercel; those services may receive ordinary connection metadata. The on-page advertising blocks are placeholders only. This page does not assert that no cookies or server logs exist.</p></section>
  <section class="credit-policy"><h2>Before live advertising</h2><p>We must choose the ad provider and target regions, verify the publisher account, document data flows and retention, implement consent where required, and update this notice before adding third-party ad or tracking code.</p></section>
</main>
{footer()}
</body>
</html>'''


def hero_art_svg() -> str:
    return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 620" role="img" aria-labelledby="title desc">
<title id="title">From idea to interface</title><desc id="desc">An illustrated build loop connecting an idea, research, code, and a useful tool.</desc>
<defs><radialGradient id="glow"><stop stop-color="#6758ff" stop-opacity=".62"/><stop offset="1" stop-color="#6758ff" stop-opacity="0"/></radialGradient><linearGradient id="paper" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#fbfaf6"/><stop offset="1" stop-color="#e9e7dc"/></linearGradient><linearGradient id="blue" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#7aa5ff"/><stop offset="1" stop-color="#365eff"/></linearGradient></defs>
<ellipse cx="365" cy="296" rx="330" ry="305" fill="url(#glow)"/><circle cx="360" cy="300" r="222" fill="none" stroke="#6876a8" stroke-opacity=".34" stroke-width="1.5" stroke-dasharray="4 10"/><circle cx="360" cy="300" r="152" fill="none" stroke="#a7b1d7" stroke-opacity=".27" stroke-width="1.5"/>
<path d="M150 300c0-116 94-210 210-210s210 94 210 210-94 210-210 210-210-94-210-210Z" fill="none" stroke="#97a6df" stroke-opacity=".38" stroke-width="1.2"/>
<g class="orbit-dot"><circle cx="198" cy="155" r="7" fill="#d7fd53"/><circle cx="198" cy="155" r="14" fill="none" stroke="#d7fd53" stroke-opacity=".45"/></g>
<g transform="translate(88 96) rotate(-8 112 78)"><rect width="220" height="138" rx="18" fill="url(#paper)"/><rect x="18" y="18" width="34" height="6" rx="3" fill="#2d5cff"/><text x="18" y="57" fill="#111726" font-family="Arial,sans-serif" font-size="19" font-weight="700">The question</text><text x="18" y="86" fill="#687083" font-family="Arial,sans-serif" font-size="12">Can an agent help here?</text><circle cx="184" cy="109" r="18" fill="#d7fd53"/><path d="M178 109h12m-6-6 6 6-6 6" stroke="#111726" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/></g>
<g transform="translate(388 74) rotate(6 110 70)"><rect width="214" height="140" rx="18" fill="#202a43" stroke="#7583b0" stroke-opacity=".55"/><circle cx="22" cy="22" r="4" fill="#ff726a"/><circle cx="36" cy="22" r="4" fill="#f2ce5b"/><circle cx="50" cy="22" r="4" fill="#54d8a5"/><rect x="19" y="47" width="88" height="7" rx="3.5" fill="#a6b4ea"/><rect x="19" y="67" width="156" height="6" rx="3" fill="#576581"/><rect x="19" y="83" width="134" height="6" rx="3" fill="#576581"/><rect x="19" y="106" width="72" height="17" rx="8.5" fill="#d7fd53"/><text x="109" y="119" fill="#e5e9f5" font-family="Arial,sans-serif" font-size="10">TEST · REFINE</text></g>
<g transform="translate(240 255)"><circle cx="116" cy="104" r="112" fill="#101523" stroke="#8796c5" stroke-opacity=".65" stroke-width="1.5"/><circle cx="116" cy="104" r="82" fill="#18213a"/><path d="M69 111 99 141l66-76" fill="none" stroke="url(#blue)" stroke-width="12" stroke-linecap="round" stroke-linejoin="round"/><text x="116" y="184" text-anchor="middle" fill="#f6f4ed" font-family="Arial,sans-serif" font-size="13" font-weight="700" letter-spacing="2">SHIP WHAT WORKS</text></g>
<g transform="translate(54 410) rotate(5 112 55)"><rect width="196" height="100" rx="16" fill="#d7fd53"/><text x="18" y="35" fill="#111726" font-family="Arial,sans-serif" font-size="11" font-weight="700" letter-spacing="2">SOURCE</text><path d="M18 53h134" stroke="#7d9640" stroke-width="2" stroke-dasharray="4 5"/><text x="18" y="76" fill="#26331b" font-family="Arial,sans-serif" font-size="13">Keep the receipts.</text></g>
<g transform="translate(485 407) rotate(-6 90 54)"><rect width="176" height="106" rx="16" fill="#423a73" stroke="#9f95e8" stroke-opacity=".7"/><text x="18" y="34" fill="#c7c3ff" font-family="Arial,sans-serif" font-size="11" font-weight="700" letter-spacing="2">HUMAN + AGENT</text><text x="18" y="62" fill="#fff" font-family="Arial,sans-serif" font-size="16" font-weight="700">Build. Review.</text><text x="18" y="83" fill="#d7d5ed" font-family="Arial,sans-serif" font-size="13">Explain the limits.</text></g>
<path d="M274 182c-23 17-37 37-43 59M460 204c-12 22-17 40-17 55M238 387c16 18 32 31 51 40M465 401c18-16 30-30 41-50" fill="none" stroke="#9aabe5" stroke-width="2" stroke-linecap="round" stroke-dasharray="3 8"/>
</svg>'''


def cover_svg(story: dict) -> str:
    slug = esc(story["slug"])
    title = esc(story["title"])
    label = esc(story["category"].upper())
    common_start = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 700" role="img" aria-labelledby="title desc"><title id="title">{title}</title><desc id="desc">Editorial illustration for {title}.</desc><defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#111827"/><stop offset="1" stop-color="#222c48"/></linearGradient><linearGradient id="glow" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#2d5cff" stop-opacity=".92"/><stop offset="1" stop-color="#9a7dff" stop-opacity=".65"/></linearGradient><filter id="shadow" x="-20%" y="-20%" width="140%" height="150%"><feDropShadow dx="0" dy="18" stdDeviation="22" flood-color="#050811" flood-opacity=".42"/></filter></defs><rect width="1200" height="700" fill="url(#bg)"/><circle cx="985" cy="130" r="260" fill="#4d62dc" opacity=".16"/><circle cx="135" cy="600" r="310" fill="#8d69ff" opacity=".13"/><path d="M70 560c190-100 300-90 470-5s318 110 590-20" fill="none" stroke="#7b89bc" stroke-opacity=".24" stroke-width="2"/><text x="70" y="82" fill="#d7fd53" font-family="Arial,sans-serif" font-size="18" font-weight="700" letter-spacing="5">{label}</text><text x="70" y="646" fill="#bbc3d9" font-family="Arial,sans-serif" font-size="15" letter-spacing="3">AMIT + HERMES  /  FIELD NOTES</text>'''
    if story["illustration"] == "desktop":
        art = '''<g filter="url(#shadow)" transform="translate(260 145)"><rect width="660" height="400" rx="28" fill="#f6f3ea"/><rect width="660" height="44" rx="28" fill="#e9e6dc"/><rect y="25" width="660" height="20" fill="#e9e6dc"/><circle cx="28" cy="22" r="6" fill="#ff766e"/><circle cx="50" cy="22" r="6" fill="#edc958"/><circle cx="72" cy="22" r="6" fill="#56c891"/><rect x="30" y="78" width="148" height="292" rx="18" fill="#e8ebf2"/><rect x="205" y="80" width="420" height="80" rx="16" fill="#fff"/><text x="230" y="112" fill="#69748d" font-family="Arial,sans-serif" font-size="12">ASK YOUR DESKTOP</text><text x="230" y="140" fill="#1b2337" font-family="Arial,sans-serif" font-size="20" font-weight="700">Find the note about the outage</text><rect x="205" y="182" width="190" height="150" rx="18" fill="#d7fd53"/><text x="227" y="216" fill="#202a20" font-family="Arial,sans-serif" font-size="13" font-weight="700">SEMANTIC SEARCH</text><circle cx="292" cy="274" r="27" fill="none" stroke="#24312a" stroke-width="5"/><path d="m311 293 25 25" stroke="#24312a" stroke-width="6" stroke-linecap="round"/><rect x="417" y="182" width="208" height="150" rx="18" fill="#dce4ff"/><path d="M445 294v-38m38 38v-68m38 68v-52m38 52v-95" stroke="#365eff" stroke-width="14" stroke-linecap="round"/><rect x="30" y="92" width="86" height="8" rx="4" fill="#aeb7c8"/><rect x="30" y="119" width="100" height="8" rx="4" fill="#aeb7c8"/><rect x="30" y="146" width="78" height="8" rx="4" fill="#aeb7c8"/><rect x="30" y="185" width="102" height="68" rx="12" fill="#fff"/><text x="46" y="225" fill="#687083" font-family="Arial,sans-serif" font-size="12">VOICE INPUT</text></g><path d="M201 210c50-50 82-65 119-68M966 472c55 20 92 12 131-14" fill="none" stroke="#d7fd53" stroke-width="3" stroke-dasharray="3 12" stroke-linecap="round"/><circle cx="192" cy="217" r="8" fill="#d7fd53"/><circle cx="1100" cy="447" r="8" fill="#d7fd53"/>'''
    elif story["illustration"] == "whatsapp":
        art = '''<g filter="url(#shadow)"><path d="M234 216c0-64 54-116 120-116h385c67 0 121 52 121 116v184c0 64-54 116-121 116H409l-115 56 30-108c-55-18-90-62-90-121Z" fill="#f4f1e8"/><circle cx="302" cy="258" r="17" fill="#d7fd53"/><rect x="342" y="241" width="190" height="34" rx="17" fill="#dce4ff"/><circle cx="302" cy="318" r="17" fill="#aa9bff"/><rect x="342" y="301" width="252" height="34" rx="17" fill="#dce4ff"/><circle cx="302" cy="378" r="17" fill="#d7fd53"/><rect x="342" y="361" width="168" height="34" rx="17" fill="#dce4ff"/><rect x="620" y="259" width="176" height="58" rx="18" fill="#d7fd53"/><text x="643" y="295" fill="#17201a" font-family="Arial,sans-serif" font-size="17" font-weight="700">Context: shared</text><rect x="574" y="341" width="222" height="58" rx="18" fill="#e8e1ff"/><text x="596" y="377" fill="#2b2645" font-family="Arial,sans-serif" font-size="16" font-weight="700">Trust: limited</text></g><g transform="translate(855 388)"><circle cx="95" cy="88" r="89" fill="#202a43" stroke="#a89bff" stroke-width="2"/><circle cx="95" cy="88" r="59" fill="none" stroke="#8997c0" stroke-width="2"/><path d="M64 90h62m-21-21 21 21-21 21" fill="none" stroke="#d7fd53" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/><rect x="30" y="177" width="130" height="38" rx="19" fill="#ff716e"/><rect x="87" y="189" width="17" height="14" rx="3" fill="#fff"/><path d="M91 189v-4a4 4 0 0 1 8 0v4" fill="none" stroke="#fff" stroke-width="2"/></g><path d="M285 516c70 74 140 100 220 105m367-17c63-37 99-82 120-141" fill="none" stroke="#8a9ac7" stroke-width="3" stroke-dasharray="4 14"/>'''
    elif story["illustration"] == "publishing":
        art = '''<g filter="url(#shadow)"><rect x="105" y="202" width="262" height="240" rx="24" fill="#f5f2e8"/><text x="137" y="244" fill="#5c69a8" font-family="Arial,sans-serif" font-size="15" font-weight="700" letter-spacing="2">01 / SOURCE</text><rect x="137" y="272" width="194" height="13" rx="6" fill="#c3c8d5"/><rect x="137" y="303" width="168" height="9" rx="4" fill="#d6d9e1"/><rect x="137" y="326" width="186" height="9" rx="4" fill="#d6d9e1"/><rect x="137" y="349" width="132" height="9" rx="4" fill="#d6d9e1"/><rect x="137" y="389" width="94" height="26" rx="13" fill="#d7fd53"/><rect x="469" y="168" width="262" height="306" rx="24" fill="#e5e3ff"/><text x="501" y="210" fill="#5f55a0" font-family="Arial,sans-serif" font-size="15" font-weight="700" letter-spacing="2">02 / DRAFT</text><rect x="501" y="238" width="198" height="12" rx="6" fill="#a39cd7"/><rect x="501" y="268" width="206" height="9" rx="4" fill="#b8b4dd"/><rect x="501" y="292" width="172" height="9" rx="4" fill="#b8b4dd"/><rect x="501" y="316" width="190" height="9" rx="4" fill="#b8b4dd"/><rect x="501" y="351" width="206" height="85" rx="14" fill="#252946"/><path d="M520 415l42-34 27 23 34-46 61 57" fill="none" stroke="#d7fd53" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/><rect x="836" y="211" width="250" height="220" rx="25" fill="#d7fd53"/><text x="871" y="255" fill="#313c21" font-family="Arial,sans-serif" font-size="15" font-weight="700" letter-spacing="2">03 / PUBLISH</text><circle cx="961" cy="331" r="47" fill="#202a43"/><path d="m940 332 15 16 30-34" fill="none" stroke="#fff" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/><text x="961" y="405" text-anchor="middle" fill="#26331b" font-family="Arial,sans-serif" font-size="16" font-weight="700">Human review stays in.</text></g><path d="M380 325h69m-16-16 16 16-16 16m294 0h70m-16-16 16 16-16 16" fill="none" stroke="#d7fd53" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/><circle cx="340" cy="128" r="9" fill="#a79bff"/><circle cx="787" cy="518" r="7" fill="#d7fd53"/>'''
    else:
        art = '''<g transform="translate(112 195)"><rect width="382" height="280" rx="27" fill="#f5f2e8"/><text x="34" y="54" fill="#6876a8" font-family="Arial,sans-serif" font-size="15" font-weight="700" letter-spacing="2">RESEARCH REQUEST</text><text x="34" y="103" fill="#1b2337" font-family="Arial,sans-serif" font-size="28" font-weight="700">Find evidence</text><text x="34" y="141" fill="#667082" font-family="Arial,sans-serif" font-size="18">not just pages</text><rect x="34" y="179" width="310" height="56" rx="18" fill="#e7e9f1"/><circle cx="68" cy="207" r="13" fill="none" stroke="#536286" stroke-width="4"/><path d="m78 217 10 10" stroke="#536286" stroke-width="4" stroke-linecap="round"/><rect x="110" y="199" width="180" height="15" rx="7" fill="#aab3c6"/></g><g transform="translate(624 126)"><circle cx="230" cy="230" r="170" fill="none" stroke="#7e8bb4" stroke-width="2" stroke-dasharray="4 12"/><circle cx="230" cy="230" r="108" fill="#202a43" stroke="#d7fd53" stroke-width="2"/><text x="230" y="217" text-anchor="middle" fill="#f6f4ed" font-family="Arial,sans-serif" font-size="17" font-weight="700">BOUNDED</text><text x="230" y="248" text-anchor="middle" fill="#d7fd53" font-family="Arial,sans-serif" font-size="18" font-weight="700">RETRIEVAL</text><g fill="#dce4ff" stroke="#121827" stroke-width="5"><circle cx="230" cy="38" r="22"/><circle cx="365" cy="92" r="22"/><circle cx="413" cy="230" r="22"/><circle cx="365" cy="367" r="22"/><circle cx="230" cy="420" r="22"/><circle cx="95" cy="367" r="22"/><circle cx="47" cy="230" r="22"/></g><g fill="#365eff"><circle cx="230" cy="38" r="7"/><circle cx="365" cy="92" r="7"/><circle cx="413" cy="230" r="7"/><circle cx="365" cy="367" r="7"/><circle cx="230" cy="420" r="7"/><circle cx="95" cy="367" r="7"/><circle cx="47" cy="230" r="7"/></g><path d="M318 112 350 93M361 254v75M317 348l-48 49M142 350l-30 17M99 208l22-83M171 83l39-26" stroke="#9ba9d4" stroke-width="3"/></g><rect x="122" y="508" width="353" height="60" rx="18" fill="#d7fd53"/><text x="154" y="546" fill="#182119" font-family="Arial,sans-serif" font-size="16" font-weight="700">Search · Extract · Crawl · Cite</text>'''
    return common_start + art + "</svg>"


def optimize_webp(source: Path, destination: Path, size: tuple[int, int]) -> int:
    from PIL import Image, ImageOps

    if not source.is_file():
        raise FileNotFoundError(f"Missing source cover artwork: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as original:
        image = ImageOps.fit(
            original.convert("RGB"), size, method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.5),
        )
        image.save(destination, "WEBP", quality=84, method=6)
    return destination.stat().st_size


def make_og_jpg(path: Path, title: str, label: str, source: Path) -> bool:
    from PIL import Image, ImageDraw, ImageFont, ImageOps

    if not source.is_file():
        raise FileNotFoundError(f"Missing source cover artwork: {source}")
    with Image.open(source) as original:
        image = ImageOps.fit(
            original.convert("RGB"), (1200, 630), method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.5),
        ).convert("RGBA")
    draw = ImageDraw.Draw(image, "RGBA")
    draw.rounded_rectangle((44, 38, 830, 592), radius=12, fill=(246, 248, 251, 241), outline=(255, 255, 255, 250), width=2)
    try:
        label_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 17)
        brand_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
        title_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        title_font = ImageFont.truetype(title_path, 46)
    except OSError:
        label_font = ImageFont.load_default()
        brand_font = ImageFont.load_default()
        title_path = None
        title_font = ImageFont.load_default()

    draw.ellipse((83, 82, 95, 94), fill=(36, 91, 255, 255))
    draw.text((111, 74), label.upper(), font=label_font, fill=(58, 73, 96, 255))

    def wrap(font) -> list[str]:
        lines: list[str] = []
        line = ""
        for word in title.split():
            candidate = (line + " " + word).strip()
            if draw.textbbox((0, 0), candidate, font=font)[2] > 680 and line:
                lines.append(line)
                line = word
            else:
                line = candidate
        if line:
            lines.append(line)
        return lines

    lines = wrap(title_font)
    if len(lines) > 3 and title_path:
        title_font = ImageFont.truetype(title_path, 39)
        lines = wrap(title_font)
    y = 155
    line_height = 60 if title_font.size >= 44 else 52
    for item in lines[:3]:
        draw.text((82, y), item, font=title_font, fill=(17, 21, 28, 255))
        y += line_height
    draw.line((82, 516, 202, 516), fill=(36, 91, 255, 255), width=3)
    draw.text((82, 536), "AMIT + HERMES  /  AI + DEVELOPER NEWSROOM", font=brand_font, fill=(73, 84, 101, 255))
    image.convert("RGB").save(path, "JPEG", quality=88, optimize=True, progressive=True)
    return True


def rss_xml(stories: list[dict]) -> str:
    items = []
    ordered = sorted(stories, key=story_published_value, reverse=True)
    for story in ordered:
        if story.get("published_at"):
            published = datetime.fromisoformat(story["published_at"]).astimezone(timezone.utc)
        else:
            published = datetime.strptime(story["published"], "%Y-%m-%d").replace(hour=7, tzinfo=timezone.utc)
        url = f"{SITE_URL}/stories/{story['slug']}/"
        description = xml_escape(story["dek"])
        items.append(f'''<item><title>{xml_escape(story['title'])}</title><link>{xml_escape(url)}</link><guid isPermaLink="true">{xml_escape(url)}</guid><pubDate>{format_datetime(published, usegmt=True)}</pubDate><description>{description}</description></item>''')
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>Amit + Hermes Newsroom</title><link>{xml_escape(SITE_URL)}/</link><description>Independent, source-linked reporting on AI, agents, open-source tools, and developer workflows.</description><language>en</language>{''.join(items)}</channel></rss>'''


def news_sitemap_xml(stories: list[dict], now: datetime | None = None) -> str:
    current = now or BUILD_AT
    if current.tzinfo is None:
        raise ValueError("News sitemap clock must be timezone-aware")
    cutoff = current.astimezone(timezone.utc) - timedelta(days=2)
    entries = []
    eligible = [story for story in stories if story.get("kind") == "news" and story.get("published_at")]
    eligible.sort(key=lambda story: story["published_at"], reverse=True)
    for story in eligible:
        published = datetime.fromisoformat(story["published_at"])
        if published.tzinfo is None:
            raise ValueError(f"News publication timestamp must include a timezone: {story['slug']}")
        if published.astimezone(timezone.utc) < cutoff:
            continue
        url = f"{SITE_URL}/stories/{story['slug']}/"
        entries.append(
            f'<url><loc>{xml_escape(url)}</loc><news:news>'
            '<news:publication><news:name>Amit + Hermes Newsroom</news:name>'
            '<news:language>en</news:language></news:publication>'
            f'<news:publication_date>{xml_escape(published.isoformat())}</news:publication_date>'
            f'<news:title>{xml_escape(story["title"])}</news:title>'
            '</news:news></url>'
        )
    body = "".join(entries)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
        'xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">'
        f'{body}</urlset>'
    )


def validate(stories: list[dict]) -> None:
    def validate_data_table(data: dict | None, context: str) -> None:
        if data is None:
            return
        headers = data.get("headers", [])
        rows = data.get("rows", [])
        if (
            not data.get("caption")
            or not headers
            or not rows
            or any(not isinstance(cell, str) for cell in headers)
            or any(len(row) != len(headers) or any(not isinstance(cell, str) for cell in row) for row in rows)
        ):
            raise ValueError(f"Invalid visual data table in {context}")

    if not stories:
        raise ValueError("No stories found")
    slugs = [story.get("slug", "") for story in stories]
    if len(slugs) != len(set(slugs)):
        raise ValueError("Story slugs must be unique")
    required = {"slug", "title", "dek", "category", "published", "illustration", "alt", "tags", "sources", "lede", "cover_asset", "cover_caption", "source_checked", "sections", "takeaway", "source_note"}
    allowed_status_tones = {tone for tone, _ in STATUS_FILTERS}
    for story in stories:
        kind = story.get("kind", "project")
        if kind not in {"project", "news"}:
            raise ValueError(f"Unknown story kind in {story.get('slug', '?')}: {kind}")
        kind_required = {"repositories", "status", "status_tone"} if kind == "project" else {"repositories", "published_at", "human_reviewed"}
        missing = (required | kind_required) - set(story)
        if missing:
            raise ValueError(f"{story.get('slug', '?')} missing fields: {sorted(missing)}")
        try:
            date.fromisoformat(story["published"])
            date.fromisoformat(story["source_checked"])
        except (TypeError, ValueError) as error:
            raise ValueError(f"Invalid publication/source-check date in {story.get('slug', '?')}") from error
        if kind == "project":
            if story["status_tone"] not in allowed_status_tones:
                raise ValueError(f"Unknown status tone in {story['slug']}: {story['status_tone']}")
        else:
            if not isinstance(story["human_reviewed"], bool):
                raise ValueError(f"News story needs an explicit human_reviewed boolean: {story['slug']}")
            try:
                published_at = datetime.fromisoformat(story["published_at"])
            except (TypeError, ValueError) as error:
                raise ValueError(f"Invalid publication timestamp in {story['slug']}") from error
            if published_at.tzinfo is None:
                raise ValueError(f"News publication timestamp must include a timezone: {story['slug']}")
            if published_at.astimezone(SITE_TIMEZONE).date().isoformat() != story["published"]:
                raise ValueError(f"News publication date does not match its local timestamp: {story['slug']}")
            if story.get("updated_at"):
                try:
                    updated_at = datetime.fromisoformat(story["updated_at"])
                except (TypeError, ValueError) as error:
                    raise ValueError(f"Invalid update timestamp in {story['slug']}") from error
                if updated_at.tzinfo is None or updated_at < published_at:
                    raise ValueError(f"Invalid or earlier update timestamp in {story['slug']}")
        validate_data_table(story.get("cover_data_table"), f"{story['slug']} cover")
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", story["slug"]):
            raise ValueError(f"Invalid slug: {story['slug']}")
        if kind == "project" and not story["repositories"]:
            raise ValueError(f"{story['slug']} must link a public source repository")
        for repository in story["repositories"]:
            if not repository["url"].startswith("https://github.com/"):
                raise ValueError(f"Source must link to public GitHub: {repository['url']}")
        if not story["sources"]:
            raise ValueError(f"{story['slug']} must list its sources")
        source_ids = [source.get("id") for source in story["sources"]]
        if any(not isinstance(source_id, int) or source_id < 1 for source_id in source_ids):
            raise ValueError(f"Invalid citation id in {story['slug']}")
        if len(source_ids) != len(set(source_ids)):
            raise ValueError(f"Duplicate citation id in {story['slug']}")
        for source in story["sources"]:
            if not source.get("label") or not source.get("kind") or not source.get("url", "").startswith("https://"):
                raise ValueError(f"Invalid source entry in {story['slug']}: {source}")
        if kind == "news":
            primary_hosts = {urlsplit(source["url"]).hostname for source in story["sources"] if "primary" in source["kind"].casefold()}
            independent_hosts = {urlsplit(source["url"]).hostname for source in story["sources"] if "independent" in source["kind"].casefold()}
            if not primary_hosts or not independent_hosts or primary_hosts & independent_hosts:
                raise ValueError(f"News story needs distinct primary and independent sources: {story['slug']}")
        asset_paths = [story["cover_asset"]]
        if story.get("frontpage_asset"):
            frontpage_asset = story["frontpage_asset"]
            frontpage_path = Path(frontpage_asset.lstrip("/"))
            if not frontpage_asset.startswith("/assets/") or ".." in frontpage_path.parts or frontpage_path.suffix.lower() != ".webp":
                raise ValueError(f"Front-page art must use a local optimized WebP: {frontpage_asset}")
            if not story.get("frontpage_art_alt", "").strip() or not story.get("frontpage_art_caption", "").strip():
                raise ValueError(f"Front-page art needs alt text and a caption in {story['slug']}")
            if not (MEDIA_SOURCE / f"{frontpage_path.stem}.png").is_file():
                raise FileNotFoundError(f"Missing front-page art source: {MEDIA_SOURCE / (frontpage_path.stem + '.png')}")
            asset_paths.append(frontpage_asset)
        for section in story["sections"]:
            if section.get("figure"):
                figure = section["figure"]
                validate_data_table(figure.get("data_table"), f"{story['slug']} section {section['heading']}")
                if not figure.get("alt", "").strip() or not figure.get("caption", "").strip():
                    raise ValueError(f"Figure needs alt text and a caption in {story['slug']}")
                asset_paths.append(figure.get("src", ""))
        for asset_path in asset_paths:
            relative_path = Path(asset_path.lstrip("/"))
            if not asset_path.startswith("/assets/") or ".." in relative_path.parts:
                raise ValueError(f"Story visual must use a local /assets/ path: {asset_path}")
            if not (ROOT / relative_path).is_file():
                raise FileNotFoundError(f"Missing story visual: {ROOT / relative_path}")
        citation_text = " ".join(
            [story["lede"], story["cover_caption"], story["source_note"], story["takeaway"]]
            + [text for section in story["sections"] for text in section.get("paragraphs", [])]
            + [text for section in story["sections"] for text in section.get("bullets", [])]
            + [section["figure"]["caption"] for section in story["sections"] if section.get("figure")]
        )
        cited_ids = {int(match.group(1)) for match in INLINE_CITATION_RE.finditer(citation_text)}
        if cited_ids != set(source_ids):
            raise ValueError(
                f"Citation/source mismatch in {story['slug']}: "
                f"uncited={sorted(set(source_ids) - cited_ids)}, "
                f"unknown={sorted(cited_ids - set(source_ids))}"
            )
        prose = " ".join(p for section in story["sections"] for p in section.get("paragraphs", []))
        if len(words(prose)) < 350:
            raise ValueError(f"Story is too short to be a full article: {story['slug']} ({len(words(prose))} words)")
        if len({section["heading"] for section in story["sections"]}) != len(story["sections"]):
            raise ValueError(f"Duplicate section heading in {story['slug']}")
    if SITE_URL.startswith("http://"):
        raise ValueError("SITE_URL must use HTTPS")


def story_lastmod(story: dict) -> str:
    updated = story.get("updated_at")
    if updated:
        return datetime.fromisoformat(updated).astimezone(SITE_TIMEZONE).date().isoformat()
    return story.get("updated", story["published"])


def build() -> dict:
    raw = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    stories = raw["stories"]
    validate(stories)
    ASSETS_PATH.mkdir(exist_ok=True)
    for directory in ("stories", "about", "editorial-policy", "advertise", "privacy"):
        (ROOT / directory).mkdir(exist_ok=True)
    shutil.copyfile(STATIC_PATH / "site.css", ASSETS_PATH / "site.css")
    shutil.copyfile(STATIC_PATH / "site.js", ASSETS_PATH / "site.js")
    (ASSETS_PATH / "favicon.svg").write_text('''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="12" fill="#19313b"/><path d="M14 46 25 17h8l11 29h-8l-2-7h-10l-2 7Zm14-13h5l-2.5-8Z" fill="#f4f7f6"/><path d="M49 22v20m-10-10h20" stroke="#0d6571" stroke-width="4" stroke-linecap="round"/></svg>''', encoding="utf-8")
    old_art = [ASSETS_PATH / "hero-orbit.svg", *ASSETS_PATH.glob("cover-*.svg")]
    for path in old_art:
        path.unlink(missing_ok=True)
    for path in ASSETS_PATH.glob("og-*.png"):
        path.unlink(missing_ok=True)
    hero_source = MEDIA_SOURCE / "hero-newsroom.png"
    optimize_webp(hero_source, ASSETS_PATH / "hero-newsroom.webp", (1200, 675))
    for story in stories:
        source = MEDIA_SOURCE / f"cover-{story['slug']}.png"
        cover = ASSETS_PATH / f"cover-{story['slug']}.webp"
        optimize_webp(source, cover, (1200, 675))
        make_og_jpg(ASSETS_PATH / f"og-{story['slug']}.jpg", story["title"], story["category"], source)
        if story.get("frontpage_asset"):
            frontpage_path = Path(story["frontpage_asset"].lstrip("/"))
            frontpage_source = MEDIA_SOURCE / f"{frontpage_path.stem}.png"
            optimize_webp(frontpage_source, ROOT / frontpage_path, (1200, 675))
    make_og_jpg(ASSETS_PATH / "og-home.jpg", "AI and developer news, with sources", "Independent AI + developer newsroom", hero_source)
    (ROOT / "index.html").write_text(homepage(stories), encoding="utf-8")
    (ROOT / "about" / "index.html").write_text(about_page(), encoding="utf-8")
    (ROOT / "editorial-policy" / "index.html").write_text(editorial_policy_page(), encoding="utf-8")
    (ROOT / "advertise" / "index.html").write_text(advertise_page(), encoding="utf-8")
    (ROOT / "privacy" / "index.html").write_text(privacy_page(), encoding="utf-8")
    for story in stories:
        directory = ROOT / "stories" / story["slug"]
        directory.mkdir(exist_ok=True)
        (directory / "index.html").write_text(article_page(story, stories), encoding="utf-8")

    page_lastmods = [
        (f"{SITE_URL}/", TODAY.isoformat()),
        (f"{SITE_URL}/about/", TODAY.isoformat()),
        (f"{SITE_URL}/editorial-policy/", TODAY.isoformat()),
        (f"{SITE_URL}/advertise/", TODAY.isoformat()),
        (f"{SITE_URL}/privacy/", TODAY.isoformat()),
    ]
    page_lastmods.extend((f"{SITE_URL}/stories/{story['slug']}/", story_lastmod(story)) for story in stories)
    urls = "\n".join(
        f'<url><loc>{xml_escape(url)}</loc><lastmod>{xml_escape(lastmod)}</lastmod></url>'
        for url, lastmod in page_lastmods
    )
    (ROOT / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>',
        encoding="utf-8",
    )
    (ROOT / "news-sitemap.xml").write_text(news_sitemap_xml(stories), encoding="utf-8")
    (ROOT / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\nSitemap: {SITE_URL}/news-sitemap.xml\n",
        encoding="utf-8",
    )
    (ROOT / "feed.xml").write_text(rss_xml(stories), encoding="utf-8")
    result = {"site_url": SITE_URL, "story_count": len(stories), "pages": len(page_lastmods), "stories": [], "assets": []}
    for story in stories:
        result["stories"].append({"slug": story["slug"], "kind": story.get("kind", "project"), "word_count": len(words(" ".join([story["lede"]] + [p for sec in story["sections"] for p in sec.get("paragraphs", [])]))), "reading_minutes": reading_time(story)})
        result["assets"].append(f"assets/cover-{story['slug']}.webp")
        result["assets"].append(story["cover_asset"].lstrip("/"))
        if story.get("frontpage_asset"):
            result["assets"].append(story["frontpage_asset"].lstrip("/"))
        result["assets"].extend(
            section["figure"]["src"].lstrip("/")
            for section in story["sections"] if section.get("figure")
        )
    result["assets"].extend(["assets/hero-newsroom.webp", "assets/og-home.jpg"])
    result["feeds"] = ["feed.xml", "sitemap.xml", "news-sitemap.xml", "robots.txt"]
    return result


def main() -> int:
    result = build()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
