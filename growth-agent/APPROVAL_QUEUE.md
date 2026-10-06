# Approval queue

To approve, change `Status: PENDING` to `Status: APPROVED` (or `REJECTED` plus a
reason), or say so in a session. Nothing here happens until it says APPROVED.
Rejected items move to the bottom and are not proposed again.

Format: `ID | Type | Where | Why (expected impact) | Risk | Status`

---

## AQ-001 | Access | Vercel Web Analytics + signup counts | Without these I can't tell whether search clicks turn into users, which is the actual score | None | Status: PENDING

What I found on 2026-10-05:

- The Vercel analytics API returns `404 Web Analytics not found` for project
  `word-wiz-ai`. The tracking script itself does load on the live site
  (`/_vercel/insights/script.js` returns 200), so either Web Analytics isn't
  enabled at the project level (in which case `signup_button_click` events
  are going nowhere), or the API just can't read it on this plan. I can't
  tell which from here.
- Signups live in the RDS database. I haven't queried it, since it holds kids'
  data and the prod database is off-limits without your OK.

What I'm asking for (any one of these helps):

1. Open the project's Analytics tab in Vercel. If it offers "Enable", turn it
   on (free on Hobby). If it already shows data, tell me, and either sign in
   to Vercel once in the Claude desktop app's built-in browser (I won't enter
   credentials myself) or paste me the last 30 days of visitors, top pages
   and `signup_button_click` counts.
2. For signups, either (a) OK me running one read-only count query per
   session, `SELECT DATE(created_at), COUNT(*) FROM users WHERE created_at >= '2026-07-01' GROUP BY 1`,
   which returns counts only and no personal fields, or (b) paste me the
   count yourself each session.

---

## AQ-002 | Config | `vercel.json` + `frontend/vercel.json` | Gives the `growth-agent` branch its own preview deploy, so I can check changes on Vercel before you merge | Low. Only adds builds for one branch; Vercel marks preview URLs noindex. Production is unaffected | Status: PENDING

The prompt assumes pushing `growth-agent` gives a preview, but both files set
`"**": false`, so no branch except `main` builds. I tried to add the exception
and my permission classifier blocked it as a change to shared deploy config,
so it's yours to apply (or tell me it's OK and add a permission rule).

The exact change, in both files:

```diff
   "git": {
     "deploymentEnabled": {
       "main": true,
+      "growth-agent": true,
       "**": false
     }
   },
```

If you apply it, the "No other branch deploys" line in `CLAUDE.md` might be
worth updating too. Until then I verify every change with a local
`npm run build` (the same prerender gate Vercel runs).

---

## AQ-003 | Decision | Product facts | Listings and outreach need a true answer to "do you need an account?" | None | Status: PENDING

The facts you gave me say "No account needed to start." The code on `main`
says otherwise. `/practice` and `/practice/:sessionId` are wrapped in
`ProtectedRoute`, which sends anyone without a token to `/login`, and every
CTA on the site goes to `/signup`. There is no guest or demo route.

