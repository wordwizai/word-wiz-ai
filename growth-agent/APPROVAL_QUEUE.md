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

## AQ-010 | Access | GitHub PR for `growth-agent` | Nothing goes live until the PR exists and you merge it. I pushed the branch but couldn't open the PR | None | Status: CLOSED

> **Outcome (2026-10-06):** Moot. Bruce ships by merging growth-agent into dev and dev into main.

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
account" is the hook. **It is live as of 2026-10-06** (checked in session 3:
/try and /try/at-family render the try page), so all of them can go now. Use **contactwordwizai@gmail.com** for every reply
address. The Gmail account connected to Claude is your personal one, so for
the emails either send them from contactwordwizai@gmail.com yourself or
connect that account and I'll send them. Approve any subset; each item
stands alone.

---

## AQ-011 | Privacy policy | `/privacy` | The try page lets kids record without an account. The policy is very general and never mentions audio, even though its meta description promises to explain how children's audio is handled | Low. It touches the privacy policy, so it's yours to OK | Status: APPROVED

> **Outcome (2026-10-06):** Approved as written. Added to /privacy on growth-agent (goes live with the next dev -> main merge).

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

## AQ-012 | Production config | backend `.env` on the EC2 box | Possibly the biggest activation fix available. In the last 30 days 40 users started a session but only 20 ever got a reading scored | Medium. Changes which recordings are accepted for every user | Status: DONE BY BRUCE

> **Outcome (2026-10-06):** Bruce: "I updated the env file". Confirm on the next deploy (quality report should say "Metrics mode: robust").

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

## AQ-013 | Reddit post | r/homeschool (or r/Homeschooling) | Homeschool parents teaching K-2 phonics are exactly the audience, and a post with a no-account link gets tried on the spot | Medium. Self-promotion rules vary; read the sidebar first and message the mods if promotion needs approval. Post from your own account, say you built it, answer replies | Status: APPROVED

> **Outcome (2026-10-06):** Bruce posts it himself (Reddit is blocked here), after the try page is live.

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

## AQ-014 | Reddit post | r/dyslexia | Parents here talk about b/d mix-ups and skipped sounds constantly, which is what sound-level feedback catches | Medium-high. Sensitive community. The post says plainly it isn't a dyslexia treatment and hasn't been studied. Check the rules first | Status: APPROVED

> **Outcome (2026-10-06):** Bruce posts it himself, after the try page is live, a day apart from AQ-013.

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

## AQ-017 | Email | KidvoKit, Karen Gage (info@kidvokit.com) | Her dyslexia-apps guide ranks for "dyslexia reading practice app" and has a "🚧 new or promising, still being studied" badge, which is the honest category for Word Wiz | Low | Status: APPROVED

