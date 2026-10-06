# Growth agent state

Last session: 2026-10-05 (session 1). Next session: start by reading this,
`APPROVAL_QUEUE.md`, the last 5 entries of `RUN_LOG.md`, and `LISTINGS.md`.

## Setup notes for the next session

- The branch lives in a worktree at `.claude/worktrees/growth-agent`. The
  main checkout at `C:\Users\bruce\Coding\word-wiz-ai` stays on `dev`; don't
  switch it.
- Start of session: `git fetch origin && git merge origin/main` inside the
  worktree (merge, not rebase, because the branch is pushed and shared with
  the PR).
- Verify changes with `cd frontend && npm run build`. It prerenders every
  route and fails on bad titles/canonicals. `node_modules` is installed in the
  worktree. `npm run typecheck` has 16 errors on `main` already; only check
  that the files you touched add none.
- No Vercel preview for this branch until AQ-002 is applied.
- No `gh` CLI and GitHub isn't signed in to the built-in browser, so the PR
  can't be opened or edited from here (AQ-010). Keep `growth-agent/PR_BODY.md`
  current every session; it's the PR description.
- Pushing `growth-agent` works (`git push origin growth-agent`, never `main`,
  never force).
- Search Console is readable through the built-in browser (persistent Google
  sign-in). Performance URL with all metrics:
  `https://search.google.com/search-console/performance/search-analytics?resource_id=sc-domain%3Awordwizai.com&num_of_days=28&metrics=CLICKS%2CIMPRESSIONS%2CCTR%2CPOSITION`
  Add `&compare_date=PREV` for the period comparison and `&breakdown=page`
  for pages. Add `&page=!<urlencoded url>` to filter one page. All table rows
  are in the DOM, so extract with `javascript_tool` instead of paging.
- A separate daily scheduled task (`gsc-request-indexing`) requests indexing
  for up to 10 URLs a day. Its log is at
  `C:\Users\bruce\.claude\scheduled-tasks\gsc-request-indexing\log.md`. Don't
  duplicate it.

## Metrics history

Search Console numbers are 28-day windows ending about 2 days before the read
date. "n/a" = not readable (see AQ-001).

| Read date | GSC clicks (28d) | Impressions (28d) | CTR | Avg pos | Indexed / not | Visitors (Vercel) | Signups |
|---|---|---|---|---|---|---|---|
| 2026-10-05 | 306 (prev 314) | 22.8K (prev 29.6K) | 1.3% | 7.4 | 45 / 130 | n/a | n/a |

90-day totals on 2026-10-05: 972 clicks, 83.9K impressions, 1.2% CTR, pos 8.2.
Full snapshot: `data/2026-10-05-gsc.md`.

## What's live vs waiting

Nothing from this branch is live yet. Everything below is waiting on the PR.

| Change | Commit | Live? | Check after |
|---|---|---|---|
| Removed made-up ratings / Product schema from 8 comparison pages | 0e536d5 | No | GSC Enhancements -> Merchant listings drops to 0 invalid, ~2 weeks after merge |
| ABCmouse vs Hooked on Phonics title/description/H1 | 996eb56 | No | CTR on that page (baseline 90d 0.2%, 28d 0% on 813 impr). Judge 3-4 weeks after merge |
| Silent-e guide title/description | a3fe0f3 | No | CTR for "silent e words" (baseline 0.1% at pos 8.0) and the page (28d 0.9%) |
| Silent-e guide +20 vowel-sorted sentences | 04c34e3 | No | Position for "magic e sentences" (6.2), "silent e sentences" (4.6), "magic e words sentences" (6.0) |
| Removed stale 2024/2025 from 11 pages' titles | bb5399c | No | Small pages. Look at CTR on consonant blends (28d 0% on 178 impr) and Reading Eggs vs Starfall |

## What's working (evidence so far)

- Content pages rank. Almost every guide/article sits at position 5-9 for its
  main queries. The problem is CTR (most pages are 0.5-2%), not rankings.
- Position improved across the board in the last 28 days (9.1 -> 7.4) while
  impressions fell 23%. Likely seasonal back-to-school demand fading, plus
  fewer low-position impressions; not something we changed.
- The "can't blend sounds" article is the one clear grower (clicks 23 -> 51,
  pos 8.8 -> 6.2).

## What isn't working

- Comparison pages get impressions and almost no clicks (ABCmouse vs HoP: 813
  impressions, 0 clicks in 28d). The SERP for these is crowded with 8+
  dedicated comparison pages (see research below).
