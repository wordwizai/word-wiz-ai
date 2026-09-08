# The weekly content improvement loop

Goal: a compounding, mostly-unattended growth engine. Each week, find queries
Google already wants to rank for `wordwizai.com` — pages sitting at position
8-20, just below the fold — and either sharpen the existing page or write a
new one targeted at the query. Repeat.

This doc is the playbook for *acting on* `growth/gsc-opportunities.md`. For
generating that report in the first place, see:
- [`../implementation_guides/SEARCH_CONSOLE_SETUP.md`](../implementation_guides/SEARCH_CONSOLE_SETUP.md) — create the property, verify DNS (do this first)
- [`GSC_API_SETUP.md`](./GSC_API_SETUP.md) — service-account credentials for the script
- `frontend/scripts/gsc-report.mjs` — generates the report

Nothing below works until those exist and Search Console has ~28 days of
data. Until then, `node scripts/gsc-report.mjs --sample-data` produces a
synthetic report with the same shape, purely so you can see what this
playbook is reacting to.

---

## 1. How to read the report

`growth/gsc-opportunities.md` (and the machine-readable
`growth/gsc-opportunities.json` behind it) has two tables.

### Opportunities: queries at position 8-20 with low CTR

Each row is one query, the page it's currently ranking with, and how far its
click-through rate is below what *this site itself* normally gets at that
position (`expectedCtr`, computed from the site's own data — not an external
industry benchmark, since those vary too much by query type to be honest
about). `estimatedClicksLeftOnTable` is `impressions × (expectedCtr − ctr)`
for that query over the report's 28-day window — a rough sense of scale for
prioritizing, not a promise.

Position 8-20 specifically because that's the band where Google has already
decided the page is relevant enough to show, but not relevant/authoritative
enough for page one. That's a much higher-leverage place to spend effort
than a query at position 45, where the page may not be a good match at all.

### CTR problem pages

Whole pages (any position) with high impressions but CTR well below the
site average. This is a narrower, cheaper fix: **only the title and meta
description need to change.** The page is already earning impressions at a
reasonable position; something about the snippet Google shows in search
results is failing to earn the click. Don't rewrite content for these —
rewrite the `metaTitle`/`metaDescription` props and stop.

---

## 2. Decision rule: improve the existing page, or write a new one

Work through the opportunity table one page at a time (a page can have
multiple opportunity queries — handle them together).

```
For each page that has 1+ opportunity queries:

  Open the page's source file (frontend/src/pages/{guides,comparisons,articles}/*.tsx)
  and read its `content: ArticleSection[]` (or comparison props).

  Does the page already directly answer the query's intent — same topic,
  same format (how-to vs. comparison vs. diagnostic "why does my kid..."),
  just not phrased/emphasized the way the query is phrased?

    YES → IMPROVE the existing page:
      - Rewrite metaTitle / metaDescription to mirror the query's exact
        phrasing (this is the single biggest CTR lever — do it even if
        you do nothing else)
      - If the query implies a sub-topic the page doesn't cover yet, add
        an ArticleSection (heading + paragraph, or a "callout") for it
        rather than padding existing sections
      - Add/strengthen internal links to this page from other pages that
        already rank well, using anchor text close to the query
      - Do NOT change canonicalUrl — it must keep matching the route

    NO, it's a different intent or format →  WRITE A NEW PAGE:
      - "X vs Y", "best X" → ComparisonPageTemplate, goes under
        frontend/src/pages/comparisons/, route /comparisons/...
      - "how to...", "why does my child...", diagnostic/how-to →
        ArticlePageTemplate, under frontend/src/pages/guides/ (instructional)
        or frontend/src/pages/articles/ (diagnostic/problem-focused) —
        check both existing directories for which tone fits
      - Cross-link the new page and the old one in both directions so
        they reinforce rather than cannibalize each other
```

Tie-breakers when it's not obvious:

- **Same page, multiple opportunity queries, same intent** → strong signal
  to improve, not split. The page is close; sharpen it.
