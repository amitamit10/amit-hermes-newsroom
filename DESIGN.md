---
version: alpha
name: Release Desk
description: A source-forward project newsroom with product clarity and newsroom hierarchy.
colors:
  primary: "#19313B"
  secondary: "#596D75"
  tertiary: "#0D6571"
  accent-strong: "#084E59"
  neutral: "#F4F7F6"
  surface: "#FFFFFF"
  border: "#D9E1E0"
  inverse: "#19313B"
  on-primary: "#FFFFFF"
  signal-lime: "#D6EC6B"
  status-open-source: "#176A53"
  status-open-source-surface: "#E8F6EF"
  status-early: "#805000"
  status-early-surface: "#FFF3D9"
  status-gated: "#184D82"
  status-gated-surface: "#EAF2FB"
  status-candidate: "#614894"
  status-candidate-surface: "#F1ECF8"
  status-caution: "#9B3D35"
  status-caution-surface: "#F9ECE9"
  status: "{colors.status-open-source}"
  status-surface: "{colors.status-open-source-surface}"
typography:
  h1:
    fontFamily: Manrope
    fontSize: 3.75rem
    fontWeight: 750
    lineHeight: 1.02
    letterSpacing: "-0.05em"
  h2:
    fontFamily: Manrope
    fontSize: 2.25rem
    fontWeight: 700
    lineHeight: 1.08
    letterSpacing: "-0.035em"
  body-md:
    fontFamily: Manrope
    fontSize: 1rem
    fontWeight: 450
    lineHeight: 1.7
  label-md:
    fontFamily: IBM Plex Mono
    fontSize: 0.75rem
    fontWeight: 500
    lineHeight: 1.5
    letterSpacing: "0.04em"
rounded:
  sm: 6px
  md: 10px
  lg: 18px
spacing:
  sm: 8px
  md: 16px
  lg: 24px
  xl: 40px
  xxl: 64px
components:
  button-primary:
    backgroundColor: "{colors.tertiary}"
    textColor: "{colors.on-primary}"
    rounded: "{rounded.sm}"
    padding: 12px
  button-primary-hover:
    backgroundColor: "{colors.accent-strong}"
    textColor: "{colors.on-primary}"
    rounded: "{rounded.sm}"
    padding: 12px
  status-pill:
    backgroundColor: "{colors.status-surface}"
    textColor: "{colors.status}"
    rounded: "{rounded.sm}"
    padding: 8px
  status-open-source-pill:
    backgroundColor: "{colors.status-open-source-surface}"
    textColor: "{colors.status-open-source}"
    rounded: "{rounded.sm}"
    padding: 8px
  status-early-pill:
    backgroundColor: "{colors.status-early-surface}"
    textColor: "{colors.status-early}"
    rounded: "{rounded.sm}"
    padding: 8px
  status-gated-pill:
    backgroundColor: "{colors.status-gated-surface}"
    textColor: "{colors.status-gated}"
    rounded: "{rounded.sm}"
    padding: 8px
  status-candidate-pill:
    backgroundColor: "{colors.status-candidate-surface}"
    textColor: "{colors.status-candidate}"
    rounded: "{rounded.sm}"
    padding: 8px
  status-caution-pill:
    backgroundColor: "{colors.status-caution-surface}"
    textColor: "{colors.status-caution}"
    rounded: "{rounded.sm}"
    padding: 8px
  signal-highlight:
    backgroundColor: "{colors.signal-lime}"
    textColor: "{colors.primary}"
    rounded: "{rounded.sm}"
    padding: 8px
  newsroom-canvas:
    backgroundColor: "{colors.neutral}"
    textColor: "{colors.primary}"
    rounded: "{rounded.md}"
    padding: 16px
  supporting-copy:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.secondary}"
    rounded: "{rounded.md}"
    padding: 16px
  rule-divider:
    backgroundColor: "{colors.border}"
    textColor: "{colors.primary}"
    rounded: "{rounded.sm}"
    padding: 1px
  inverse-surface:
    backgroundColor: "{colors.inverse}"
    textColor: "{colors.on-primary}"
    rounded: "{rounded.md}"
    padding: 16px
---

## Overview

**Release Desk** is an Explore-first independent newsroom for public software projects, build notes, and source-linked AI/developer reporting. The homepage starts with a compact masthead and one topic-navigation rail, followed by a source-backed lead with clean, text-free artwork and a compact latest feed. The lead is selected by publication date; the full archive remains searchable and filterable. Keep the story headline in HTML rather than repeating it inside the artwork. Avoid extra editorial strips and headline tickers that compete with the lead. Use editorial hierarchy and pace as general inspiration, but keep Release Desk's own palette, typography, assets, copy, and layout; do not copy Geektime's wordmark, colors as brand identity, assets, text, or distinctive arrangement.

