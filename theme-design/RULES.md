# 📜 RULES.md — Ivy Blog Source

**Handover rules for anyone working on the Jekyll site** (`blog-source/`, live at **https://blog.aaruvi.space**).
Follow these. They exist because each one was learned the hard way.

---

## 1. Architecture (30-second map)

```
blog-source/
├── _sass/custom/custom.scss      ← ALL custom styling (1,200+ lines) — the main design file
├── _includes/custom/             ← head.html (fonts/meta/JSON-LD), post.html, tail.html
├── _layouts/                     ← site overrides (home/post/tags/about.html). Theme layouts stay in vendor/
├── _tabs/                        ← about.md, tags.md (page skeletons)
├── _posts/YYYY-MM-DD-slug.md     ← blog posts (Chirpy frontmatter)
├── _config.yml                   ← site config: url, collections, jekyll-archives, etc.
├── sitemap.xml                   ← custom posts-only sitemap (jekyll-sitemap removed — see §4)
├── assets/robots.txt             ← THE robots.txt (site file beats theme file — see Rule 3)
└── vendor/bundle/                ← theme + gems. NEVER edit. Treat as read-only.
```

Stack: **Jekyll 4.4.1 + Chirpy 7.5** (editorial golden-standard custom theme — dark “Frozen lake” / light “Quiet luxury”, IBM Plex), built via GitHub Actions → gh-pages → Cloudflare proxy.

---

## 2. Design system (implemented — keep it)

Design source: `opendesign/` + `blog-site-plan.md`. Dark (default) = **Frozen lake** (Combo 85), light = **Quiet luxury** (Combo 60). Tokens live ONLY in `:root`/`[data-theme='light']` in `custom.scss`; the toggle (`data-theme` on `<html>`, `ivy-theme` localStorage + cookie) switches them.

| Token | Dark — Frozen lake | Light — Quiet luxury | Use |
|-------|--------------------|----------------------|-----|
| `--bg` | `#202A38` slate | `#F6F1E8` champagne | page base |
| `--surface` | `#263140` | `#FFFFFF` | raised panels |
| `--border` | `#374354` | `#E6DDCC` | hairlines, dividers |
| `--fg` | `#EFF4F7` snow | `#3A2E26` warm brown | body text |
| `--muted` | `#9AA7B8` | `#76665B` warm taupe | muted text |
| `--accent` | `#A8D4E6` icy blue | `#9A4E57` muted rose | links, active nav, focus, tags |
| `--aurora` | `#9CD0E5` | `#C08A8F` | signature hairline only |
| Display font | IBM Plex Sans | IBM Plex Sans | headings/UI |
| Body font | IBM Plex Serif | IBM Plex Serif | reading |

Chirpy's own `data-mode` system is locked to dark (`theme_mode: dark` in `_config.yml`) so it never fights the editorial `data-theme` toggle.

---

## 3. Hard rules (break these = break the site)

### 🚫 Rule 1 — NEVER animate `opacity: 0` on load-visible elements
The page fade-in **must not start at `opacity: 0`**. Google's mobile Lighthouse treats a first frame at opacity 0 as "no content painted" → NO_FCP → every PSI audit errors while desktop scores fine. This exact bug was shipped and fixed (commit `d304b06`).

```scss
/* ✅ correct — slide only, no opacity */
@keyframes fadeIn {
  from { transform: translateY(8px); }
  to   { transform: translateY(0); }
}
/* ❌ never this: from { opacity: 0; ... } */
```
Also: respect `prefers-reduced-motion`.

### 🚫 Rule 2 — jekyll-archives layout names have NO `.html`
Jekyll's `LayoutReader` keys layouts by filename **without extension** (`tag.html` → `"tag"`). Writing `tag: tag.html` makes every tag page 404 with "Layout does not exist" (commit `9091877`).

```yaml
# _config.yml — correct:
jekyll-archives:
  enabled: [tags, categories]
  layouts: { tag: tag, category: category }   # no .html!
  permalinks: { tag: /tags/:name/, category: /categories/:name/ }
```

### 🚫 Rule 3 — robots.txt lives in `assets/robots.txt`
Chirpy's theme has its own `robots.txt` which **wins via permalink** over a root-level file. To control robots, edit **`assets/robots.txt`** (site file overrides theme). Never re-create `blog-source/robots.txt`. Current file: `Allow: /` for all + Sitemap line. Cloudflare may merge its own managed AI-crawler blocklist on top — that's fine, it doesn't block Google.

### 🚫 Rule 4 — never edit theme files
Anything under `vendor/bundle/` or the theme's own `_layouts/`/`_sass/` is read-only. To override:
- Styles → append to `_sass/custom/custom.scss` (it's included last, wins)
- Layout HTML → copy the theme file into `_layouts/` and edit the copy

### 🚫 Rule 5 — numeric tags must be quoted
YAML parses bare numbers: `tags: [00000]` → integer → octal parse crash on build. Always quote numeric tags in post frontmatter: `tags: ["00000"]`. (Tag `00000` exists on old posts from an extract_tags bug — harmless now, renders fine, but ugly in the trending list; clean up if touching those posts.)

---

## 4. SEO rules (all verified live — don't regress)

- **Canonical/URL**: `https://blog.aaruvi.space` (no baseurl). GitHub Pages URL `tirforge.github.io/ivy/` 301-redirects here — expected, don't "fix" it.
- **Tag/category pages**: `/tags/:name/` + `/categories/:name/` exist (rendered by jekyll-archives) but are **deliberately excluded from the sitemap** (low-value listing pages — the sitemap is posts + about only). Post meta links to them. Never remove jekyll-archives.
- **Sitemap**: CUSTOM `sitemap.xml` at `blog-source/sitemap.xml` (posts-only, ~75 URLs + real `lastmod`). `jekyll-sitemap` was **removed from `_config.yml` plugins** (its ~120-URL output leaked tags/categories/pagination junk into the index). Keep the custom file in sync — adding `sitemap: true` to a page's frontmatter includes it. Deploy workflow submits to IndexNow + GSC.
- **Meta**: OG/Twitter/JSON-LD (WebSite, Organization, BlogPosting, Breadcrumb) all in `_includes/custom/head.html`. Keep them in sync when editing head.
- **Mermaid**: frontmatter `mermaid: true` required; dark theme configured via `window.mermaid` in head.html.
- **Images**: always explicit `width`/`height` (CLS), `loading="lazy"` except LCP, Unsplash `data-unsplash-dl` on inline images.
- **No AI references** in rendered pages — the blog reads as human editorial.
- **Performance floor**: preload the LCP image (favicons.html) + preconnect Google Fonts + jsdelivr + Unsplash, non-blocking stylesheets via `media="print" onload`. CDN scripts load individually (site `js-selector.html` override) — no giant jsdelivr combine request.

---

## 5. Content rules (what the crew writes)

- **Length**: 600–900 words (news topics) / 1,200–1,500 (evergreen) — 4–5 sections + intro + conclusion.
- **Format**: emoji headers, Mermaid diagrams, blockquotes, bullets, inline source links. Every claim sourced.
- **Frontmatter** (Chirpy): `title`, `date`, `tags` (quoted numerics!), `categories` (tech|science|culture), `image` (Unsplash cover), `mermaid: true` when diagrams used, `math: true` when LaTeX.
- Pipeline: Writer (research) → Humaniser (natural tone) → Editor (fact-check/polish). Don't skip stages.

---

## 6. Workflow

```bash
# local dev (from blog-source/)
bundle exec jekyll serve        # http://localhost:4000

# build + verify (do this before committing)
JEKYLL_ENV=production bundle exec jekyll build
# then check: no "does not exist" warnings in output

# deploy
git add -A && git commit -m "<conventional message>" && git push origin main
gh workflow run rebuild-deploy.yml --repo tirforge/ivy   # or ask the assistant
```

- **Commits**: conventional style (`fix(seo): …`, `feat(ui): …`). CI commits get `[skip ci]`.
- **Never** deploy by editing gh-pages directly — always through the rebuild-deploy workflow (it runs publish → build → deploy → IndexNow → GSC → cache purge).
- `Gemfile.lock` is gitignored — CI resolves deps itself.

---

## 7. Acceptance checklist (before you call it done)

- [ ] `jekyll build` completes with **zero** "does not exist" / error warnings
- [ ] No `opacity: 0` on anything visible at page load
- [ ] Tag + category pages still render (`/tags/technology/`, `/categories/tech/` → 200 with posts)
- [ ] robots.txt still served from `assets/robots.txt` (has Sitemap line)
- [ ] Sitemap URL count sane (posts + about only, ~76 — no tags/categories/pagination), generated from custom `blog-source/sitemap.xml`
- [ ] Live check after deploy: `curl -sL -o /dev/null -w "%{http_code}" https://blog.aaruvi.space/` → 200
- [ ] Mobile PageSpeed gives a real score (no NO_FCP errors)
- [ ] No theme files touched; all changes in custom layer

---

## 8. Known quirks (don't be surprised)

- Cloudflare proxies the site; `cf-cache-status: DYNAMIC` on HTML is normal.
- Cloudflare serves its own managed robots.txt additions (AI-crawler blocklist) — expected.
- PSI mobile can transiently fail with NO_FCP even on a healthy site — retry after 30 min before suspecting your code.
- Chrome `--headless=new` + `--screenshot` is the fastest way to visually verify a design change.

---

## 9. OpenDesign handoff (design workflow)

- **Token source of truth**: `theme-design/design-tokens.json` (W3C Design Tokens format) — extracted from `_sass/custom/custom.scss`. Import into OpenDesign via **Design Tokens → Import JSON**. Regenerate by re-extracting from the SCSS when the theme changes.
- **Design flow**: OpenDesign → tokens → components → export HTML/CSS → port into `_sass/custom/custom.scss` + `_includes/custom/`. Keep §2 (Frozen lake / Quiet luxury) as the identity — evolve, don't reskin.
- **Verification**: `chrome --headless=new --screenshot` against `bundle exec jekyll serve` (localhost:4000) is the fastest visual check (see §8).