- **One page is trying to serve two clearly different intents** (e.g. it's
  both the "how to teach X" answer and picking up "X vs Y" traffic it was
  never written for) → keep the page for whichever intent it matches best,
  spin the other into a new page, cross-link.
- **Before creating anything new, check `frontend/src/pages/guides/`,
  `comparisons/`, and `articles/` for a near-duplicate.** If one already
  covers the topic, that's an "improve," not a "new page" — this codebase
  already has 35+ SEO pages; check before adding a 36th that overlaps.
- **When genuinely unsure, improve first.** It's cheaper, ships faster, and
  doesn't risk two pages competing for the same query. Only write a new page
  if a later week's report shows the query still isn't moving after the
  existing page was sharpened.

CTR-problem-page rows skip this decision entirely — see above, it's always
a title/description edit, never new content.

---

## 3. The reusable agent prompt

This is written to be handed to an AI coding agent (Claude Code or
otherwise) running inside this repo, once a real `growth/gsc-opportunities.md`
exists. Copy it as-is; the bracketed parts are what you fill in per run.

````text
You are acting on this week's Search Console opportunity report at
growth/gsc-opportunities.md (data: growth/gsc-opportunities.json). Read it
first.

Task: [paste one row or one page's worth of rows from the "Opportunities"
table, OR paste one row from the "CTR problem pages" table — do one page
per run, not the whole report at once]

Follow the decision rule in growth/CONTENT_LOOP.md section 2 to decide
whether this is an "improve existing page" or "write new page" case, and
say which you picked and why before making changes.