> **Outcome (2026-10-06):** Bruce sends it himself from contactwordwizai@gmail.com (that account isn't connected here).

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

## AQ-018 | Contact form | Lead in Literacy, Christina / Mrs. Winter's Bliss (https://leadinliteracy.com/contact/) | Her "7 Best Phonics Apps" ranks for "free phonics app" and is built around Science of Reading practice | Low | Status: APPROVED

> **Outcome (2026-10-06):** Agent submits the contact form once the try page is live.

> **Sent 2026-10-06, form confirmed.** Recorded on Bruce's posting checklist ("Lead in Literacy contact form (confirmed)") by a local session after session 2. **Don't resend.**

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

## AQ-019 | Contact form | TeachersFirst (https://www.teachersfirst.org/contact.cfm) | Nonprofit, ad-free, 16,000+ educator-reviewed resources with weekly updates. A listing reaches K-2 teachers directly | Low | Status: APPROVED

> **Outcome (2026-10-06):** Agent submits the contact form once the try page is live.

> **Filled in, waiting on Bruce (2026-10-06).** Per Bruce's posting checklist, a local session filled the form in his built-in browser and it's waiting on the reCAPTCHA tick. If that tab is gone, paste the copy below at teachersfirst.org/contact.cfm (email contactwordwizai@gmail.com).

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

## AQ-020 | Email | Ontario Federation of Teaching Parents (website@ontariohomeschool.org) | Their online resources page lists Reading Eggs under Language Arts and they accept suggestions without charging. Canadian homeschool families | Low | Status: APPROVED

> **Outcome (2026-10-06):** Bruce sends it himself from contactwordwizai@gmail.com.

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

## Wave 2 outreach (session 3, 2026-10-06)

Ten more, from three research passes (listicle authors, teacher and homeschool
resource lists, dyslexia and literacy sites). Every contact route was checked
on the live site on 2026-10-06, and every note is built from what's actually
on that page. All link to wordwizai.com/try and use contactwordwizai@gmail.com.
Ranked roughly by expected reach. Send any subset; each stands alone.

What each one needs from you once approved:

| ID | Who | How it goes out |
|---|---|---|
| AQ-021 | Proud to be Primary | You email it |
| AQ-022 | Simply Kinder | You email it |
| AQ-023 | Differentiated Teaching | I can submit (no CAPTCHA) |
| AQ-024 | Learning at the Primary Pond | You email it |
| AQ-025 | Let's Read San Mateo County | I can submit (no CAPTCHA), or you email it |
| AQ-026 | Frontier Charter School | You email it |
| AQ-027 | Wisconsin Dyslexia Roadmap | You email it |
| AQ-028 | Undivided | You email it |
| AQ-029 | Worcester Education Collaborative | You email it |
| AQ-030 | Contra Costa County Library | You submit (reCAPTCHA) |

---

## AQ-021 | Email | Proud to be Primary, Elyse Rycroft (proudtobeprimary@gmail.com) | "Online Reading for Kids: Best Programs and Apps" is a K-3 list of about 39 tools, modified 2026-09-08 per its page metadata, written by a Vancouver primary teacher. It already lists free web programs (Reading Bear, Progressive Phonics), and nothing on it listens to a child read | Low. Her post has affiliate links, so a free tool earns her nothing. Expect a no-reply | Status: PENDING

Verified 2026-10-06: the address is the "Email Me" link on https://proudtobeprimary.com/contact/ and on the article. The site's contact form uses invisible reCAPTCHA, so email is the cleaner route.
Page: https://proudtobeprimary.com/online-reading-for-kids/

Send from contactwordwizai@gmail.com.

**Subject:** A free phonics tool for your online reading list

> Dear Elyse,
>
> I came across your list of online reading programs and apps and wanted to
> suggest one for the "Online Phonics Programs and Apps" section. I built Word
> Wiz AI, a free reading tutor where a child reads a sentence out loud and it
> shows which sounds were off (like "ship" read as "sip"), then writes the next
> sentence around those sounds.
>
> Although your list already has a lot of great phonics practice, I didn't see
> one that listens to the child read, which is the part I focused on. It runs
> in a browser with no ads, and kids can try three sentences without an
> account at wordwizai.com/try. It works best with a decent microphone.
>
> I'm a high school student and built it on my own, so I'd really appreciate
> any feedback, even if it doesn't end up on the list.
>
> Best,
> Bruce Peters

---

## AQ-022 | Email | Simply Kinder (hello@SimplyKinder.com) | "The Best Free Kindergarten Apps For Reading" is a free-only list built from questions in the Simply Kinder Teacher Facebook Group, and it says "if you come across an app that you love for your classroom, please share it." Ranked #1 in our research search for "best reading apps for kindergarten teacher blog free" | Low. The post was last modified in 2022, so it may not be actively updated | Status: PENDING

Verified 2026-10-06: hello@SimplyKinder.com is the general address on https://www.simplykinder.com/contact/. Jennifer@ on the same page is for brand partnerships, so don't use it.
Page: https://www.simplykinder.com/kindergarten-apps-for-reading/

Send from contactwordwizai@gmail.com.

**Subject:** An app to share for your kindergarten reading apps list

> Dear Simply Kinder team,
>
> Your post on free kindergarten apps for reading says you're adding apps as
> you see them, so I wanted to share one. I built Word Wiz AI, a free reading
> tutor where a child reads a sentence out loud and it shows which sounds they
> missed, then gives them a new sentence built around those sounds.
>
> Since the post reminds teachers to read the privacy policy before
> downloading anything, I'll mention that part up front. Kids can try three
> sentences at wordwizai.com/try without an account, and recordings from that
> page aren't saved. Regular practice needs a free account, and the policy is
> at wordwizai.com/privacy.
>
> It's free with no ads and runs in a browser, so there's nothing to download
> (it works best with a decent mic). I'm a high school student and built it on
> my own, so feedback from kindergarten teachers would honestly help a lot.
>
> Best,
> Bruce Peters

---

## AQ-023 | Contact form | Differentiated Teaching, Rebecca Davies (https://www.differentiatedteaching.com/contact-rebecca/) | Former teacher and instructional coach, now homeschooling. Her "20 Best Free Reading Websites for Kids" (updated May 2, 2026) ends with "if you know any other great resources, send them my way!!" and is all books and read-alouds, nothing that listens to a child read. Her "Best Free Reading Intervention Programs" (updated June 3, 2026) is free-only and lists Lalilo for K-2. Readers are teachers and homeschool parents. All three research passes found her | Low. She leans on "research-based", so the note says plainly Word Wiz hasn't been studied | Status: PENDING

Verified 2026-10-06: the form has Name, Email, Role, Message Topic and Message, with no CAPTCHA. Use Role "Other", Topic "I have a product or blog post request.", Email contactwordwizai@gmail.com. Once approved I can submit it from any session.
Pages: https://www.differentiatedteaching.com/free-reading-websites-for-kids/ and https://www.differentiatedteaching.com/10-websites-for-reading-intervention/

> Dear Rebecca,
>
> Your post on the 20 best free reading websites for kids says to send more
> resources your way, so I wanted to share one I built. Word Wiz AI is a free
> reading tutor where a child reads a sentence out loud and it shows which
> sounds inside each word were off (like "cake" read as "cack"), then writes
> the next sentence around those sounds.
>
> Although most of the list is books and read-alouds, I didn't see anything
> that listens to the child read and gives feedback, which is the part Word
> Wiz does. It might also fit next to Lalilo on your free intervention list
> for the K-2 kids. To be upfront, it hasn't been formally studied. It's free
> with no ads, and kids can try three sentences without an account at
> wordwizai.com/try.
>
> I'm a high school student and built it on my own, so I'd really appreciate
> your take on it as a former teacher, even if it doesn't make either list.
>
> Best,
> Bruce Peters

---

## AQ-024 | Email | Learning at the Primary Pond, Alison (alison@learningattheprimarypond.com) | A literacy specialist with a large K-2 teacher audience. "Free Websites for Teachers (K-2)" ranked #1 in our research search for "free reading websites for kids teacher list K-2" and lists Epic, Starfall, ReadWorks and Storyline Online | Low. The post is from Feb 14, 2021 and covers teacher tools in general, so it may not be updated | Status: PENDING

Verified 2026-10-06: the address is a mailto link on the article. She sells courses and memberships; I saw no paid placements on this post.
Page: https://learningattheprimarypond.com/blog/free-websites-for-teachers-k-2/

Send from contactwordwizai@gmail.com.

**Subject:** A free K-2 reading site for your teacher list

> Dear Alison,
>
> I came across your post on free websites for K-2 teachers and wanted to
> suggest one for the reading side of it. I built Word Wiz AI, a free reading
> tutor where a student reads a sentence out loud and it shows which sounds
> were off (like "ship" read as "sip"), then writes the next sentence around
> those sounds.
>
> Your post starts with how little time teachers have to check out new sites,
> so the quickest way to see it is wordwizai.com/try, where a student can
> read three sentences without an account. It runs in a browser with no ads.
> It works best with a decent mic, which I know can be hit or miss on school
> laptops.
>
> I'm a high school student and built it on my own, so feedback from a
> literacy specialist would honestly mean a lot.
>
> Best,
> Bruce Peters

---

## AQ-025 | Contact form | Let's Read San Mateo County, The Big Lift (https://letsreadsmc.org/lets-read-san-mateo-county/) | A county-wide K-3 literacy site led by the County of San Mateo, San Mateo County Libraries and the County Office of Education, with K, 1st and 2nd grade pages and a phonics page (Starfall, ABCya). It asks "Have ideas for ways to improve...?" Word Wiz's CAC placing is for CA-15, so the local angle is real | Low. A research-minded county project may not add an unstudied tool | Status: PENDING

Verified 2026-10-06: the About page has a form (Name, Email, Message, and a mailing-list checkbox to leave unticked) with no CAPTCHA, and bigliftsanmateocounty@gmail.com in the footer. Once approved I can submit the form with contactwordwizai@gmail.com, or you can email it.
Pages: https://letsreadsmc.org/phonics/

If you live in San Mateo County, it might be worth saying so in the first line. I left it as "Bay Area" because I can't confirm it.

> Dear Let's Read San Mateo County team,
>
> I'm a high school student in the Bay Area, and I wanted to suggest a free
> tool for your phonics page. I built Word Wiz AI, a reading tutor where a
> child reads a sentence out loud and it shows which sounds they got wrong
> (like "ship" read as "sip"), then writes the next sentence around those
> sounds. It placed 2nd in the Congressional App Challenge for California's
> 15th district.
>
> It's free with no ads and runs in a browser, so families can use it at home
> on a laptop or Chromebook. Kids can try three sentences without an account
> at wordwizai.com/try. It's built for roughly K-2, which lines up with your
> grade pages, and it works best with a decent microphone.
>
> Although it hasn't been formally studied, I'd really appreciate it if your
> team took a look, and I'm happy to answer any questions.
>
> Best,
> Bruce Peters
> contactwordwizai@gmail.com

---

## AQ-026 | Email | Frontier Charter School, Anchorage School District homeschool program (hook_carli@asdk12.org) | A parent-directed homeschool program whose "Curriculum & Resources" page has a Reading Instructional Support list (Freedom Homeschooling, Lexia Core5, Teach Your Monster, Reading Rockets) and says "To suggest any edits, please email us at hook_carli@asdk12.org" | Low. Small reach (one district program) | Status: PENDING

Verified 2026-10-06: the address and invitation are on the page.
Page: https://frontier.asdk12.org/curriculum-resources

Send from contactwordwizai@gmail.com.

**Subject:** Suggestion for your Reading Instructional Support list

> Dear Ms. Hook,
>
> Your Curriculum & Resources page says to email you with edits, so I wanted
> to suggest a free resource for the Reading Instructional Support section.
> Word Wiz AI is a reading tutor for early readers (roughly K-2) where a child
> reads a sentence out loud and it shows which sounds they got wrong, then
> gives them a new sentence built around those sounds.
>
> It's free with no ads and runs in a browser, so families can use it at home
> with nothing to install. It's meant as extra practice next to whatever
> phonics program a family already uses, not a full curriculum. Kids can try
> three sentences without an account at wordwizai.com/try.
>
> I'm a high school student and built it on my own, so I'd be grateful for any
> feedback from your families.
>
> Best,
> Bruce Peters

---

## AQ-027 | Email | Wisconsin Dyslexia Roadmap (widyslexiaroadmap@gmail.com) | A statewide parent guide whose Parent Resources page has a game-based apps section (Teach Your Monster to Read, Starfall, Nessy) and says "Please send feed back, suggestions, and celebrations to widyslexiaroadmap@gmail.com." | Medium. Built around structured literacy, and parents of dyslexic kids may be wary of an unstudied AI tool. The note says plainly it isn't an intervention | Status: PENDING

Verified 2026-10-06: the address and the invitation are on the page itself.
Page: https://www.widyslexiaroadmap.org/parents/parent-resources

Send from contactwordwizai@gmail.com.

**Subject:** A suggestion for your Parent Resources apps list

> Dear Wisconsin Dyslexia Roadmap team,
>
> Your Parent Resources page asks for suggestions, so I wanted to share a free
> tool for the game-based apps section. Word Wiz AI is a reading tutor where a
> child reads a sentence out loud and it shows which individual sounds were
> off (for example, /b/ read as /d/), then gives them a new sentence built
> around those sounds.
>
> I want to be clear that it isn't a dyslexia intervention and it hasn't been
> formally studied, so it wouldn't replace a tutor or structured instruction.
> Although it's built for general K-2 phonics practice, I thought the
> sound-by-sound feedback might help parents practicing at home between
> sessions. It's free, and kids can try three sentences without an account at
> wordwizai.com/try.
>
> I'm a high school student and built it on my own, so I'd honestly
> appreciate any feedback, even if it isn't a fit.
>
> Best,
> Bruce Peters

---

## AQ-028 | Email | Undivided, "Reading Curricula, Tech, Apps, and More!" by Karen Ford Cull (support@undivided.io) | Updated Aug 21, 2026. It has an "AI reading tools" section (Socrat.ai, Cubox, Read.ai, EdCafe.ai) with nothing for kids who are still learning to sound out words. Audience is California families of kids with disabilities | Medium. Sensitive audience. The note says plainly Word Wiz isn't designed for any disability and hasn't been studied | Status: PENDING

Verified 2026-10-06: support@undivided.io is on the page, next to a "Give feedback to the Undivided team" link. Undivided runs a paid membership; I saw no paid placements on this page.
Page: https://undivided.io/resources/learning-resources-reading-and-literacy-8

Send from contactwordwizai@gmail.com.

**Subject:** An early-reader tool for your AI reading tools section

> Dear Undivided team,
>
> I read Karen Ford Cull's guide to reading curricula, tech and apps and
> noticed the AI reading tools section doesn't have anything for kids who are
> still learning to sound out words. I built a free one called Word Wiz AI. A
> child reads a sentence out loud, it shows which individual sounds were off
> (for example, /b/ read as /d/), and then it writes the next sentence around
> those sounds.
>
> It isn't designed for any specific disability and it hasn't been formally
> studied, so I'm not claiming it treats anything. It's free with no ads, runs
> in a browser, and kids can try three sentences without an account at
> wordwizai.com/try. It works best with a decent microphone.
>
> I'm a high school student and built it on my own. If you think it fits, I'd
> really appreciate you taking a look.
>
> Best,
> Bruce Peters

---

## AQ-029 | Email | Worcester Education Collaborative, Raising Readers Together (worcesteredcollab@gmail.com) | A citywide literacy initiative whose family page lists "Eight vendors that offer free literacy applications" with descriptions and pricing (Starfall, PBS, Duck Duck Moose, Blending Board...). Exactly the format a free tool belongs in | Low. The page footer says 2021, so it may not be maintained | Status: PENDING

Verified 2026-10-06: worcesteredcollab@gmail.com is in the page footer. Staff emails are on https://www.wecollaborative.org/contact, but the general address is the right first step.
Page: https://www.wecollaborative.org/family-resources

Send from contactwordwizai@gmail.com.

**Subject:** A free literacy app for Raising Readers Together

> Dear Worcester Education Collaborative team,
>
> I came across the free applications list on your Raising Readers Together
> page and wanted to suggest one more for families. Word Wiz AI is a free
> reading tutor for kids in about K-2. A child reads a sentence out loud, it
> shows which sounds were off (like "cake" read as "cack"), and then it gives
> them a new sentence built around those sounds.
>
> For the pricing note on your list, it's completely free with no ads and
> nothing to buy. It runs in a browser, and families can try three sentences
> without an account at wordwizai.com/try (regular practice needs a free
> account).
>
> I'm a high school student and built it on my own, so any feedback from your
> families would honestly help.
>
> Best,
> Bruce Peters

---

## AQ-030 | Contact form (Bruce submits) | Contra Costa County Library, "Resources for New and Struggling Readers" (https://ccclib.org/contact-us/email-form/) | Updated 2026-09-24. Its "Free Online Resources with Tips for Teaching Reading" section lists Khan Academy Kids, Starfall, FCRR and Reading Rockets. A Bay Area library system, so the local-student angle is real | Low. The form is protected by reCAPTCHA, so it's yours to submit | Status: PENDING

Verified 2026-10-06: the page and section exist as described. No staff email is published. The form's comment option is "This is a comment/question about the Library", and it requires "Which library do you use?". **If you don't use a Contra Costa branch and there's no "other" option, skip this one** rather than pick a branch.
Page: https://ccclib.org/resources-for-new-and-struggling-readers/

> Dear Contra Costa County Library,
>
> I saw your Resources for New and Struggling Readers page and wanted to
> suggest a free tool for the Free Online Resources section. I'm a high school
> student in the Bay Area, and I built Word Wiz AI, a reading tutor where a
> child reads a sentence out loud and it shows which sounds they got wrong
> (like "ship" read as "sip"), then writes the next sentence around those
> sounds.
>
> It's free with no ads and runs in a browser. Families can try three
> sentences without an account at wordwizai.com/try, and regular practice
> needs a free account. It's built for roughly K-2 and works best with a
> decent microphone.
>
> I'd really appreciate it if someone on your team took a look.
>
> Best,
> Bruce Peters
> contactwordwizai@gmail.com

---

## Bigger listings (paste-ready, all need your account or your name)

These three are from the "Bigger listings" part of your checklist. Each one is
yours to submit. I've written the text so approving is a yes/no.

---

## AQ-031 | Listing update (your ISTE login) | ISTE+ASCD EdTech Index, existing Word Wiz AI listing | **Word Wiz is already listed** (ULTID P78D-8135-5C53-C4C6-98, approved Dec 14, 2025, https://edtechindex.org/product/ultid/P78D-8135-5C53-C4C6-98/). The listing is missing 2nd grade, claims every operating system including Tizen, and its description says it "supports evidence-based reading instruction", which reads as a research claim we can't back. Fixing it keeps the one curated school directory accurate and adds the try link | Low. Edits go back through ISTE review (Published / Edits Required / Excluded, by email). Free; ignore the Premium upsell | Status: PENDING

Sign in at https://ltd.iste.org/ and edit the existing product. Don't register a new one. Only change these fields.

| Field | Change to |
|---|---|
| Description (no lists, aim under 500 characters) | See below (487 characters) |
| Educational Level | Keep Transitional Kindergarten, Kindergarten, 1st Grade. **Add 2nd Grade** |
| Supported Operating Systems | Web Browser, Chrome OS, Windows, macOS. **Untick Tizen and Other.** Keep iOS, iPadOS and Android only if you've checked that recording works in mobile Safari and Chrome |
| Software Requirements | See below |
| End User(s) | Student, Teacher/Tutor, Parent |
| Plan Type | Free |
| Pricing Description | Keep "Free forever" |
| Plain Language Privacy Statement | Keep yours, and add the try-page paragraph below (the wording you approved for /privacy in AQ-011) |
| Supporting Evidence | Leave empty. Nothing to cite yet |

**Description**

> Word Wiz AI is a free, browser-based reading tutor for kindergarten through
> 2nd grade. A student reads a sentence out loud and Word Wiz checks it sound by
> sound, so instead of only marking a word wrong it shows that the "sh" in
> "ship" came out as "s". It then writes the next practice sentence around the
> sounds the student missed. Students can try three sentences without an
> account at wordwizai.com/try, and regular practice uses a free account. It
> works best with a decent microphone.

**Software Requirements**

> A web browser with microphone access and an internet connection. Works on
> laptops, desktops and Chromebooks. A decent microphone in a quiet room gives
> the most accurate feedback, since a muffled mic lowers accuracy.

**Add to the privacy statement**

> Practicing without an account. On wordwizai.com/try, a child can read a few
> practice sentences without creating an account. The recording is sent to our
> server, analyzed to give pronunciation feedback, and then discarded. Word Wiz
> AI doesn't save it or link it to anyone.

One thing to check first. Your current statement says voice input "is not
stored permanently". In the code that holds as long as `ENABLE_AUDIO_CACHE`
is not set on the server (it's off by default and the try page ignores it).
I can't see the server from a cloud session, so it might be worth a quick
`grep ENABLE_AUDIO_CACHE backend/.env` before you resubmit.

---

## AQ-032 | Freebie submission (email) | Free Homeschool Deals, contact@freehomeschooldeals.com | Chosen submissions get a post, social promotion and a spot in their e-blast to "over 30,000+ families" (their number). They post free educational apps (a free iOS app, ChantCode, ran in Sept 2026). One-time spike, not a lasting listing | Low. They may decline, and the submit page doesn't say whether an account requirement is OK, so the post is upfront about it | Status: PENDING

Rules (from https://www.freehomeschooldeals.com/submit/, read 2026-10-06): email
contact@freehomeschooldeals.com with subject "Freebie submission", the link,
a post of 150+ words in third person that isn't copied from our site, a large
graphic (preferably 1000x1500) as an attachment, and any end date. No affiliate
links. No fee is mentioned.

**Graphic**: a draft 1000x1500 PNG is at `growth-agent/assets/fhd-graphic-1000x1500.png`
(same look as the site's og-image). Swap in your own if you prefer.

Send from contactwordwizai@gmail.com.

**Subject:** Freebie submission

> Dear Free Homeschool Deals team,
>
> I'd like to submit a free reading tool for your educational apps posts. The
> link is wordwizai.com/try, the post is below, and the graphic is attached
> (1000x1500). It isn't time-sensitive.
>
> Best,
> Bruce Peters

**Post title:** Free Reading Tutor That Listens to Your Child Read (Word Wiz AI)

**Post text** (third person, 248 words)

> Word Wiz AI is a free reading tutor for kids in kindergarten through 2nd
> grade, and it does something most phonics apps don't. Instead of only
> checking whether a whole word was right, it listens to a child read a
> sentence out loud and points out the exact sound that went wrong, like the
> "sh" in "ship" coming out as "s". Then it writes the next practice sentence
> around those sounds, so practice keeps aiming at what the child actually
> needs.
>
> **What's Included**
>
> Unlimited practice sentences, a story mode, and a choose-your-own-adventure
> mode. After each sentence, Word Wiz shows which sounds came out wrong and
> says what to fix out loud.
>
> **Who It's For**
>
> Families teaching phonics at home to early readers, roughly ages 5 to 8. It
> works well as a few minutes of extra practice next to whatever phonics
> program a family already uses.
>
> **How to Use It**
>
> Families can try three sentences right away at wordwizai.com/try with no
> account, and nothing from that page is saved. To keep practicing, a parent
> creates a free account with Google or email. Word Wiz runs in a web browser
> on a computer, Chromebook or tablet, so there is nothing to install. A quiet
> room and a decent microphone give the most accurate feedback, since a
> muffled mic makes it less accurate.
>
> Word Wiz AI was built by Bruce Peters, a high school student in the Bay
> Area, and placed 2nd in the Congressional App Challenge for California's
> 15th district. There are no ads and nothing to buy.

---

## AQ-033 | Product Hunt relaunch (two steps) | producthunt.com, existing page https://www.producthunt.com/products/word-wiz (launch post /posts/word-wiz-ai, 1 point) | The first launch (Dec 16, 2025) required an account before any feedback. The try page fixes exactly that, and Product Hunt visitors click straight through to try things | Medium. Product Hunt only allows a relaunch after 6 months (met) **and** a "significant update", and says "New UIs, pricing plan changes, etc. are not considered significant." The try page plus the rebuilt app might count or might not, so step 1 asks them first, which their help page recommends | Status: PENDING

Rules (from help.producthunt.com, "Can I relaunch my product?", updated Jul 7, 2026): six months between posts for the same product, plus a significant update such as "a new mobile app or a complete product redesign with new functionality". Asking for upvotes is against the rules and can get the post dropped from the homepage, so ask friends to try it and comment instead.

**Step 1. Email hello@producthunt.com** (from contactwordwizai@gmail.com)

**Subject:** Relaunch question for Word Wiz AI

> Dear Product Hunt team,
>
> I launched Word Wiz AI on Product Hunt on December 16, 2025
> (producthunt.com/products/word-wiz), and I wanted to check whether the
> changes since then count as a significant update before I post again. Word
> Wiz is a free reading tutor that listens to a child read and shows which
> sounds they got wrong.
>
> Since the first launch I added a page where any kid can try it without an
> account (wordwizai.com/try), rebuilt the signed-in app, and added an animated
> character that listens and reacts while the child reads. Although the core
> idea is the same, the no-account page changes who can actually use it, so I
> wasn't sure which side of the line it falls on.
>
> Is a relaunch OK, and if so, should it go on the same product page?
>
> Best,
> Bruce Peters

**Step 2. If they say yes, the launch** (schedule it for 12:01am PT on a Tuesday, Wednesday or Thursday from your personal account)

| Field | Text |
|---|---|
| Name | Word Wiz AI |
| Tagline (60 max) | A free reading tutor that listens to your child read (52) |
| Description (260 max) | Word Wiz AI is a free reading tutor for kids in K-2. Your child reads a sentence out loud, it shows which sounds they got wrong (like "ship" read as "sip"), and it writes the next sentence around those sounds. Try 3 sentences with no account. (242) |
| Link | https://wordwizai.com/try |
| Topics (3 max) | Education, Kids, Artificial Intelligence |
| Pricing | Free |
| Thumbnail | Square, 240x240, the Word Wiz logo |
| Gallery (min 2, 1270x760) | 1) the try page intro, 2) a feedback screen showing a wrong sound highlighted, 3) story mode, 4) the mascot reacting. Real screenshots only |

