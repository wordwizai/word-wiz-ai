# Growth agent state

Last session: 2026-10-06 (session 2). Next session: read this,
`APPROVAL_QUEUE.md`, the last 5 entries of `RUN_LOG.md`, and `LISTINGS.md`.

**Bruce, 2026-10-06: "you aren't a coding agent, you are an advertising
agent."** Default to outreach, listings, posts and on-page SEO. Product or
backend work only when it directly blocks getting users, and keep it short.

## Setup notes for the next session

- **Full instructions:** `growth-agent/AGENT_PROMPT.md` (original prompt + Bruce's amendments).
- **Bruce's manual to-do list:** https://claude.ai/artifact/4RsbovZ7BiNaubUbpJ4qiT
  (posting checklist with copy-ready text). When new approved items need his
  hands, add them there (or tell him to).
- **Cloud sessions** have none of Bruce's local access: no Search Console or
  Vercel logins (built-in browser), no prod DB, no `.env.deploy`/SSH key, no
  Reddit. Write "n/a (cloud session)" for metrics you can't read, never
  estimates, and spend the session on research, drafts for the queue, and
  on-page SEO verified with `npm run build`. Push `growth-agent` only.

- Branch `growth-agent` (pushed to origin). Bruce wants finished work merged
  into `dev` and no worktree left behind. Pattern that works: add a worktree
  **outside the repo folder** (session 2 used the scratchpad), do the work,
  `git merge --no-ff growth-agent` into `dev` from the main checkout, push
  `growth-agent`, then `git worktree remove`. A worktree inside the repo
  gets its `node_modules` locked by VS Code's Tailwind extension and can't be
  deleted.
- Bruce merges `dev` into `main` himself; `main` auto-deploys the frontend.
  The backend deploys separately (`scripts/deploy-backend.sh`).
- Verify with `cd frontend && npm run build` (prerender gate on every route).
  `npm run typecheck` has 11 pre-existing errors; only check touched files.
- No preview deploys for this branch (AQ-002 rejected). No `gh` CLI, and
  GitHub isn't signed in to the built-in browser.
- **Search Console**: built-in browser (Bruce's Google sign-in). All-metrics URL:
  `https://search.google.com/search-console/performance/search-analytics?resource_id=sc-domain%3Awordwizai.com&num_of_days=28&metrics=CLICKS%2CIMPRESSIONS%2CCTR%2CPOSITION`
  plus `&compare_date=PREV`, `&breakdown=page`, `&page=!<urlencoded url>`.
  Extract table rows with `javascript_tool`.
- **Vercel analytics**: Bruce is signed in to Vercel in the built-in browser.
  The public API/MCP returns "Web Analytics not found"; use the dashboard's
  endpoint from the analytics page:
  `/api/web-analytics/v2/stats?environment=production&from=...&to=...&tz=America%2FLos_Angeles&projectId=word-wiz-ai&teamId=team_VRw4lcYxVcgCW9P6UHugvhZV&limit=50&type=<path|referrer|event_name|country|...>&filter=<json>`
  Event filter: `{"event_name":{"values":["signup_button_click"],"operator":"eq"}}`.
- **Signups**: AQ-001 approved a read-only aggregate query per session (see
  `data/2026-10-06-vercel-and-signups.md` for the exact queries; `users` has
  no timestamp, so count by first session). Run with the main venv in a
  `SET SESSION TRANSACTION READ ONLY` connection, counts only.
- Reddit is blocked in the built-in browser and WebFetch. Bruce posts there.
- Gmail connector = brucebpeters12@gmail.com. Bruce wants
  **contactwordwizai@gmail.com** on all outreach, so emails go out from that
  account by Bruce (or connect it). Forms: use contactwordwizai@gmail.com.
- Daily GSC indexing routine: `C:\Users\bruce\.claude\scheduled-tasks\gsc-request-indexing\`.
  Session 2 moved the silent-e guide and ABCmouse comparison to the front
  of its queue (quota was used up).

## Metrics history

| Read date | GSC clicks (28d) | Impr (28d) | CTR | Pos | Indexed / not | Visitors (30d) | Signup-click visitors (30d) | New users (30d, by first session) | Users with a scored reading (30d) |
|---|---|---|---|---|---|---|---|---|---|
| 2026-10-05 | 306 (prev 314) | 22.8K (prev 29.6K) | 1.3% | 7.4 | 45 / 130 | n/a | n/a | n/a | n/a |
| 2026-10-06 | (same window) | | | | 45 / 130 | 774 | 65 | 39 | 20 |

Other 2026-10-06 reads: GSC shows 15 invalid merchant listings, 15 product
snippets and 15 review snippets, all from the fake schema removed in
session 1 (live 2026-10-06). Target 0 as Google recrawls. Total accounts
252. Full detail: `data/2026-10-05-gsc.md`, `data/2026-10-06-vercel-and-signups.md`.

## The funnel (2026-10-06, last 30 days)

774 visitors -> 65 clicked a signup button -> ~39 started a first session
-> 20 got a reading scored. Google sends 339 visitors, mostly to guides, but
guides produced ~9 signup-click visitors in total; the homepage converts
~35% of its visitors to a click. ChatGPT referrals: 14 visitors, 8 clicked.

## Live vs waiting

| Change | Commit | Status | Check after |
|---|---|---|---|
| Fake ratings/Product schema removed (8 comparison pages) | 0e536d5 | **Live 2026-10-06** | GSC merchant/review snippets -> 0 by ~Oct 20 |
| ABCmouse vs HoP retitle | 996eb56 | **Live 2026-10-06** | Page CTR (baseline 0.2%/90d) ~Nov 1 |
| Stale years removed (11 pages) | bb5399c | **Live 2026-10-06** | Small; check with the rest |
| Silent-e guide retitle | a3fe0f3 | **Live 2026-10-06** | CTR on "silent e words" (0.1% at pos 8) ~Nov 1 |
| Silent-e guide +20 sentences | 04c34e3 | **Live 2026-10-06** | Pos for "magic e sentences" (6.2) ~Nov 1 |
| About page founder section | 9c84b9a | In dev, not main | |
| Privacy line for the try page (AQ-011) | 4c0c2c8 | In dev, not main | |
| Robust quality gates (AQ-012, Bruce set the env) | n/a | **Live 2026-10-06**, confirmed `Metrics mode: robust` | Users with a scored reading (baseline 20/40) |
| 4 magic-e practice pages | 895cbdd | In dev, not main | Indexing; "magic e words" pos 17.2 |
| Guest route + try page + guide CTAs | 47c92d1, e4a6965, 46a50ce | **Backend live 2026-10-06** (9583b5d, verified in prod). Frontend in dev, waiting on dev -> main | `try_link_click` / `try_attempt` / `try_completed` events; signup clicks per guide visit |
| Digital-silence fix | 50e1a11 | **Live 2026-10-06** (backend) | Users with a scored reading (baseline 20/40) |

## What's working

- Rankings: almost every guide/article is at position 5-9 for its main
  queries. The problem was CTR and conversion, not rankings.
- The homepage converts. Guides don't (yet).

## What isn't working

- Guides convert almost nobody (fix shipped to dev: try page CTAs).
- Half of new users never get a reading scored. Two leads found: the
  digital-silence failure (fixed in dev) and legacy quality gates (AQ-012).
- 110+ practice-words pages still "Discovered - not indexed".

## Backlog (advertising first)

1. **Once the try page is live** (dev -> main): submit AQ-018 and AQ-019 contact forms; remind Bruce to post AQ-013/AQ-014 (a day apart) and send AQ-017/AQ-020 from contactwordwizai@gmail.com. HN and LinkedIn were rejected.
   Then one follow-up wave of 4-6 more listicle authors from research
   (spellingjoy, learningreadinghub, mmguardian have no clear contact route;
   skip comment-section link drops).
2. **AlternativeTo + SaaSHub** (Bruce's logins): add "alternative to" links
   for Starfall, Reading Eggs, Khan Academy Kids, Google Read Along, Ello;
   claim SaaSHub. Fix "Open Source" label.
3. **Product Hunt relaunch** around the try page (last launch Dec 16, 2025,
   1 upvote). Needs screenshots/video and Bruce.
4. **Free Homeschool Deals** feature (needs a 150-word third-person blurb
   and a 1000x1500 graphic) and **ISTE EdTech Index** (Bruce's account).
5. **Homepage title** around "reading app that listens to your child read"
   (research: product pages win those queries). Careful, homepage CTR is 5.6%.
6. **Comparisons vs apps that listen** (Read Along, Reading Coach, Ello,
   Readability) and "free alternatives to X" pages.
7. b/d article title + "is it normal or dyslexia?" section.
8. Long-vowel guide CTR (1,708 impr/28d, 0.6%).
9. Comparison pages are dead ends (no related links); HoP page shows Word
   Wiz twice; competitor prices unverified.
10. Bylines "Word Wiz AI Editorial Team" -> "Word Wiz AI".

## Next actions (session 3)

1. Merge `origin/main`, read the queue, execute APPROVED items.
2. Backend is deployed (verified). Check the frontend: https://wordwizai.com/try/at-family
   should show the try intro, not the homepage. If live, send AQ-018/AQ-019.
3. Re-read Vercel: `try_link_click`, `try_attempt`, `try_completed`,
   `signup_button_click` by page. Re-read GSC for the session-1 pages.
4. Check contactwordwizai@gmail.com replies are being handled (Bruce) and
   whether Freedom Homeschooling confirmed (AQ-009).
