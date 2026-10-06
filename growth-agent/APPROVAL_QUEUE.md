# Approval queue

To approve, change `Status: PENDING` to `Status: APPROVED` (or `REJECTED` plus a
reason), or say so in a session. Nothing here happens until it says APPROVED.
Rejected items move to the bottom and are not proposed again.

Format: `ID | Type | Where | Why (expected impact) | Risk | Status`

---

## AQ-001 | Access | Vercel Web Analytics + signup counts | Without these I can't tell whether search clicks turn into users, which is the actual score | None | Status: APPROVED

> **Outcome (2026-10-06):** Bruce logged in to Vercel in the built-in browser and OK'd the count query. Vercel numbers come from the dashboard's internal endpoint (the public API still 404s). `users` has no created timestamp, so signups are counted by first practice session. See `data/2026-10-06-vercel-and-signups.md`.

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

## AQ-003 | Decision | Product facts | Listings and outreach need a true answer to "do you need an account?" | None | Status: RESOLVED

> **Outcome (2026-10-06):** An account IS required to practice. Listings and copy say "needs a free account (Google or email)".

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

## AQ-004 | Product change | Guest "try one sentence" mode | Likely the biggest conversion lever on the site. A parent on the silent-e guide has to create an account before hearing a single piece of feedback | Medium. Touches auth, unauthenticated audio from children, and the privacy policy | Status: APPROVED

> **Outcome (2026-10-06):** Bruce: "yes we can make a mode that doesn't require them having an account". Being built on `growth-agent` in session 2.

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

## AQ-005 | Site copy (uses your name) | `/about` | The About page never says who built Word Wiz. A real founder line is a trust signal for parents and for Google's quality raters, and it's the one fact no competitor can copy | Low. Uses your name in a new public place | Status: APPROVED

> **Outcome (2026-10-06):** Approved with an addition: mention his AI-in-education research at Boston University and that he's working to make tools like this better for the people who matter. Shipped on `growth-agent` in session 2, written in his voice.

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

## AQ-006 | Email | Phonics.org contact form (https://phonics.org/contact/) | Their guide "Best AI Reading Tutors for Kids" ranks for "ai reading tutor for kids", one of the few queries where we already convert (4.9% CTR at pos 5). Being listed on it puts Word Wiz in front of parents who are already shopping for exactly this | Low | Status: APPROVED

> **Outcome (2026-10-06):** Sent 2026-10-06 through phonics.org's contact form (site confirmed "Your message is on its way"). Reply address was brucebpeters12@gmail.com because Bruce's "use contactwordwizai@gmail.com" instruction arrived just after.

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

## AQ-007 | Email | Freddy the Frog Caster contact form (https://freddythefrogcaster.com/contact-us/) | Dr. Leah Bennett's "Best Reading Apps for Kids: Free and Paid Options" ranks for "reading app that listens to child read" and already lists apps that listen (Ello, Readability). Word Wiz would be the free one | Low | Status: APPROVED

> **Outcome (2026-10-06):** Sent 2026-10-06 through the Freddy the Frogcaster contact form ("Your submission was successful"). Reply address brucebpeters12@gmail.com, same reason as AQ-006. The contact page has placeholder filler text, so it may not be monitored.

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

## AQ-008 | Email | University of Michigan Dyslexia Help (dyslexiahelp@umich.edu) | Their apps directory ranks for "dyslexia reading practice app". It's a university site with short blurbs per app, so a listing is a real, relevant link and a steady trickle of the families most likely to need sound-level feedback | Low. The email is careful not to claim Word Wiz is built for or tested with dyslexia | Status: APPROVED

> **Outcome (2026-10-06):** Sent 2026-10-06 by email from brucebpeters12@gmail.com (the only Gmail account connected), before the contactwordwizai@gmail.com instruction.

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

## AQ-009 | Directory listing | Freedom Homeschooling, "Submit a Resource You CREATED" form (https://freedomhomeschooling.com/submit-free-resource/) | Its phonics page ranks #1 for "free phonics curriculum online homeschool", it links with a normal (dofollow) link, and homeschool parents of K-2 kids are exactly who Word Wiz is for | Low. Free, no account, never accepts payment. They may decline because they limit AI resources | Status: APPROVED

