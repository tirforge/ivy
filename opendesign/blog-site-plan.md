# Ivy Blog — Standard Blog Website Plan (dark/light + SEO)

> PRD-style design brief for the Ivy blog (blog.aaruvi.space) prototype.
> Source of truth for the next Design-mode generation turn.

## 1. Intent

Redesign the Ivy blog as a **standard, Medium-style blog website**:
home feed + article reading view, a working **dark/light theme toggle**,
**SEO-optimized markup**, and good UX — while **obeying every project rule**
(RULES.md, AGENTS.md, theme-design tokens).

## 2. Locked decisions

- **Style (user override, latest):** the card-grid direction (Montserrat +
  Lato) was also rejected ("not this one, use golden standard one"). Current
  direction: **golden-standard long-form editorial** — the Reddit consensus
  formula of *readable standard fonts, serif for reading, sans for structure*
  (r/Blogging "just use a readable standard font"; Reddit itself runs IBM Plex).
  Minimal chrome, centered single-column feed on Home, ~72ch serif reading
  column on Article. Distinct from the plain log-list (v1), the newspaper
  (v2), and the card-grid (v3).
- **Design system (tokens):** Figma color-combination override (user-picked,
  source of truth: https://www.figma.com/resource-library/color-combinations/):
  - **Light theme = Combination 60 "Quiet luxury"** — *Champagne* base with
    yellow/pink undertones, *muted pink* and *warm brown* hues; elegant,
    vintage, wedding/fashion-brand feel.
  - **Dark theme = Combination 85 "Frozen lake"** — *slate gray*, *icy blue*,
    *snow white*; cool, minimalist, winter-calm feel (wellness/app-style).
  - This overrides the previous Midnight Purple/Aurora token mapping for
    surfaces, text, and accent. Identity continuity is kept via **Raleway**
    display + **Google Sans** body, the aurora line signature, layout, and
    `data-od-id` sections — not via the old purple tokens. Also overrides the
    runtime-injected Atelier Zero system (project rule: evolve, don't reskin).
- **Hex swatches:** exact hex labels live inside the palette images on the
  Figma page; the two PNGs were not decodable this session, so §4 lists
  provisional hexes faithful to the named colors — to be re-verified against
  the Figma swatches at build time before committing.
- **Build base:** the Web Prototype seed class system
  (`assets/template.html`) + section layouts from `references/layouts.md`
  (adapted to the editorial-magazine identity above).
- **Fonts (from Reddit "golden standard", v4):** `IBM Plex Sans`
  (headings/UI — Reddit-grade neutral) + `IBM Plex Serif`
  (reading — long-form body), per the r/Blogging consensus + Reddit's own
  Plex usage. UI/mono stacks kept for labels/meta. Display and body families
  differ, per the rules.
  (Raleway/Google Sans v1, Playfair/Open Sans v2, Montserrat/Lato v3 all
  retired.)
- **Content:** real posts from `blog-source/_posts/` + rendered copy in
  `blog-source/_site/` (real titles, dates, tags, read-time, byline).
- **Scope default:** Home + Article. Tags/About pages are optional add-ons.

## 3. Screens & file plan

| File | Screen | Status |
|---|---|---|
| `index.html` | Home (feed) | evolves from `ivy-blog-home.html` |
| `post.html` | Article reading view | new |
| `topic.html` | Topics index (topic archive + client-side filter, renamed from `tag.html`) | new — built on request |
| `about.html` | About (bio, topics, connect) | new — built on request |

`index.html` is the entry point for the multi-file set. The current
`ivy-blog-home.html` gets folded into `index.html` (rename decision, §8).

### 3.1 Home (`index.html`)

Sections (each with `data-od-id`):

1. **Topnav** `topnav` — wordmark "Ivy" (Plex Sans 700), nav (Home · Topics ·
   About), theme toggle button. Minimal chrome: no search input, no Subscribe.
2. **Masthead** `masthead` — centered: eyebrow ("Vol. 01 · Published daily"),
   Plex Sans site title (h1) with accent period "Ivy.", italic Plex Serif
   tagline.
3. **Featured story** `featured` — editorial lead panel (max ~780px): `--surface`
   fill, 1px border, 2px `--aurora` top hairline, mono index `01`, eyebrow +
   date, large Plex Sans h2 with a Plex Serif italic key noun, dek in muted
   serif, "Read the story →" CTA. Hover: lift 2px, aurora border, CTA→accent.
4. **Latest stories** `feed` — centered ~780px column; hairline-separated
   editorial rows (meta column = mono index 01–06 · category · date; title +
   serif dek). 6 real stories, AI Tutor first.
5. **Browse by topic** `topics` — quiet text links separated by "·" (44px),
   no pills: Technology · AI · Science · Culture · Aviation · Gadgets.
6. **Footer** `footer` — wordmark · © · tagline · email.

> No newsletter / Subscribe section anywhere (user removed it on both pages).

### 3.2 Article (`post.html`)

1. **Topnav** `topnav` (same as home, no Subscribe).
2. **Breadcrumb** `breadcrumb` — Home › AI › title.
3. **Article header** `article-head` — centered: accent eyebrow (category ·
   date), Plex Sans h1, italic serif lead, byline.
4. **Figure** `figure` — 16:9 media + caption strip.
5. **Body** `article-body` — centered ~680px column, Plex Serif 18px/1.8,
   Plex Sans h2/h3, accent-rule blockquote, stat callout (Plex Serif numeral,
   hairline top/bottom rules, no card), inline source links, text tag links,
   share buttons (Twitter, LinkedIn, Telegram).
6. **Author card** `author-card` — avatar, name, bio, GitHub/email.
7. **Related posts** `related` — hairline list of 3 story rows (title + meta),
   no cards.
8. **Footer** `footer` (as home).

> No newsletter / Subscribe section (removed).

## 4. Dark / light theming

- **Mechanism:** `:root` holds dark tokens (default). A `[data-theme="light"]`
  block on `<html>` overrides the same variables. Toggle button in topnav
  (`aria-pressed`, sun/moon icon) writes `data-theme`.
- **Persistence (dual):** the toggle writes **both `localStorage` (`ivy-theme`)
  and a same-name cookie**; the inline `<head>` pre-paint reads localStorage →
  cookie → `prefers-color-scheme` → dark. Cookie is the cross-page fallback so
  the choice survives navigation even where localStorage is partitioned or
  blocked (e.g. sandboxed previews).
- **First visit:** inline `<head>` script applies saved theme, else honors
  `prefers-color-scheme` — **before first paint (no FOUC)**.
- **Meta:** `color-scheme: dark light`; `theme-color` swapped per theme.

| Token | Dark — Frozen lake (default) | Light — Quiet luxury |
|---|---|---|
| `--bg` | `#202A38` slate | `#F6F1E8` champagne |
| `--surface` | `#263140` | `#FFFFFF` |
| `--border` | `#374354` | `#E6DDCC` |
| `--fg` | `#EFF4F7` snow | `#3A2E26` warm brown |
| `--muted` | `#9AA7B8` | `#76665B` warm taupe (AA-adjusted) |
| `--accent` | `#A8D4E6` icy blue | `#9A4E57` muted rose (AA-adjusted) |
| `--accent-deep` | `#6FA9C9` | `#7C3B43` |
| `--aurora` | `#9CD0E5` | `#C08A8F` (signature line only) |

> Hexes are **named-color faithful** but were tightened from the earlier
> provisionals so both themes pass WCAG AA (light accent/muted deepened to
> stay ≥4.5:1 on champagne). Confirm exact swatch hexes from the Figma palette
> images at build time before finalizing CSS.

- Accent budget: **one accent family per screen ≤2×** (eyebrow + primary CTA).
  Aurora line = the single signature element in the accent tint; dark uses icy
  blue, light uses muted pink.
- Rule 1: **no `opacity: 0` on load-visible elements** — slide-only animation,
  `prefers-reduced-motion` respected.

## 5. Interaction & state rules

- Hover/focus pairs keep or raise contrast — never dim text toward bg. Solid
  buttons swap fg+bg together. `:focus-visible` ring on all focusables.
- Touch targets ≥ 44px; mobile ≤920px collapses all grids to 1 column, **no
  horizontal scroll**.
- Mobile pass (implemented, all four pages): sticky navbar drops
  `backdrop-filter` for a solid `var(--bg)` at ≤760px or
  `(hover:none) and (pointer:coarse)` (fixes touch-scroll blur jank); ≤400px
  compacts nav (10px gaps, 13px links, 20px wordmark). `--gutter` tightens to
  20px at ≤640px; feed rows collapse to 1 column with thumbnail first (gap 14px);
  topic chip navs scroll horizontally (nowrap + `overflow-x:auto`, hidden
  scrollbar); search input is `16px` + `appearance:none` (no iOS zoom); article
  blockquote scales to 19px and `pre`/`table` get `overflow-x:auto` at ≤640px.
- No `scrollIntoView()` (breaks embedded preview); `scrollTo()` if needed.
- No emoji as icons; inline SVG monoline marks only.

## 6. SEO plan (RULES.md §4 parity)

- Per page: unique `<title>`, meta description, canonical URL, `lang="en"`,
  robots meta. `sitemap.xml` + `robots.txt` placeholders committed (user
  finalizes URLs/lastmod before publish).
- **OG/Twitter cards** + **JSON-LD**: WebSite + Organization on Home;
  BlogPosting + BreadcrumbList on Article; AboutPage→Person on About. OG
  image meta on all four pages points at `og-cover.png` (user supplies later).
- **Feed + PWA headers:** `feed.xml` (RSS 2.0, six stories) linked via
  `<link rel="alternate">`; `favicon.svg` + `site.webmanifest` (icons ->
  `og-cover.png` placeholder) on all four pages.
- Semantic landmarks (`header`, `nav`, `main`, `article`, `aside`, `footer`),
  one `<h1>` per page, ordered headings, skip-to-content link before `main`.
- Images: explicit `width`/`height` (CLS), descriptive `alt`, `loading="lazy"`
  except LCP hero.
- Fonts: preconnect Google Fonts, **preload IBM Plex**, non-blocking load
  (`media="print" onload`).
- No AI references — reads as human editorial (RULES.md).

## 7. Content model (real data)

- **Featured candidate:** "The Gavel and the Algorithm…" (current) or evergreen
  "How I Use LLMs to Learn Complex Topics".
- **Feed posts** (real, from `_posts/`): Claude fingerprints · Pixel 9 Flipkart
  · Air India A320 · AI Tutor · Dr. Shriram Nene · UPI MDR.
- **Tags:** technology · AI · agents · science · culture · aviation · gadgets ·
  automation (real tags).
- Numbers/labels only from real posts — no invented metrics.

## 8. Rules compliance checklist

- [x] P0 checklist: tokens only in `:root`; accent ≤2×/screen; no
      purple-gradient backgrounds; no emoji icons; no invented metrics; no
      filler copy; `data-od-id` per section; mobile reflow; no
      `scrollIntoView`.
- [x] RULES.md: no `opacity:0` fade-in; IBM Plex Sans/Serif; Figma palette
      identity (Quiet luxury / Frozen lake); SEO/CLS/performance floor; no AI
      references.
- [x] Charter: contrast pairs verified in both themes; focus rings; touch
      targets; single h1; semantic markup.

## 9. Locked scope (user confirmed — lock now)

- [x] **Scope:** Home + Article was the v4 lock; **Topics + About pages built
      later on user request** (`topic.html` + `about.html`, wired into the nav,
      breadcrumb, article tags, and home topics list). The Tags archive was
      renamed to **Topics** (`tag.html` → `topic.html`, hash anchors
      `#tag-*` → `#topic-*`, canonical `/tags` → `/topics`) on user request.
- [x] **Contact (user override):** GitHub username **`tirforge`**, email
      **`thirupathi74@gmail.com`** — used in the footer, author card, about
      Connect, and JSON-LD across all four pages.
- [x] **Naming:** restructure to `index.html` (home, evolves from
      `ivy-blog-home.html`) + `post.html` (article).
- [x] **Themes:** light = Combination 60 Quiet luxury · dark = Combination 85
      Frozen lake (dark is default).
- [x] **Layout:** golden-standard long-form editorial — centered masthead +
      hairline story-list feed on Home; centered ~72ch serif reading column +
      hairline related list on Article. No marketing hero, no cards/gallery,
      no sidebar, no newsletter/Subscribe (user confirmed).
- [x] **Fonts:** IBM Plex Sans (headings/UI) + IBM Plex Serif (reading) per the
      Reddit "golden standard" consensus (v4; v1 Raleway/Google Sans, v2
      Playfair/Open Sans, and v3 Montserrat/Lato all rejected by the user).
- [x] **Caveat:** the two palette hex sets are named-color-faithful provisionals;
      final swatches will be read from the Figma palette images before the
      CSS is committed (non-blocking — build can start).

## 10. Next step

Remaining items added: **search** (index.html client-side filter, live result
count + empty state), **RSS** (`feed.xml`), **favicon/manifest** present,
**skip-link** on all four pages, **cover-image placeholders** (`.ph-img` slots
in the six feed rows). Held for the user, per instruction: real cover images,
`og-cover.png`, per-post sitemap URLs — placeholders are wired and labeled.
Verify the golden-standard build across all four pages (`index.html`,
`post.html`, `topic.html`, `about.html`): static checks (no Subscribe, no
`scrollIntoView`, hex discipline, fonts swapped, `data-od-id` counts, nav
right-aligned, transform-only motion, animations now JS-driven so they render
everywhere) then export renders for review.

Mobile pass (complete): sticky navbar jitter fixed site-wide — blur/+solid bg
fallback at `(max-width: 760px), (hover: none) and (pointer: coarse)` plus a
`(max-width: 400px)` compaction; `--gutter` → 20px at `(max-width: 640px)`;
feed rows stack with `gap: 14px` (thumb first via `order: -1`); topic chips
scroll horizontally with hidden scrollbar; search input `font-size: 16px` +
`appearance: none` (no iOS zoom); `pre`/`table`/blockquote guarded at ≤640px;
`.featured-cta` tap target padded. Verified 19 hex/file, braces balanced,
1 h1, unique `data-od-id`, 0 `scrollIntoView`, 0 authored `opacity:0`.
