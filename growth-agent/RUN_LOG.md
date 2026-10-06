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

**Queued for Bruce**: AQ-001 to AQ-010 (analytics access, preview deploys,
account-fact conflict, guest mode, About page founder line, 3 outreach
emails, Freedom Homeschooling listing, opening the PR).

**Listings**: none submitted. Found 3 existing listings (AlternativeTo,
SaaSHub, Product Hunt) and researched 16 candidates plus an excluded list;
all in `LISTINGS.md`. The best free fit (Freedom Homeschooling) needs
Bruce's name, email and two agreement boxes, so it's AQ-009. The rest need
his account, are outreach, or are low-fit AI/startup directories, which I
skipped on purpose (listing count isn't the goal).

**Blocked**: editing `vercel.json` to enable branch previews was denied by my
permission classifier. Moved to AQ-002 with the exact diff.

**Pushed** `growth-agent` to origin (7 commits). **Couldn't open the PR**:
no `gh` CLI, and GitHub isn't signed in to the built-in browser. The PR
description is in `PR_BODY.md`; AQ-010 asks Bruce to open it.

**Check next session**: whether the PR was merged. If it was, nothing will
have moved yet (Google needs 2-4 weeks), so just confirm the pages re-crawled
via URL Inspection and move on to backlog #1.

---

## 2026-10-06 - Session 2

**Bruce's answers to the queue**: AQ-001 approved (signed in to Vercel),
AQ-002 rejected, AQ-003 resolved (an account IS required), AQ-004 approved
(build guest mode), AQ-005 approved with a BU-research addition, AQ-006 to
AQ-009 approved, AQ-010 no answer. Mid-session: "use contactwordwizai@gmail.com
for any emails sent out" and "you aren't a coding agent, you are an
advertising agent". Both saved to memory.

**Found**: Bruce merged dev (with session 1) into main on Oct 5, 11:20pm PT,
so session 1's SEO changes went live 2026-10-06. `verify:live` passed; live
pages have the new titles and no Product/AggregateRating markup.

**Measured** (`data/2026-10-06-vercel-and-signups.md`): 774 visitors / 30d,
339 from Google, 65 signup-click visitors (55 from the homepage, ~9 from all
guides combined), 39 new users, 20 with a scored reading.

**Outreach sent** (all approved):
- AQ-008 email to U. Michigan Dyslexia Help (from brucebpeters12@gmail.com)
- AQ-006 Phonics.org contact form (confirmed)
- AQ-007 Freddy the Frogcaster contact form (confirmed)
- AQ-009 Freedom Homeschooling: Bruce ticked the reCAPTCHA, I submitted.
  Unconfirmed (503s from their server, no confirmation shown).
The first three went out with the personal address before Bruce's
contactwordwizai instruction.

**Shipped to dev** (all on `growth-agent`, merged into dev):
- `9c84b9a` About page "Who built this" section (AQ-005)
- `895cbdd` four magic-e practice pages + silent-e guide practice card
- `47c92d1`, `e4a6965` public `/guest/analyze-audio` route: allowlisted
  sentences, no DB writes, no audio caching, per-IP and site-wide limits,
  2 concurrent analyses. 16 tests.
- `50e1a11` fix: recordings with digital silence failed the whole pipeline
  (NaN from noisereduce, spread by normalization). Affects signed-in users
  too. Reproduced end to end, test added.
- `46a50ce` `/try/:slug` page, guide and practice-page CTAs point to it,
  try-funnel analytics events, stale-token bounce fixed on public pages.
Verified: backend suite passes (all 18 modules), real-model end-to-end run
of the guest route (caught "made"->"mad", "cake"->"cack"), full frontend
build with prerender.

**Queued**: AQ-011 privacy line, AQ-012 production quality-gate flag
(possible activation fix), AQ-013..AQ-020 outreach batch (2 Reddit posts,
Show HN, LinkedIn, 4 emails/forms), all timed for after the try page is live.

**Blocked / notes**: GSC indexing quota was used up; moved the two key pages
to the front of the daily routine's queue instead. Reddit can't be read or
posted from here.

**Expect**: once backend + dev->main deploy, try-page events start; signup
clicks per guide visitor should rise from ~9 per 30 days. Check in session 3.

**Later in session 2 (Bruce's second round of answers)**: AQ-011 approved
(privacy line added, 4c0c2c8). AQ-012 done by Bruce (he updated the server
env; confirmed `WWAI_SOFT_QUALITY_GATES=1` in the container and "Metrics
mode: robust" on live requests). Reddit posts approved (Bruce posts). HN and
LinkedIn rejected. All contact forms and emails approved; the two emails
(KidvoKit, OFTP) are Bruce's to send from contactwordwizai@gmail.com, the
two forms (Lead in Literacy, TeachersFirst) wait for the try page.

**Deployed the backend** at Bruce's request: merged growth-agent into dev
(one conflict in prerender.mjs's excluded routes, resolved by keeping both
"/dev" and "/try"), verified merged dev (all backend tests, full frontend
build, 158 pages), pushed dev, cleared Docker build cache and unused images
on the server (1.4 GB -> 6.6 GB free), ran `scripts/deploy-backend.sh 9583b5d`.
/docs 200, ONNX loaded. In production: arbitrary sentence -> 400, guest
analysis full stream, digital-silence recording now scores. Pruned again
after the swap (6.6 GB free).

---

## 2026-10-06 - Session 3 (cloud)

Cloud session, none of Bruce's local access (no Search Console or Vercel
logins, no prod DB, no deploy key, no Reddit), so no metrics this time.

**Loaded**: merged `origin/main` into `growth-agent` (already up to date,
main at 2e9d41a). Read AGENT_PROMPT, STATE, the queue, both earlier run log
entries and LISTINGS.

**Measured**: GSC, Vercel analytics, signups all n/a (cloud session).

**Checked**: session 2's frontend is on main (2e9d41a, merged Oct 6 07:45 PT).
Rendered https://wordwizai.com/try and /try/at-family in headless Chromium.
Both show the try intro ("No account needed... doesn't save recordings from
this page"). The About page shows "Who built this".

**Approved items**: nothing for me to execute. Bruce's posting checklist page
(updated by a local session after session 2, not in the repo) shows AQ-018
(Lead in Literacy) already sent and confirmed, and AQ-019 (TeachersFirst)
filled in and waiting on his reCAPTCHA tick. Both forms have CAPTCHAs anyway.
AQ-013, AQ-014, AQ-017 and AQ-020 are Bruce's sends and can go now. Updated
the queue and LISTINGS so AQ-018 isn't resent.

**Research** (four parallel passes, nothing sent or submitted):
- Listicle authors, teacher and homeschool resource lists, dyslexia and
  literacy sites. 25+ pages checked, contact routes confirmed on the live
  sites, spot-checked 9 of them myself. Paid-placement sites excluded.
- Found that **Word Wiz is already on the ISTE EdTech Index** (approved
  Dec 14, 2025). LISTINGS had it as not submitted.
- Product Hunt's page is /products/word-wiz. A relaunch needs 6 months (met)
  and a "significant update".
- Free Homeschool Deals takes submissions by email, not a form.

**Queued** (all in Bruce's voice, contactwordwizai@gmail.com, linking
wordwizai.com/try, writing-rule check passed: no em dashes, no colons in
prose, no banned words):
- AQ-021 to AQ-030, outreach wave 2: Proud to be Primary, Simply Kinder,
  Differentiated Teaching, Learning at the Primary Pond, Let's Read San Mateo
  County, Frontier Charter School, Wisconsin Dyslexia Roadmap, Undivided,
  Worcester Education Collaborative, Contra Costa County Library.
- AQ-031 ISTE listing edit, AQ-032 Free Homeschool Deals (post text plus a
  1000x1500 graphic in `assets/`, built in the og-image style), AQ-033
  Product Hunt (ask first, then launch copy and first comment).

**SEO changes** (one hypothesis each, verified with `npm ci && npm run build`:
158 pages prerendered and validated, new titles in the built HTML):
1. `d819ec7` b/d article title and description, aimed at the "is it normal?"
   question that wins that search. *Expect:* page CTR up from 0.6% (90d) at
   pos 6.9. Check 3-4 weeks after it's live.
2. `48f77d6` long-vowel guide title and description, saying what's on the
   page (212 unique words, 8 decodable sentences, 4 games). *Expect:* page CTR
   up from 0.7% (90d) at pos 8.1. Same bet as the silent-e retitle on a
   different page. Check 3-4 weeks after it's live.
3. `d864a4c` sitemap-lastmod.json hashes (32 pages hashed differently on this
   build; lastmod dates unchanged).

**Blocked**: pushing. `git push` returned 403 ("Claude doesn't have GitHub
access to wordwizai/word-wiz-ai"), and the GitHub connector's write also
returned 403. Reads work. Sent Bruce a patch of every session 3 commit
instead. Fix: reconnect GitHub at https://claude.ai/connect-github or
install the Claude GitHub App on the org.

**Check next session**: whether the commits reached origin, which outreach
went out, and the try-funnel events since Oct 6.

**Later in session 3**: Bruce installed the Claude GitHub App on the
wordwizai org, and `git push` went through (2338d0f..6db7ead). The patch
he was sent is no longer needed. Also added `OUTREACH_IDEAS.md`, a ranked
brainstorm of 20 wave-3 ideas (4 routes checked, the rest unverified).

**Later in session 3 (wave 3, Bruce: "get started with everything... keep
researching low hanging advertising fruit")**
- Ran 8 research passes (edtech bloggers, Bay Area literacy orgs, community
  rules, Teachers Pay Teachers rules, podcasts, AASL form, freebie sites,
  library guides), checked the key routes myself, and queued AQ-034 to
  AQ-056: EdSurge pitch, AASL answers, Bay Area orgs, educator bloggers,
  podcasts, Well-Trained Mind and Reddit posts, library guides,
  Internet4Classrooms, a Facebook group post.
- Found and queued **AQ-036**: recordings go to Deepgram without its
  model-improvement opt-out, and the privacy page never mentions AI or
  deletion. Needs Bruce (kids' data, privacy policy).
- Dropped with reasons: Teachers Pay Teachers (sellers 18+, $29 fee), Free
  Technology for Teachers (Richard Byrne left edtech), Cool Cat Teacher and
  Class Tech Tips (sponsored), Raising A Reader and Reading Partners (no
  outside tools), nearly every homeschool freebie site (paid or dormant).
- Site: free two-page magic-e printable built from the silent-e guide's
  sentences, served at `/printables/magic-e-sentences.pdf` with a CTA on
  the guide and a `printable_download` event (f51d6ad). Verified with a full
  build (158 pages). *Expect:* downloads within days of going live; a
  shareable asset for AQ-032, AQ-051, AQ-056.
- Started round 2 research: city literacy coalitions, listicles about apps
  that listen, big public library systems.