**First comment** (post it yourself right when it goes live)

> Hi everyone, I'm Bruce, a high school student, and I built Word Wiz AI on my
> own.
>
> When I first launched here last December, you had to make an account before
> hearing a single piece of feedback, which is a lot to ask from a parent who
> just wants to see if it works. So the biggest change is wordwizai.com/try.
> Any kid can read three sentences there and see exactly which sounds came out
> wrong, with no account and nothing saved.
>
> Most reading apps only tell a kid whether a whole word was right. A tutor
> sitting next to them would hear that the "sh" in "ship" came out as an "s"
> and practice that sound next, so that's what Word Wiz tries to do. It's
> free, there are no ads, and it's built for roughly K-2.
>
> Two honest caveats. It works best with a decent mic, and it's still a
> student project, so I'd really appreciate hearing what breaks or what's
> confusing.

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
- **ISTE EdTech Index already lists Word Wiz** (approved Dec 14, 2025). LISTINGS.md
  had it as "not submitted". AQ-031 is an edit to that listing, not a new one.
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

## AQ-015 | Show HN | news.ycombinator.com | HN likes a technical build story from a student, and a no-signup demo is close to a requirement there. Mostly developers, but many are parents, and a front-page run brings links and press | Medium. One shot per project; post on a weekday morning US time and stay around to answer | Status: REJECTED

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

> **Rejected 2026-10-06.** Bruce: "don't do hacker news or linked in". Don't re-propose.

## AQ-016 | LinkedIn post | your LinkedIn | Your network includes teachers, BU people and CAC contacts, and one share from a teacher reaches a classroom of parents | Low | Status: REJECTED

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

> **Rejected 2026-10-06.** Bruce: "don't do hacker news or linked in". Don't re-propose.
