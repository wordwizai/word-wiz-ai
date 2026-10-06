# Vercel analytics + signup counts, read 2026-10-06

## Vercel Web Analytics (production, last 30 days: 2026-09-06 to 2026-10-06)

Source: the project's Analytics tab and its internal endpoint
`/api/web-analytics/v2/stats`, read in the built-in browser with Bruce's
Vercel login (AQ-001 approved). The public API / MCP still returns "Web
Analytics not found", so use the dashboard route. Filter syntax that works:
`filter={"event_name":{"values":["signup_button_click"],"operator":"eq"}}`.

| Metric | Value |
|---|---|
| Visitors | 774 (0% vs prior 30d) |
| Page views | 1,585 (+21%) |
| Bounce rate | 80% (-5%) |
| `signup_button_click` | 109 clicks from 65 visitors |

Top pages by visitors: `/` 158, silent-e guide 77, `/dashboard` 72, blend
article 69, decodable sentences 52, `/login` 52, CVC guide 46, `/signup` 45,
`/oauth-callback` 41.

Referrers by visitors: google.com 339, accounts.google.com 44 (OAuth
round-trips), chatgpt.com 14, bing.com 9, vercel.com 4, duckduckgo.com 3.

Countries: US 35%, **Singapore 20%** (worth a look, may be bots or a
hosting/proxy artifact), UK 4%, Philippines 3%, Canada 3%.
Devices: desktop 63%, mobile 35%, tablet 2%.

### Where signup clicks happen (event filtered, by page)

| Page | Clicks | Visitors who clicked |
|---|---|---|
| `/` | 73 | 55 |
| `/signup` | 26 | 23 |
| `/guides/silent-e-words-practice-for-kids` | 3 | 3 |
| `/guides/short-vowel-sounds-exercises-beginning-readers` | 2 | 2 |
| `/guides/how-to-teach-cvc-words-to-struggling-readers` | 2 | 1 |
| `/about` | 1 | 1 |
| `/guides/long-vowel-sounds-practice-first-grade` | 1 | 1 |
| `/guides/r-controlled-vowels-teaching-strategies-parents` | 1 | 1 |

All content pages together: about 9 visitors clicked a signup button. The
silent-e guide had 77 visitors and 3 clickers (~4%). The homepage had 158
visitors and 55 clickers (~35%).

Signup clicks by referrer: google.com 26 visitors, chatgpt.com 8 (of 14
visitors from ChatGPT), bing.com 3, tiktok.com 1, github.com 1.

## Signups (production DB, read-only aggregate counts)

AQ-001 approved a read-only count query. `users` has no created timestamp,
so new users are counted by each user's first practice session. Run inside
`SET SESSION TRANSACTION READ ONLY`; no personal fields selected.

| Measure | Value |
|---|---|
| Total accounts | 252 (max id 253). Includes test user 252 from a 2026-10-05 UX session |
| Accounts that never started a session | 38 |
| Users whose first session was in Aug 2026 | 22 |
| ... Sep 2026 | 38 |
| ... Oct 1-5, 2026 | 9 |
| New users (first session) since 2026-09-06 | 39 |
| Active users (any session) since 2026-09-06 | 40, with 95 sessions |
| Users who submitted at least one reading attempt since 2026-09-06 | **20**, with 157 attempts |

Earlier months by first session: Jul 2025 2, Aug 2025 6, Sep 2025 2, Nov
2025 4, Dec 2025 4, Jan 2026 20, Feb 29, Mar 21, Apr 16, May 15, Jun 13, Jul 13.

Caveat: sessions include a few from UX testing on 2026-10-05 (test user 252,
sessions 1050-1054).

## The funnel, last 30 days

774 visitors -> 65 clicked a signup button -> ~39 started a first session
-> **20 actually read a sentence aloud**. Guides bring the search traffic but
almost never produce a signup click, and half of the people who start a
session never record an attempt.