- 110 practice-words pages are "Discovered - currently not indexed". Internal
  links went live with commit ccff4e1 (merged to main 2026-10-05). Give it
  until ~Nov 2 before judging.
- No way to see conversion at all (AQ-001).

## Backlog (ranked by expected users per hour)

1. **Magic e practice pages** (`a_e`, `i_e`, `o_e`, `u_e` in
   `frontend/src/data/phonicsPatterns.ts`). The silent-e cluster is the site's
   biggest (18.8K impressions/90d), the silent-e guide's practice card
   currently links CVC families because no magic-e patterns exist, and
   "magic e words" sits at pos 17.2. Each page needs a real word list,
   decodable sentences, teaching notes and common mistakes, same as the
   existing pattern pages.
2. **"Reading app that listens to your child read" landing angle.** Research
   shows those queries are won by product pages whose title nearly matches
   the query (GoReadling's homepage title is that phrase). The homepage title
   is "Free AI Reading Tutor for Kids | Learn Phonics & Pronunciation" (76
   chars). It might be worth testing a homepage title/H1 built around "listens
   to your child read". Homepage CTR is already 5.6%, so do this carefully
   and alone.
3. **Comparisons against apps that actually listen**: Word Wiz vs Google Read
   Along, vs Microsoft Reading Coach, vs Ello, vs Readability; "free
   alternatives to Ello/Readability". Research found almost no competing
   pages for these. Honest difference is sound-level feedback for K-2 (free +
   browser is shared with Read Along web and Reading Coach). Check every
   competitor fact on their own site and date it.
4. **b/d article**: rework title around "b vs d / b and d difference for kids"
   and add an "is it normal or dyslexia?" section (every ranking page answers
   that). 28d: 1,822 impressions, 0.7% CTR, pos 6.5. Many impressions are
   Indonesian ("bayangan cermin dari huruf b") and can't be served.
5. **Long vowel guide CTR** (28d 1,708 impressions, 0.6%, pos 8.0). Look at
   its query mix first.
6. **Comparison pages are dead ends**: no related links, no practice card
   (ComparisonPageTemplate). Add related links into guides.
7. **Hooked on Phonics vs Word Wiz page bug**: `product2` is Word Wiz and
   `const wordWiz = product2`, so tables show Word Wiz twice. Visible content
   bug; the template needs a 2-product mode.
8. **Competitor prices on comparison pages are unverified** (e.g. ABCmouse
   $14.99/mo, HoP $19.99/mo). Neither vendor's homepage shows a price.
   Verify on pricing pages or remove.
9. **Bylines**: 15 pages credit "Word Wiz AI Editorial Team", and dead `bio`
   strings call it "expert educators". Not rendered, but it might be worth
   changing the byline to "Word Wiz AI" and deleting the bios.
10. **Printable PDFs** for the silent-e and decodable-sentences guides
    (research: these SERPs are won by printables). Bigger job.
11. Titles over 60 chars on 27/44 pages and descriptions over 160 on 21. Fix
    opportunistically when a page is touched for another reason, not as a
    mass edit.
12. Brand query "wordwizai.com" averages position 18.8 (66 impr/90d). Odd for
    an exact-domain query. Inspect in GSC.
13. Missing BreadcrumbList schema although every page shows breadcrumbs.
14. `/login` and `/signup` have no title/canonical and are crawlable.

## Research on file (2026-10-05)

- Real competitors that listen to a child read: Google Read Along (free,
  Android + web), Microsoft Reading Coach (free, web; closest analogue),
  Ello (free tier + paid, apps), Readability ($19.99/mo), Amira (schools),
  Fonetti, Bookbot, Reading Racer. None clearly claims phoneme-level
  diagnosis on its own site.
- "abcmouse vs hooked on phonics" SERP: ABCmouse's own comparison page plus
  8 or so third-party comparison pages.
- Phonics content SERPs ("silent e words", "magic e sentences", "decodable
  sentences") are won by printables (Reading Universe PDFs, TpT, Wonster
  Words, Pinterest).
- Listicle candidates for outreach: see AQ-006/007/008 and the full list in
  `RUN_LOG.md` session 1.

## Next actions (session 2)

1. Merge `origin/main`, read the queue, execute anything APPROVED. Check
   whether the PR exists (AQ-010) and whether it was merged.
2. Re-read GSC 28d totals and the five pages above. Expect no movement yet if
   the PR isn't merged; say so at the top of the report.
3. Build the four magic-e practice pages (backlog #1).
4. If AQ-009 is APPROVED, submit Freedom Homeschooling and log it in
   LISTINGS.md. Draft TeachersFirst outreach (LISTINGS #6) for the queue.