The publication is human-accountable, not necessarily human-authored. Disclose AI-generated reporting and whether it was individually reviewed; never imply official affiliation with Nous Research or any platform referenced in an article.

## Colors

- **Primary (#19313B):** deep blue-green ink for headlines, navigation, and high-emphasis text.
- **Secondary (#596D75):** readable supporting copy and metadata.
- **Tertiary (#0D6571):** restrained teal for actions, source links, focus indicators, and active navigation.
- **Signal (#D6EC6B):** limited lime highlight for a small number of release/action accents, never the main status system.
- **Neutral (#F4F7F6), Surface (#FFFFFF), and Border (#D9E1E0):** calm cool canvas, article surfaces, and quiet separators.
- **Status colors communicate project state, always alongside a text label:** green (#176A53) for public/open source; amber (#805000) for early/experimental; blue (#184D82) for authorization-gated; violet (#614894) for local candidate; muted red (#9B3D35) only for caution.
- Use the paired pale status surfaces defined in the tokens. Keep status labels visible in text and never rely on color alone; do not use a positive green for experimental or candidate work.

## Typography

Use Manrope for display and reading text: clear, modern, human, and not a copy of OpenAI Sans, Anthropic's brand type, or Apple's SF family. Use IBM Plex Mono only for compact issue, date, repository, and status metadata. Keep headlines sans-serif, left-aligned, and short; long-form body text should remain at least 15px, while compact card deks and metadata may be smaller. Do not use italic serif headlines or all-caps paragraph copy.

## Layout

Use a 1160px maximum content width and a flexible two-column desktop composition with purposeful whitespace. The homepage order is masthead, one horizontally scrollable topic navigation row with a subtle mobile edge fade when topics overflow, one source-backed lead story with clear non-text artwork, then the compact Latest feed beside it on desktop and below it on mobile. Keep date, topic, AI/byline or project status, source links, and the read action easy to scan. Do not repeat the story title inside its artwork or add a separate headline ticker/editorial strip above the lead. Follow with one clearly labeled ad placeholder, a searchable/filterable archive, credit explanation, and contact. Article pages use a readable main column and a source/status rail; on narrow screens, move the rail above the article body and retain visible source links. Reflow cleanly at 1024px, 768px, and 320/360/390px. Treat phones as the primary layout: show the lead image first, keep touch controls and source actions at least 44px high, tags at least 40px, and mobile long-form body copy at 16px. Allow horizontal scrolling only inside the intentional topic rail or expanded diagrams/data tables, never at page level. Respect reduced-motion preferences.

## Elevation & Depth

Prefer 1px borders and flat surfaces. Use a small shadow only where it helps separate the featured story; no glassmorphism, decorative gradients, parallax, or oversized blurred glows. Media may use dark studio imagery to signal product context, but the surrounding interface stays calm and light.

## Shapes

Use 6px controls, 10px standard media panels, and at most 18px for the single featured story container. Avoid pill-shaped buttons, oversized rounded cards, and floating decorative badges. Keep focus rings obvious and high-contrast.

## Components

- **Primary button:** teal background, white text, compact and rectangular; hover to darker teal without changing its label.
- **Source link:** teal text link with an explicit repository name and external-link cue; never hide the source behind an icon-only control.
- **Project status:** readable text in a semantic status row or pill; preserve qualifiers such as “candidate” and “early release” exactly. Use the matching token color and tint, and keep red for cautions only.
- **Story index row:** date, category, status, title, short dek, and source/read actions in a clear hierarchy. Search, topic/status filters, selected states, and clear-all must work together and remain keyboard-operable.
- **Article tools:** provide section navigation, reading progress, copy-link feedback, focusable source references, and an accessible expand-dialog for diagrams. Numeric charts must expose their exact source data in a readable disclosure/table.
- **Generated artwork:** use GPT Images only as explicitly identified conceptual artwork. It is not a screenshot or evidence of actual software UI.

## Do's and Don'ts

- Do keep the homepage Explore-first: readers can see actual topics and the current source-backed lead before promotional content.
- Do lead with source, author credit, status, and limits; use existing verified story facts only.
- Do preserve search, category/status filters, URL-shareable state, clear-all, RSS, sitemap, canonical metadata, keyboard operation, visible focus, and reduced-motion behavior.
- Do meet WCAG AA text contrast (4.5:1 for normal text) and pair each status color with an explicit text label; reserve red for caution only.
- Don't make a control look interactive unless it has a useful action; don't hide chart values from readers who cannot interpret an SVG.
- Don't invent user counts, adoption, performance claims, testimonials, release dates, or endorsements.
- Don't make generated art look like a real product screenshot; label it as conceptual artwork in both visible captions and image alt text.
- Don't use warm paper/terracotta still-life styling, generic AI-brain imagery, copied brand marks, or visually identical layouts from the reference companies.
