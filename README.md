# Amit + Hermes Newsroom

An English-first independent publication about AI, agents, open-source tools, and developer work. This repository contains the static-site generator, its source content and artwork, tests, and the generated pages served by the live site.

**Live site:** <https://amit-hermes-newsroom.vercel.app>

The publication is independent and is not an official Nous Research newsroom or endorsement. It identifies AI-generated reporting, links to its sources, and distinguishes project status from shipped or publicly released work. Ad placements are labeled placeholders; no advertising scripts or tracking are included.

## Run locally

Requirements: Python 3.10+ and Pillow.

```sh
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install Pillow
python3 build.py
python3 -m unittest discover -s tests -v
python3 -m http.server 4173
```

Open <http://localhost:4173/>. The builder writes crawlable HTML pages, local assets, RSS, robots.txt, and standard/news sitemaps into the repository root. The generated pages are committed too, so the site can also be served directly as static files.

## Project layout

- `build.py` — validates the stories and generates the static publication.
- `data/stories.json` — source-linked editorial content and publication metadata.
- `static/` — authored CSS and JavaScript; copied into `assets/` by the build.
- `media-source-v3/*.png` — image masters used to produce optimized local WebP/JPEG assets.
- `assets/` — generated artwork, article visuals, icons, and social images.
- `ops/generate_cover.py` — local, offline illustration helper for news covers.
- `tests/` — build, content, accessibility, and interaction checks.

## Editing and rebuilding

Edit `data/stories.json`, then run `python3 build.py`. `SITE_URL` controls canonical links and sitemap/feed URLs when rebuilding for another host:

```sh
SITE_URL=https://your-domain.example python3 build.py
```

The builder uses Pillow for image optimization. Static pages require no database, server-side runtime, or AI API. For a static host, use the repository root as the output directory and run `python3 build.py` as the build command.

## Editorial and artwork notes

Stories preserve source links and claim-level citations. News reports disclose AI authorship and review status; the copy does not imply that generated cover art is a screenshot or photograph. The newsroom's stories describe projects and public sources, not an official relationship with the software vendors they cover.

## License

No license file is included. Public availability of this repository does not grant a separate license to reuse its code, content, or artwork.