> **Outcome (2026-10-06):** Filled 2026-10-06 with contactwordwizai@gmail.com. Bruce ticked the reCAPTCHA himself, I pressed Submit. **Unconfirmed**: one AJAX call returned `{"success":true}`, then four returned 503 "service unavailable" and no confirmation appeared. Not resubmitted (they ask for one submission per site). Check contactwordwizai@gmail.com for a confirmation; if none by next session, resubmit with Bruce's reCAPTCHA tick.

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

> **Outcome (2026-10-06):** Mostly moot: Bruce merged dev (which contains growth-agent) into main on 2026-10-05, so session 1 went live without a PR. Still true that the agent can't open or edit PRs (no gh, GitHub not signed in).

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

## How to send the outreach below

Everything from AQ-013 on is timed for **after the try page is live**
(backend deployed, then dev merged to main), because "try it without an
account" is the hook. Use **contactwordwizai@gmail.com** for every reply
address. The Gmail account connected to Claude is your personal one, so for
the emails either send them from contactwordwizai@gmail.com yourself or
connect that account and I'll send them. Approve any subset; each item
stands alone.

---

## AQ-011 | Privacy policy | `/privacy` | The try page lets kids record without an account. The policy is very general and never mentions audio, even though its meta description promises to explain how children's audio is handled | Low. It touches the privacy policy, so it's yours to OK | Status: PENDING

Proposed addition, as its own short paragraph after the first one:

> **Practicing without an account.** On wordwizai.com/try, a child can read
> a few practice sentences without creating an account. The recording is
> sent to our server, analyzed to give pronunciation feedback, and then
> discarded. Word Wiz AI doesn't save it or link it to anyone.

One thing to decide: the recording also passes through Deepgram (word
timing) on the way, the same as in signed-in practice, and the policy
doesn't name any service providers today. It might be worth a line like
"We use trusted service providers to process audio for feedback," but that
applies to the whole product, not just the try page.

---

## AQ-012 | Production config | backend `.env` on the EC2 box | Possibly the biggest activation fix available. In the last 30 days 40 users started a session but only 20 ever got a reading scored | Medium. Changes which recordings are accepted for every user | Status: PENDING

While testing guest mode I found the quality checks run in "legacy" mode
unless `WWAI_SOFT_QUALITY_GATES=1` is set, and your local `.env` doesn't
set it. In legacy mode the noise check assumes the first and last half
second of a recording are background noise. On a clean recording of
"Jake made a cake for the game" it measured 3 dB and refused it as "too
noisy". The robust mode (built in the recent audio-robustness work) measured
the same file at 60 dB and scored it normally.

I can't see the production environment. Two steps, both yours:

1. On the server, `grep WWAI_SOFT_QUALITY_GATES backend/.env`.
2. If it's not set, add `WWAI_SOFT_QUALITY_GATES=1` and redeploy the
   backend. Refused recordings never become feedback entries, so the
   effect would show up as more users with at least one scored attempt
   (baseline 20 of 40 in the last 30 days).

---

## AQ-013 | Reddit post | r/homeschool (or r/Homeschooling) | Homeschool parents teaching K-2 phonics are exactly the audience, and a post with a no-account link gets tried on the spot | Medium. Self-promotion rules vary; read the sidebar first and message the mods if promotion needs approval. Post from your own account, say you built it, answer replies | Status: PENDING

Send after: the try page is live.

**Title:** I built a free tool that listens to your kid read and points out the exact sounds they missed. Would love feedback from homeschool parents

> Hi everyone, I'm a high school student and I built Word Wiz AI on my own.
>
> A lot of reading apps only tell a kid whether the whole word was right. I
> wanted something closer to what a tutor does, which is hear that the "sh"
> in "ship" came out as an "s" and then practice that sound next.
>
> So Word Wiz has your kid read a sentence out loud, shows which sounds were
> off, and writes the next sentence around those sounds. It's free, there are
> no ads, and it runs in a browser. You can try three sentences without
> making an account at wordwizai.com/try
>
> Two honest caveats. It works best with a decent mic (a muffled laptop mic
> makes it less accurate), and it's built for roughly K-2.
>
> I'd really appreciate hearing what works and what doesn't, especially from
> parents teaching phonics at home.

