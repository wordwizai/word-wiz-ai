# SEO architecture

Short version of how pages get their meta tags, and the traps that already bit
this repo once.

## Where per-page tags come from

`index.html` is served for **every** route, so anything page-specific placed in
it appears on all 154 pages. That is exactly how every article, guide and
comparison page ended up declaring `<link rel="canonical" href="https://wordwizai.com/">`
and looking like a duplicate of the homepage.

Per-page tags therefore come from `react-helmet-async`:

| Route kind | Source |
|---|---|
| `/`, `/about`, `/contact`, `/privacy` | `components/SeoHead.tsx` |
| articles, guides, most comparisons | `components/ArticlePageTemplate.tsx` |
| 3-way comparisons | `components/ComparisonPageTemplate.tsx` |
| `/practice-words/*` | `components/PracticePageTemplate.tsx` |
| `/practice-words` hub | `pages/PracticeWordsHub.tsx` |

`scripts/prerender.mjs` then bakes each route's rendered tags into static HTML,
because Bing, GPTBot, ClaudeBot, PerplexityBot and every social unfurler run no
JavaScript.

**Do not put page-specific tags in `index.html`.** The ones there are fallbacks
for routes that render no Helmet block.

**Do not put explanatory prose in `index.html` comments either.** Comments ship
to every page. A previous version of this note contained the words `noindex`
and `<title>`, which shipped in the HTML of all 154 pages and tripped naive
SEO checkers.

## The build gate

`npm run build` runs the prerender, which refuses to write anything if any page
has a missing/duplicate/mismatched title, canonical or meta description, a
title identical to the homepage's, an empty `#root`, or a `relatedSlugs` entry
that resolves to no pattern.

If the build fails on SEO validation, that is the gate doing its job. Fix the
page rather than loosening the check.

## robots.txt is NOT fully under our control

`public/robots.txt` is only the **second half** of what the domain serves.
Cloudflare prepends a managed block. As of 2026-09-08 the live file begins with
Cloudflare's content-signal header and disallows these crawlers site-wide:

```
Amazonbot, Applebot-Extended, Bytespider, CCBot, ClaudeBot,
CloudflareBrowserRenderingCrawler, Google-Extended, GPTBot, meta-externalagent
```

plus `Content-Signal: search=yes, ai-train=no, use=reference`.

**Not blocked:** `bingbot`, `Googlebot`, `PerplexityBot`.

So Google Search and Bing indexing are unaffected — `Google-Extended` governs
Gemini grounding/training, not Search. But OpenAI's and Anthropic's own
crawlers cannot fetch the site, which limits the value of `llms.txt` and
`llms-full.txt`.

This is a Cloudflare dashboard setting, not a repo change. Whether to keep it
is a policy call: blocking AI training crawlers is a legitimate choice, it just
trades away LLM-citation reach.

**Always check the live file, not the repo file:**

```bash
curl -s https://wordwizai.com/robots.txt
```

## Verifying a deploy

```bash
cd frontend
npm run verify:live     # confirms production serves prerendered HTML
npm run indexnow        # pushes all URLs to Bing/Yandex (after deploying)
```

`verify:live` fails if any checked page returns the homepage's title or
canonical, which is the signature of prerendering not being served.

## Regenerating the social card

```bash
npm run og:image
```

Built from the real design system (Poppins, Charis SIL for phonemes, the logo
read from `public/wordwizIcon.svg`, brand purple and gold). `og:image` must
point at a file that actually ships — the SPA rewrite returns `index.html` with
a **200** for any missing path, so a wrong filename serves crawlers HTML
labelled as a PNG rather than a clean 404.
