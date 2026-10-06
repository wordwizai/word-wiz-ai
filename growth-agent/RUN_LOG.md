# Run log

Newest at the bottom. Each entry: what I did, commits, what metric should
move, and when to check it.

---

## 2026-10-05 - Session 1 (first run)

**Setup**
- Created branch `growth-agent` from `origin/main` (81f2bf9) in a worktree at
  `.claude/worktrees/growth-agent`, so the main checkout stays on `dev`.
- Created `growth-agent/` (STATE, APPROVAL_QUEUE, RUN_LOG, LISTINGS, data/).
  Confirmed it isn't built or served: Vercel's root is `frontend/`, Vite's
  publicDir is `frontend/public`, `tsconfig` only includes `src`.
- Production is current: the latest Vercel production deploy is `main`
  81f2bf9, built today.

**Measured** (full detail in `data/2026-10-05-gsc.md`)
- GSC 28d: 306 clicks (prev 314), 22.8K impressions (prev 29.6K), CTR 1.3%,
  avg pos 7.4 (prev 9.1).
- Indexing: 45 indexed, 130 not (110 practice-words pages "Discovered").
- Vercel Web Analytics: the API returns "Web Analytics not found", although
  the tracking script loads on the live site. Signups: not readable. Both in
  AQ-001.

**Audit findings that drove this session**
- 8 comparison pages emitted `Product` + `Offer` + `AggregateRating`
  JSON-LD with invented numbers, including Word Wiz AI "4.8 from 2,500
  reviews" (and "250" on three pages). Word Wiz has no review system. This is
  the "review stars with no real reviews" case in Google's spam policies, and
  it's also why GSC shows "Merchant listings: 2 invalid items". `@type:
  "ComparisonPage"` isn't a schema.org type either.
- Word Wiz pricing data said "Premium features available". There is no paid
  tier. Not rendered, but removed.
- 13 titles still said 2024 or 2025.
- Practice requires an account (ProtectedRoute), which conflicts with the
  "no account needed" product fact. AQ-003.
- Comparison pages are dead ends, the Hooked on Phonics page shows Word Wiz
  twice, and no magic-e practice pages exist. Backlog.

**Changes** (all on `growth-agent`, verified with a full `npm run build`)

1. `0e536d5` - Comparison schema. The template now builds an `Article`
   JSON-LD from the page's own headline, description and URL, with the three
   products as `about` entries. Removed the `rating`/`reviewCount` fields and
   every per-page `structuredData` block from the 8 pages.
   *Expect:* Merchant listings invalid items -> 0 within ~2 weeks of merge.
   No CTR change expected (the stars were never shown as rich results).
   *Why it matters:* removes a manual-action risk sitting on 8 indexed pages.
2. `996eb56` - ABCmouse vs Hooked on Phonics: title, description and H1
   rewritten for the query people type ("abc mouse vs hooked on phonics",
   ~1,500 impr/90d across variants at pos ~8). Dropped "vs Word Wiz AI" and
   "(2025)" from the title.
   *Expect:* page CTR from 0.2% (90d) toward 1%+. Check 3-4 weeks after merge.
3. `bb5399c` - Removed stale years from 11 pages' titles/H1s (comparisons,
   consonant blends, phonics at home, choosing an app, pronounces words wrong). Left
   the CVC guide alone because its CTR is rising (1.3% -> 2.4%).
   *Expect:* small CTR lift on consonant blends (28d 0% on 178 impr) and
   Reading Eggs vs Starfall. Low confidence, low stakes.
4. `a3fe0f3` - Silent-e guide title and description now say what searchers
   want (word lists and sentences): "Silent E Words: 100+ Magic E Words and
   Sentences for Kids". Both numbers are counted from the page (103 unique
   words, 28 sentences).
   *Expect:* CTR on "silent e words" from 0.1% at pos 8 and page CTR from
   0.9% (28d). Biggest single bet this session, since the page has 18.8K
   impressions/90d.
5. `04c34e3` - Silent-e guide: added 20 decodable sentences sorted by vowel
   (a_e, i_e, o_e, u_e) with their own anchors, inside the existing
   `#sentence-reading` section. Fixed "can/kane" -> "can/cane".
   *Expect:* positions for "magic e sentences" (6.2), "magic e words
   sentences" (6.0), "silent e sentences" (4.6).

Commits 4 and 5 touch the same page. They test different things (snippet CTR
vs ranking for sentence queries), measured on different queries.

**Queued for Bruce**: AQ-001 to AQ-009 (analytics access, preview deploys,
account-fact conflict, guest mode, About page founder line, 3 outreach
emails, Freedom Homeschooling listing).

**Listings**: none submitted. Found 3 existing listings (AlternativeTo,
SaaSHub, Product Hunt) and researched 16 candidates plus an excluded list;
all in `LISTINGS.md`. The best free fit (Freedom Homeschooling) needs
Bruce's name, email and two agreement boxes, so it's AQ-009. The rest need
his account, are outreach, or are low-fit AI/startup directories, which I
skipped on purpose (listing count isn't the goal).

**Blocked**: editing `vercel.json` to enable branch previews was denied by my
permission classifier. Moved to AQ-002 with the exact diff.

**Check next session**: whether the PR was merged. If it was, nothing will
have moved yet (Google needs 2-4 weeks), so just confirm the pages re-crawled
via URL Inspection and move on to backlog #1.