---

## AQ-014 | Reddit post | r/dyslexia | Parents here talk about b/d mix-ups and skipped sounds constantly, which is what sound-level feedback catches | Medium-high. Sensitive community. The post says plainly it isn't a dyslexia treatment and hasn't been studied. Check the rules first | Status: PENDING

Send after: the try page is live. Post a day or more apart from AQ-013.

**Title:** I built a free tool that shows which sounds in a word a kid misread. Not a dyslexia treatment, but I'd love honest feedback

> Hi all, I'm a high school student and I built Word Wiz AI, a free reading
> tool for early readers. A kid reads a sentence out loud and it shows which
> individual sounds were off (like /b/ read as /d/, or "cake" read as
> "cack"), then gives them a new sentence built around those sounds.
>
> To be upfront, it isn't designed specifically for dyslexia and it hasn't
> been formally studied, so I'm not claiming it treats anything. Although
> it's built for general K-2 phonics practice, b/d mix-ups and skipped
> sounds come up a lot here, so I wanted to ask whether the sound-level
> feedback would actually help your kids or if it misses the point.
>
> You can try three sentences without an account at wordwizai.com/try. It
> works best with a decent mic. Any feedback, good or bad, helps a lot.

---

## AQ-015 | Show HN | news.ycombinator.com | HN likes a technical build story from a student, and a no-signup demo is close to a requirement there. Mostly developers, but many are parents, and a front-page run brings links and press | Medium. One shot per project; post on a weekday morning US time and stay around to answer | Status: PENDING

Send after: the try page is live AND the backend deploy with the silence fix
(the post mentions it).

**Title:** Show HN: Phoneme-level reading feedback for kids learning to read

**URL:** https://wordwizai.com/try

**Text:**

> Hi HN, I'm a high school student, and Word Wiz AI is a reading tutor I
> built for kids learning to read (roughly K-2).
>
> Most reading apps score whole words. Word Wiz scores sounds. The child
> reads a sentence, a wav2vec2 model fine-tuned on TIMIT to output IPA
> phonemes (running on ONNX Runtime) transcribes what they actually said,
> and a dynamic-programming alignment matches those phonemes against the
> expected pronunciation word by word. Each word gets a phoneme error rate,
> and the feedback names the specific sound, like the /eɪ/ in "cake" coming
> out as /æ/. The next practice sentence is generated around the sounds the
> child missed.
>
> The hard parts have been kids' voices (TIMIT is adult speech), cheap laptop
> and Chromebook mics, and recordings that start with digital silence, which
> were failing the whole pipeline until this week.
>
> You can try three sentences without an account at the link. I'd love
> feedback on the approach, especially from anyone who has worked on
> children's speech recognition.

---

## AQ-016 | LinkedIn post | your LinkedIn | Your network includes teachers, BU people and CAC contacts, and one share from a teacher reaches a classroom of parents | Low | Status: PENDING

Send after: the try page is live.

> Word Wiz AI now has a page where any kid can try it without making an
> account.
>
> When I looked at the analytics this week the pattern was pretty clear.
> Parents find Word Wiz through our phonics guides, but almost none of them
> signed up from there, because you had to make an account before hearing a
> single piece of feedback. Now you can open wordwizai.com/try, have your
> child read three sentences, and see exactly which sounds they missed.
>
> I'm also doing research on AI in education at Boston University, and a
> tool like this only matters if it actually reaches kids. If you know a
> parent, teacher or tutor working with an early reader, I'd really
> appreciate you sending this their way.

---

## AQ-017 | Email | KidvoKit, Karen Gage (info@kidvokit.com) | Her dyslexia-apps guide ranks for "dyslexia reading practice app" and has a "🚧 new or promising, still being studied" badge, which is the honest category for Word Wiz | Low | Status: PENDING

Send after: the try page is live. From contactwordwizai@gmail.com.

**Subject:** A free tool for your "new or promising" list