If CTR-problem-page row: only change metaTitle and metaDescription (and
their og:/twitter: mirrors, which the templates already derive from them —
don't add separate ones). Nothing else about the page changes.

If improving an existing page: read its current source in
frontend/src/pages/{guides,comparisons,articles}/*.tsx. Its `content` prop
is an ArticleSection[] (defined in frontend/src/components/ArticlePageTemplate.tsx)
— each entry is one of:
  { type: "heading", level: 2 | 3, content: string, id?: string }
  { type: "paragraph", content: string }   // "**bold**" is supported inline
  { type: "list", content: string[] }
  { type: "image", content: { src, alt, caption? } }
  { type: "callout", content: { type: "info"|"tip"|"warning"|"success", title?, content } }
Match the existing voice and structure. Prefer adding one well-placed
section over rewriting the page. Update metaTitle/metaDescription to mirror
the target query's phrasing.

If writing a new page: pick ArticlePageTemplate (guides/ for instructional,
articles/ for diagnostic "my child does X" problems) or
ComparisonPageTemplate (comparisons/, for "X vs Y" / "best X" queries) —
see frontend/src/components/ArticlePageTemplate.tsx and
ComparisonPageTemplate.tsx for the full prop shapes, and an existing page in
the matching directory (e.g. frontend/src/pages/guides/TeachCVCWords.tsx)
as a worked example of every prop including structuredData and breadcrumbs.
Then:
  1. Create the new .tsx file following the naming/casing convention already
     used in that directory.
  2. Register its route in frontend/src/App.tsx: add a lazy import next to
     the other pages in the same section, and a <Route path="..." element=.../>
     in the matching "{Comparison,Article,Guide} Pages" block. The route's
     path segment becomes part of the URL and MUST exactly match
     canonicalUrl's path (canonicalUrl is always https://wordwizai.com<path>).
  3. Add the new URL to frontend/public/sitemap.xml, following the existing
     <url> entries' format exactly.
  4. Add 2-4 internal links between the new page and related existing pages
     (via relatedArticles, or an inline link in a paragraph/list item).

Hard constraints, non-negotiable — frontend/scripts/prerender.mjs enforces
these as a build gate and the production build FAILS if you violate them:
  - Exactly one <title> per page (comes from the page's own <Helmet><title>;
    never touch frontend/index.html's fallback tags)
  - Exactly one <link rel="canonical">, and it must equal
    https://wordwizai.com + the route's path, exactly (trailing slash only
    for the homepage)
  - At most one <meta name="description">
  - The page's <title> must differ from the homepage's — i.e. don't skip
    the Helmet block
Every page template here already produces exactly this shape via its single
<Helmet> block, so as long as you don't add a second one or hand-edit
index.html, you're fine by construction.

When you're done, verify it actually passes the gate — don't just assert it
does:
  cd frontend
  npm run build:prerender
This builds, prerenders every route (including your new one, auto-discovered
from App.tsx), and runs the validation described above. It fails loudly
with a specific list of problems if anything's wrong. Only report the task
done once this passes clean.
````

A few notes on why the prompt is shaped this way: it forces one page per
run (a report with 15 opportunities is 15 separate, reviewable diffs, not
one enormous one); it makes the agent state improve-vs-new explicitly so a
human skimming the diff can sanity-check the call before merging; and the
"verify with build:prerender" step exists because the whole point of the
gate is that a broken title/canonical ships silently otherwise — the gate
only protects you if something actually runs it.

---

## 4. Scheduling

**Recommended cadence: weekly, not more often.** Two reasons: Search
Console data lags 2-3 days (the report's `GSC_LAG_DAYS` already accounts for
this), and a 28-day rolling window barely moves week to week for a site
this size — running it daily would mostly reproduce last night's numbers
and burn review time re-reading a near-identical report. Weekly is also the
cadence the report's `estimatedClicksLeftOnTable` figures are meaningful at:
frequent enough to catch a page sliding, infrequent enough that a content
change has time to show up in the next report before you act again.

Suggested day/time: **Monday morning**, after the weekend traffic dip
settles into the data and before the week's writing time gets allocated
elsewhere.

**This task does not create any scheduled job.** Below is the exact command
and, if using Claude Code's own scheduler, the exact prompt — pick one and
set it up yourself.

### Option A — cron (if you run this from a machine or server you control,
e.g. the EC2 box the backend already runs on)

```cron
0 13 * * 1 cd /path/to/word-wiz-ai/frontend && GSC_SERVICE_ACCOUNT_KEY=/path/to/wordwizai-gsc-key.json GSC_SITE_URL=sc-domain:wordwizai.com node scripts/gsc-report.mjs >> /var/log/gsc-report.log 2>&1
```

(`0 13 * * 1` = Monday 13:00 UTC — adjust for your timezone. Set the two env
vars for real, don't leave the placeholder paths.)

### Option B — Claude Code's own scheduler (`/schedule`)

If you're running this inside Claude Code and want it to remind you /
run the loop automatically, the exact prompt to give the `/schedule`
skill is:

```
/schedule every Monday at 9am: cd frontend && node scripts/gsc-report.mjs,
then read growth/gsc-opportunities.md and follow growth/CONTENT_LOOP.md
to act on the top 1-2 opportunities
```

Review what it sets up before confirming — it should run in this repo's
directory and needs the same `GSC_SERVICE_ACCOUNT_KEY` / `GSC_SITE_URL`
environment available to whatever session it spawns.

### Option C — GitHub Actions

If you'd rather this run in CI than on a machine you maintain, a scheduled
workflow with a `workflow_dispatch` trigger works too — store the service
account JSON as a repo secret (`GSC_SERVICE_ACCOUNT_KEY_JSON`), write it to
a temp file at the start of the job, point `GSC_SERVICE_ACCOUNT_KEY` at
that path, run the script, then commit or upload the two output files as
an artifact. Sketch of the cron trigger: `cron: "0 13 * * 1"` (same Monday
13:00 UTC). Not built here — this repo's `.github/` isn't in scope for this
change — but it's the natural next step if the loop proves itself manually
first.

Whichever option you pick, **run it manually once before scheduling
anything**, so you know the credentials actually work and the report looks
reasonable, rather than debugging both the script and the scheduler at
once.