The site copy doesn't claim "no account", so nothing public is wrong. But
`growth/LISTING_KIT.md` and the drafts in `growth/SUBMISSIONS.md` do ("Practice
works without signing up", "doesn't need an account to try"), and so would
any listing I write from your facts.

Until you answer, every listing and email says "free" and never "no account".
Which is true?

- (a) An account is required right now (I'll keep the wording as is), or
- (b) there's a no-account path I'm missing (tell me where), or
- (c) you want one (see AQ-004).

---

## AQ-004 | Product change | Guest "try one sentence" mode | Likely the biggest conversion lever on the site. A parent on the silent-e guide has to create an account before hearing a single piece of feedback | Medium. Touches auth, unauthenticated audio from children, and the privacy policy | Status: PENDING

Proposal only. I won't build any of this without an APPROVED here.

- New public route `/try` (and later `/try/:pattern`, e.g. `/try/magic-e`).
- The child reads up to 3 fixed sentences for that pattern, gets the normal
  sound-level feedback, then sees "Save progress and keep going - sign up
  free".
- No session, no feedback history, nothing written to the database. Audio is
  analyzed and dropped, the same as now minus storage.
- Rate-limited per IP on the backend so it can't be used as a free ASR API.
- Content CTAs ("Practice these words out loud") would point to the matching
  `/try/:pattern` instead of `/signup`.

Open questions for you before this goes anywhere:

1. Are you OK with unauthenticated audio from children hitting the backend?
   The privacy policy might need a line about it (COPPA-sensitive).
2. Can the EC2 box take anonymous load? `CLAUDE.md` says memory is the
   binding limit.
3. Would you rather do the cheap version first, which is fixing the
   post-signup redirect so a parent who signs up from the silent-e guide
   lands in practice instead of the dashboard? That also touches auth code,
   so it needs a yes too.

How I'd measure it: signup-button clicks per 100 guide visits, before vs
after (needs AQ-001).

---

## AQ-005 | Site copy (uses your name) | `/about` | The About page never says who built Word Wiz. A real founder line is a trust signal for parents and for Google's quality raters, and it's the one fact no competitor can copy | Low. Uses your name in a new public place | Status: PENDING

Right now `/about` is generic mission text with no person behind it. Proposed
new section, placed above "Connect With Us":

> **Who built this**
>
> I'm Bruce Peters, a high school student in the Bay Area, and I built Word
> Wiz AI on my own. Most reading apps tell a kid that a word was wrong. I
> wanted something that could hear which sound inside the word was off, the
> way a tutor sitting next to them would. Word Wiz placed 2nd in the
> Congressional App Challenge for California's 15th district. It's free, and
> if something isn't working for your child, I'd honestly like to hear about
> it through the contact page.

---

## AQ-006 | Email | Phonics.org contact form (https://phonics.org/contact/) | Their guide "Best AI Reading Tutors for Kids" ranks for "ai reading tutor for kids", one of the few queries where we already convert (4.9% CTR at pos 5). Being listed on it puts Word Wiz in front of parents who are already shopping for exactly this | Low | Status: PENDING

Page: https://phonics.org/best-ai-reading-tutors-for-kids-a-parent-and-teacher-guide/

> Subject: A free AI reading tutor for your guide
>
> Dear Phonics.org team,
>
> I read your guide to AI reading tutors for kids while looking at what's out
> there for parents, and I wanted to suggest one more. I built Word Wiz AI, a
> free reading tutor that runs in a browser.
>
> A child reads a sentence out loud and it shows which sounds inside each word
> were off (like "ship" coming out as "sip"), then it writes the next sentence
> around those sounds. It's made for roughly K-2, and it works best with a
> decent microphone.
>
> If you think it fits the guide, I'd really appreciate you taking a look at
> wordwizai.com. I'm a high school student and built it on my own, so any
> feedback helps too.
>
> Best,
> Bruce Peters
> 2nd Place, Congressional App Challenge (CA-15)

---

## AQ-007 | Email | Freddy the Frog Caster contact form (https://freddythefrogcaster.com/contact-us/) | Dr. Leah Bennett's "Best Reading Apps for Kids: Free and Paid Options" ranks for "reading app that listens to child read" and already lists apps that listen (Ello, Readability). Word Wiz would be the free one | Low | Status: PENDING

Page: https://freddythefrogcaster.com/best-reading-apps-for-kids-free-and-paid-options/

> Subject: A free reading app that listens to kids read
>
> Dear Dr. Bennett,
>
> I came across your list of free and paid reading apps for kids and wanted to
> suggest one for the free side. I built Word Wiz AI, a reading tutor that
> listens to a child read out loud and points out the exact sounds they
> missed, instead of just marking the whole word wrong.
>
> It's free, runs in a browser, and is aimed at kids in about K-2. Although
> it does a lot of what Ello and Readability do, the part I focused on is the
> sound-level feedback, since that's what a parent can't easily hear on their
> own.
>
> You can try it at wordwizai.com. I'd really appreciate any feedback, even if
> it doesn't end up on the list.
>
> Best,
> Bruce Peters

---

## AQ-008 | Email | University of Michigan Dyslexia Help (dyslexiahelp@umich.edu) | Their apps directory ranks for "dyslexia reading practice app". It's a university site with short blurbs per app, so a listing is a real, relevant link and a steady trickle of the families most likely to need sound-level feedback | Low. The email is careful not to claim Word Wiz is built for or tested with dyslexia | Status: PENDING

Page: https://dyslexiahelp.umich.edu/tools/apps/

> Subject: Suggestion for your apps list
>
> Dear Dyslexia Help team,
>
> I wanted to suggest an app for your apps list. Word Wiz AI is a free,
> browser-based reading tutor where a child reads a sentence out loud and it
> shows which individual sounds were wrong (for example, /b/ read as /d/),
> then gives them a new sentence built around those sounds.
>
> It isn't designed specifically for dyslexia and it hasn't been formally
> studied, so I understand if it doesn't fit. Although most reading apps
> only mark a whole word right or wrong, a kid who mixes up b and d usually
> gets the rest of the word right, so I thought the sound-level feedback
> might be useful for the families you work with.
>
> It's at wordwizai.com, and I'm happy to answer any questions about how it
> works.
>
> Best,
> Bruce Peters

---

## AQ-009 | Directory listing | Freedom Homeschooling, "Submit a Resource You CREATED" form (https://freedomhomeschooling.com/submit-free-resource/) | Its phonics page ranks #1 for "free phonics curriculum online homeschool", it links with a normal (dofollow) link, and homeschool parents of K-2 kids are exactly who Word Wiz is for | Low. Free, no account, never accepts payment. They may decline because they limit AI resources | Status: PENDING

Needs your OK because the form takes your name and email and has two
agreement checkboxes (their terms and a "read the FAQ" box). If approved, I
fill it in exactly like this and submit once:

| Field | Answer |
|---|---|
| Your Name | Bruce Peters |
| Email | brucebpeters12@gmail.com (or tell me another) |
| Name of Business or Organization | Word Wiz AI |
| Title of the Free Resource | Word Wiz AI - free reading tutor that listens to your child read |
| Link | https://wordwizai.com |
| Grade levels | Kindergarten, 1st Grade, 2nd Grade |
| This free resource is | Secular or neutral |
| Did you use AI tools in creating this resource? | The AI-assisted option (AI is part of how the tool works) |

**Please describe the free resource**

> Word Wiz AI is a free reading tutor for kids in kindergarten through 2nd
> grade. Your child reads a sentence out loud and it checks their reading
> sound by sound, so instead of just marking a word wrong it can tell you the
> "sh" in "ship" came out as an "s". Then it writes the next sentence around
> the sounds they missed. There's an unlimited practice mode, a story mode and
> a choose-your-own-adventure mode. It runs in a browser and needs a free
> account (Google or email). It works best with a decent microphone. There
> are no ads and nothing to buy.

**If you selected either AI option, please describe how AI was used**

> AI is part of how the tool works. A speech recognition model turns the
> child's reading into individual sounds, and a language model writes the
> feedback and the next practice sentence. I designed and built the app
> myself, including the part that lines up what the child said with what the
> sentence should sound like and decides which sounds were wrong.

If AQ-003 comes back "no account needed", I'll drop the account sentence
before submitting.

---

## AQ-010 | Access | GitHub PR for `growth-agent` | Nothing goes live until the PR exists and you merge it. I pushed the branch but couldn't open the PR | None | Status: PENDING

`gh` isn't installed on this machine, and the built-in browser isn't signed
in to GitHub (I won't sign in for you or pull a token out of git's
credential store).

1. **Now, one click:** open
   https://github.com/wordwizai/word-wiz-ai/compare/main...growth-agent?expand=1,
   title it "Growth agent: SEO fixes and state (running PR)", and paste the
   contents of `growth-agent/PR_BODY.md` as the description.
2. **So I can keep it updated myself (optional):** `winget install GitHub.cli`
   then `gh auth login`. After that I'll edit the PR description each session
   instead of asking you to.

---

## Notes for Bruce (not approval items)

- **AlternativeTo lists Word Wiz as "Open Source"**, but the repo has no
  LICENSE file. It might be worth fixing that field when you're logged in.
  While you're there, adding Word Wiz as an alternative to Starfall, Reading
  Eggs, Khan Academy Kids, Google Read Along and Ello is what actually puts it
  in front of people (it has 0 "alternative to" links now).
- **SaaSHub already lists Word Wiz** (unclaimed) and shows it as #4 on its
  Starfall alternatives page, which ranks #1 for "Starfall alternatives".
  Claiming it takes an account, which I can't create for you, but it's a few
  minutes and lets you fix the description.
- `growth/SUBMISSIONS.md` lists AlternativeTo and Product Hunt as not
  started, but both already exist (Product Hunt launched Dec 16, 2025). It
  also lists EducationalAppStore, which now charges a submission fee.

- `growth/SUBMISSIONS.md` has older drafts (Homeschooling with Dyslexia, The
  Edvocate, Tech & Learning, local press) that say "has a few hundred users"
  and "doesn't need an account to try". Neither is verified (see AQ-001,
  AQ-003). It might be worth not sending those as written. I haven't
  re-proposed them here.
- Notion isn't connected in this session (it needs authorizing in your
  claude.ai connector settings), so there are no Notion tasks for these items.

---

## Rejected

(none yet)