> Dear Karen,
>
> I came across your guide to dyslexia apps and liked that you mark each
> tool by how much evidence is behind it. I built a free reading tutor called
> Word Wiz AI, and I think it honestly belongs in your "new or promising, but
> still being studied" group rather than the evidence-based one.
>
> A child reads a sentence out loud and it shows which individual sounds
> were off (for example, /b/ read as /d/), then gives them a new sentence
> built around those sounds. It's free, runs in a browser, and you can try a
> few sentences without an account at wordwizai.com/try.
>
> It hasn't been formally studied and it isn't designed only for dyslexia,
> so I completely understand if it doesn't fit. If you do try it, I'd really
> appreciate any feedback.
>
> Best,
> Bruce Peters
> 2nd Place, Congressional App Challenge (CA-15)

---

## AQ-018 | Contact form | Lead in Literacy, Christina / Mrs. Winter's Bliss (https://leadinliteracy.com/contact/) | Her "7 Best Phonics Apps" ranks for "free phonics app" and is built around Science of Reading practice | Low | Status: PENDING

Send after: the try page is live. Reply address contactwordwizai@gmail.com.

> Dear Christina,
>
> I read your list of the 7 best phonics apps and liked how much weight you
> put on independent practice that actually follows the Science of Reading.
> I built a free tool called Word Wiz AI that might fit that independent
> practice slot.
>
> A child reads a decodable sentence out loud and Word Wiz shows which sounds
> inside each word were off, like "cake" read as "cack," then writes the next
> sentence around those sounds. It's free, runs in a browser, and kids can
> try a few sentences without an account at wordwizai.com/try.
>
> Although it doesn't replace explicit instruction, the sound-by-sound
> feedback is the part kids usually can't get when they practice on their
> own. I'd really appreciate your take on it, even if it doesn't end up on
> the list.
>
> Best,
> Bruce Peters

---

## AQ-019 | Contact form | TeachersFirst (https://www.teachersfirst.org/contact.cfm) | Nonprofit, ad-free, 16,000+ educator-reviewed resources with weekly updates. A listing reaches K-2 teachers directly | Low | Status: PENDING

Send after: the try page is live. Reply address contactwordwizai@gmail.com.

**Subject:** Resource suggestion for K-2 phonics practice

> Dear TeachersFirst team,
>
> I wanted to suggest a free resource for K-2 reading. Word Wiz AI listens to
> a student read a sentence out loud and shows which sounds were
> mispronounced, so a teacher can see that "ship" came out as "sip" instead
> of just that the word was wrong. It runs in a browser, it's free with no
> ads, and students can try a few sentences without an account at
> wordwizai.com/try.
>
> I'm a high school student and built it on my own. It works best with a
> decent microphone, which I know can be a problem on some school devices.
> I'd really appreciate it if your reviewers took a look.
>
> Best,
> Bruce Peters

---

## AQ-020 | Email | Ontario Federation of Teaching Parents (website@ontariohomeschool.org) | Their online resources page lists Reading Eggs under Language Arts and they accept suggestions without charging. Canadian homeschool families | Low | Status: PENDING

Send after: the try page is live. From contactwordwizai@gmail.com.

**Subject:** Suggestion for your Language Arts resources

> Dear OFTP team,
>
> I wanted to suggest a free resource for the Language Arts section of your
> online resources page. Word Wiz AI is a reading tutor for early readers
> (roughly K-2) where a child reads a sentence out loud and it shows which
> sounds they got wrong, then gives them a new sentence built around those
> sounds.
>
> It's free with no ads and runs in a browser, so there's nothing to
> install. Families can try a few sentences without an account at
> wordwizai.com/try. I'm a high school student and built it on my own, so I'd
> also be grateful for any feedback from families who use it.
>
> Best,
> Bruce Peters

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

## AQ-002 | Config | `vercel.json` + `frontend/vercel.json` | Gives the `growth-agent` branch its own preview deploy, so I can check changes on Vercel before you merge | Low. Only adds builds for one branch; Vercel marks preview URLs noindex. Production is unaffected | Status: REJECTED

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

> **Rejected 2026-10-06.** Bruce: "don't do that". No preview deploys for growth-agent; keep verifying with a local `npm run build`. Don't re-propose.
