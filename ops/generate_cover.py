#!/usr/bin/env python3
"""Create a neutral, clearly illustrative newsroom cover without external services."""
from __future__ import annotations

import argparse
import html
import re
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
WIDTH, HEIGHT = 1200, 675


def _font(path: str, size: int):
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def _wrap(title: str, width: int = 35, limit: int = 3) -> list[str]:
    lines = textwrap.wrap(" ".join(title.split()), width=width, break_long_words=True, break_on_hyphens=True)
    if len(lines) > limit:
        lines = lines[: limit - 1] + [lines[limit - 1].rstrip("…") + "…"]
    return lines or ["Newsroom story"]


def generate_cover(slug: str, title: str, category: str, assets_dir: Path, media_dir: Path) -> tuple[Path, Path]:
    if not SLUG_RE.fullmatch(slug):
        raise ValueError("slug must be lowercase alphanumeric words joined by hyphens")
    title = " ".join(title.split())
    category = " ".join(category.split())
    if not title or len(title) > 180 or not category or len(category) > 48:
        raise ValueError("title or category is empty or too long")

    assets_dir.mkdir(parents=True, exist_ok=True)
    media_dir.mkdir(parents=True, exist_ok=True)
    svg_path = assets_dir / f"newsroom-{slug}.svg"
    png_path = media_dir / f"cover-{slug}.png"
    lines = _wrap(title, width=32)
    title_spans = "".join(
        f'<tspan x="88" dy="{0 if index == 0 else 58}">{html.escape(line)}</tspan>'
        for index, line in enumerate(lines)
    )
    label = html.escape(category.upper())
    svg_path.write_text(
        f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 675" role="img" aria-labelledby="title desc">
<title id="title">Editorial illustration: {html.escape(title)}</title>
<desc id="desc">Abstract typographic newsroom cover for {html.escape(title)}. This is an illustration, not a product screenshot or photograph.</desc>
<defs><linearGradient id="background" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#19313b"/><stop offset="1" stop-color="#0d6571"/></linearGradient><radialGradient id="glow"><stop stop-color="#d6ec6b" stop-opacity=".42"/><stop offset="1" stop-color="#d6ec6b" stop-opacity="0"/></radialGradient></defs>
<rect width="1200" height="675" fill="url(#background)"/><circle cx="1010" cy="148" r="310" fill="url(#glow)"/><circle cx="1010" cy="148" r="176" fill="none" stroke="#d6ec6b" stroke-opacity=".42" stroke-width="2"/><circle cx="1010" cy="148" r="230" fill="none" stroke="#d6ec6b" stroke-opacity=".22" stroke-width="2" stroke-dasharray="5 13"/>
<path d="M700 90v495M760 90v495M820 90v495M880 90v495M940 90v495M1000 90v495M1060 90v495" stroke="#fff" stroke-opacity=".055"/><path d="M80 105H660" stroke="#d6ec6b" stroke-width="3"/>
<text x="88" y="82" fill="#d6ec6b" font-family="Arial,sans-serif" font-size="20" font-weight="700" letter-spacing="4">{label}</text>
<text x="88" y="230" fill="#f6f8fb" font-family="Arial,sans-serif" font-size="49" font-weight="700">{title_spans}</text>
<rect x="88" y="512" width="24" height="24" rx="12" fill="#d6ec6b"/><text x="132" y="531" fill="#f6f8fb" font-family="Arial,sans-serif" font-size="15" letter-spacing="2">NEWSROOM ILLUSTRATION · NOT A SCREENSHOT</text>
<text x="88" y="604" fill="#d9e2e6" font-family="Arial,sans-serif" font-size="18" letter-spacing="3">AMIT + HERMES NEWSROOM</text></svg>''',
        encoding="utf-8",
    )

    image = Image.new("RGB", (WIDTH, HEIGHT), "#19313b")
    draw = ImageDraw.Draw(image)
    top, bottom = (25, 49, 59), (13, 101, 113)
    for y in range(HEIGHT):
        blend = y / max(1, HEIGHT - 1)
        color = tuple(round(top[i] * (1 - blend) + bottom[i] * blend) for i in range(3))
        draw.line((0, y, WIDTH, y), fill=color)
    draw.ellipse((790, -140, 1230, 300), outline=(214, 236, 107), width=3)
    draw.ellipse((735, -195, 1285, 355), outline=(214, 236, 107), width=2)
    draw.ellipse((870, -60, 1150, 220), fill=(214, 236, 107, 25))
    label_font = _font("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 21)
    title_font = _font("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
    footer_font = _font("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    draw.line((88, 105, 650, 105), fill=(214, 236, 107), width=3)
    draw.text((88, 62), category.upper(), font=label_font, fill=(214, 236, 107))
    for index, line in enumerate(lines):
        draw.text((88, 185 + index * 64), line, font=title_font, fill=(246, 248, 251))
    draw.rounded_rectangle((88, 504, 1160, 552), radius=14, fill=(25, 49, 59))
    draw.text((112, 517), "NEWSROOM ILLUSTRATION  ·  NOT A SCREENSHOT", font=footer_font, fill=(246, 248, 251))
    draw.text((88, 600), "AMIT + HERMES NEWSROOM", font=footer_font, fill=(217, 226, 230))
    image.save(png_path, "PNG", optimize=True)
    return svg_path, png_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slug", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--category", required=True)
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.project_root.resolve()
    svg_path, png_path = generate_cover(
        args.slug, args.title, args.category,
        root / "assets", root / "media-source-v3",
    )
    print(f"Created illustration: {svg_path}")
    print(f"Created raster source: {png_path}")
    print("Not a screenshot or photograph.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())