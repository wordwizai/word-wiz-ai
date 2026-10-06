# Listings tracker

One row per site, ever. Check here before submitting anything. Status values:
`existing` (was already there before this tracker), `candidate` (researched,
not submitted), `queued` (draft in APPROVAL_QUEUE), `needs-bruce` (needs his
account or his name in a new way), `submitted`, `live`, `rejected`,
`excluded` (fails the rules: paid, reciprocal link, etc.).

## Already listed (found 2026-10-05)

| Site | URL | Date submitted | Status | Live listing URL | Dofollow? | Notes |
|---|---|---|---|---|---|---|
| AlternativeTo | https://alternativeto.net | 2026-01-06 (by brucebpeters12) | existing | https://alternativeto.net/software/word-wiz-ai/about/ | unknown (fetch blocked) | 1 like, 0 "alternative to" links. **Lists Word Wiz as "Open Source", but the repo has no LICENSE file.** Worth correcting. The real value is adding "alternative to" links on Starfall, Reading Eggs, Khan Academy Kids, Google Read Along, Ello. Needs Bruce's login |
| SaaSHub | https://www.saashub.com/word-wiz-ai | unknown (auto-added?) | existing, unclaimed | https://www.saashub.com/word-wiz-ai | nofollow (checked HTML) | Already #4 on SaaSHub's "Starfall alternatives" page, which ranked #1 for "Starfall alternatives". Claiming needs an account (Bruce). Ignore their paid "submit to 110 directories" tool |
| Product Hunt | https://www.producthunt.com | 2025-12-16 (launch) | existing | (find exact URL) | unknown | 1 upvote. Relaunch only for a significant iteration, and only with Bruce's approval |

## Candidates (researched 2026-10-05, nothing submitted)

Ranked by expected real users for a K-2 reading tool.

| # | Site | Submit route | Account? | Status | Dofollow? | Fit (1-5) | Notes |
|---|---|---|---|---|---|---|---|
| 1 | Freedom Homeschooling | https://freedomhomeschooling.com/submit-free-resource/ ("created" form) | No | queued (AQ-009) | yes (checked HTML) | 5 | Phonics page ranks #1 for "free phonics curriculum online homeschool". Never accepts payment. Limits AI-generated resources, so be clear about how AI is used |
| 2 | ISTE+ASCD EdTech Index | https://ltd.iste.org ("Join Now") | Yes (company profile) | needs-bruce | unknown | 5 | Free. Needs a privacy policy (have one). Curated, uses Bruce's name. Main replacement for Common Sense reviews |
| 3 | Free Homeschool Deals | https://freehomeschooldeals.com/submit | No | candidate | unknown | 4 | Needs a 150+ word third-person post and a 1000x1500 graphic. One-time email spike to a large list, not a lasting listing |
| 4 | DyslexiaHelp (U. Michigan) | dyslexiahelp@umich.edu | No | queued (AQ-008) | unknown | 4 | Email, so it's outreach. An unrelated app called "Word Wizard" is already listed there |
| 5 | Common Sense Privacy | privacy@commonsense.org | No | needs-bruce | n/a | 4 | Evaluation request by email. Public rating, so a privacy-policy review first might be worth it. Kids' data, needs Bruce |
| 6 | TeachersFirst | https://www.teachersfirst.org/contact.cfm | No | candidate | unknown | 4 | Editorial, contact form only, so it's outreach. Draft next session |
| 7 | Homeschooling with Dyslexia | contact form | No | candidate | unknown | 4 | Has an "Advertising Options" page, so features may be paid. Older draft in `growth/SUBMISSIONS.md` has unverified claims |
| 8 | ALSC Notable Children's Digital Media | ALA Airtable form | No | needs-bruce | unknown | 3 | Award-style list. Eligibility window unclear |
| 9 | Tech & Learning | editorial pitch | No | needs-bruce | n/a | 3 | Older draft in `growth/SUBMISSIONS.md` |
| 10 | EdTech Insiders GenAI map | info@edtechinsiders.org | No | candidate | n/a | 3 | Audience is founders/investors, not parents |
| 11 | Ontario Federation of Teaching Parents | website@ontariohomeschool.org | No | candidate | yes (checked HTML) | 3 | Canadian homeschool org, lists Reading Eggs and Khan Academy |
| 12 | EdTech Impact | https://edtechimpact.com/providers/ | Yes | candidate | appears yes | 2 | UK/EU schools |
| 13 | Future Tools | https://www.futuretools.io/submit-a-tool | No | candidate | internal redirect | 2 | Over 75% rejected, no reply. AI-hobbyist audience, few parents |
| 14 | Uneed | https://www.uneed.best/submit-a-tool | Yes | candidate | only at score 20+ | 1 | Maker audience |
| 15 | Launching Next | https://www.launchingnext.com/submit/ | No | candidate | unknown | 1 | Low fit |
| 16 | Microlaunch | https://microlaunch.net | Yes | candidate | unverified | 1 | Couldn't load submit page |

## Excluded (don't revisit unless the terms change)

| Site | Why |
|---|---|
| EducationalAppStore | One-time submission fee (their own Aug 2025 guide) |
| There's An AI For That | $49+ only |
| TopAI.tools | Paid tiers only on its submit page |
| Futurepedia, Toolify | Paid ($247+, $99) |
| BetaList | "All submissions now require payment" |
| Dang.ai | Free tier needs a backlink to them (link exchange) |
| Fazier | Free tier needs their badge on our site (unverified, treat as excluded) |
| 1EdTech TrustEd Apps | Paid membership |
| Peerlist | Paid ID verification or work email; developer audience |
| OpenAlternative, OER Commons | Need an open license |
| Cathy Duffy Reviews | Doesn't review standalone apps |
| TheHomeSchoolMom, Homeschool Hub Utah | Local in-person listings only |
| Slant, ALA Great Websites, Student Privacy Pledge, EdTools.io, TechMatrix | Read-only, retired, or dead |
| Common Sense Education reviews | Paused Feb 2026 |

## Listing copy (checked against the code on 2026-10-05)

Never say "no account needed" until AQ-003 is answered. Never quote a user or
visitor count that isn't in `STATE.md` with a date.

**Tagline, 52 chars**
A free reading tutor that listens to your child read

**Short description, ~240 chars**
Word Wiz AI is a free reading tutor for kids in about K-2. Your child reads a
sentence out loud, it shows which sounds they got wrong, and it writes the
next sentence around those sounds. It runs in a browser, so there's nothing to
install.

**Long description, ~600 chars**
Word Wiz AI is a free, browser-based reading tutor for early readers (roughly
kindergarten to 2nd grade). A child reads a sentence out loud and Word Wiz
checks it sound by sound, so instead of just marking a word wrong it can tell
you the "sh" in "ship" came out as an "s". Then it writes the next practice
sentence around the sounds the child missed. There are three modes -
unlimited practice, a story mode, and a choose-your-own-adventure mode. It
works best with a decent microphone, since a muffled mic makes the analysis
less accurate. Built by a high school student, 2nd place in the Congressional
App Challenge (CA-15).

**Categories**: Education, Early literacy, Reading, Phonics, AI tutor
**Pricing**: Free
**Platform**: Web browser (desktop, tablet, Chromebook)
