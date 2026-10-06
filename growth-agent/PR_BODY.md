<!-- Title: Growth agent: SEO fixes and state (running PR) -->
<!-- Open at: https://github.com/wordwizai/word-wiz-ai/compare/main...growth-agent?expand=1 and paste everything below. The agent keeps this file current each session. -->

Running PR for the growth agent. Merging it is the approval to put these changes live. It stays open and gets updated each session; anything already merged drops off the list below.

## Ready to merge (session 1, 2026-10-05)

Each commit is one change with one thing to measure. All verified with a full `npm run build` (prerender + title/canonical validation on all 154 routes passed).

| Commit | Change | What should move | Baseline (GSC) |
|---|---|---|---|
| `0e536d5` | **Removes invented review ratings** from 8 comparison pages. They emitted `Product` + `Offer` + `AggregateRating` JSON-LD with made-up numbers, including Word Wiz AI at "4.8 from 2,500 reviews". That's the "review stars with no real reviews" case in Google's spam policies, and it's what GSC reports as "Merchant listings: 2 invalid items". The template now builds a plain `Article`. | Merchant listing errors go to 0. Mostly this removes a manual-action risk. | 2 invalid items |
| `996eb56` | ABCmouse vs Hooked on Phonics: title, description and H1 now match the query (dropped "vs Word Wiz AI" and "(2025)" from the title). | Page CTR | 0.2% CTR on 2,648 impr / 90d, pos 7.5 |
| `bb5399c` | Removes stale 2024/2025 from 11 pages' titles. CVC guide left alone since its CTR is rising. | Small CTR lift | e.g. consonant blends 0% on 178 impr / 28d |
| `a3fe0f3` | Silent-e guide (biggest page, 18.8K impr / 90d) retitled around what searchers want: "Silent E Words: 100+ Magic E Words and Sentences for Kids". Counts are taken from the page. | CTR for "silent e words" | 0.1% CTR at pos 8.0 |
| `04c34e3` | Silent-e guide: +20 decodable sentences sorted by vowel (a_e, i_e, o_e, u_e) with anchors; fixes "can/kane". | Position for "magic e sentences" etc. | pos 6.2 / 4.6 / 6.0 |

Also in this PR, not part of the site build:
- `growth-agent/`: the agent's state, run log, listings tracker and approval queue. It sits at the repo root, outside Vercel's `frontend/` root directory, so it isn't built or served.
- `growth/LISTING_KIT.md`: flags the "no account needed" claims as unresolved, since the code requires sign-in before practice.

## Waiting on you

See `growth-agent/APPROVAL_QUEUE.md`. Highlights:
- **AQ-003**: the product facts say "no account needed", the code requires one. Which is true?
- **AQ-001**: Vercel analytics can't be read through the API, and signups need your OK to read. Without these there's no way to tell if clicks become users.
- **AQ-002**: one-line `vercel.json` change to give this branch preview deploys (blocked for me).
- AQ-004 to AQ-009: guest "try it" mode proposal, About page founder line, 3 outreach emails, one directory listing (Freedom Homeschooling).
- AQ-010: the agent can't open or update this PR itself (no `gh`, and GitHub isn't signed in to the built-in browser).

🤖 Generated with [Claude Code](https://claude.com/claude-code)
