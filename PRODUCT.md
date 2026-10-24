# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

The child is always the one reading. Design work serves the **parent at home** first (confirmed by Bruce, 2026-10-23). The parent finds Word Wiz, decides to try it, makes the account, and often sits beside the child for a few sentences a day. Many parents were never taught phonics themselves, and most arrive from Google on a guide or article about one specific problem (blending, silent e, b and d mix-ups, guessing instead of sounding out).

The reader is a child of about 5 to 8, early in learning to read. Practice screens talk to the child. Everything around them (signup, progress, guides, settings) talks to the parent.

Children with dyslexia and their families are a named audience whose needs shape design (confirmed). Phoneme-level feedback fits them more sharply than anyone else.

Teachers and reading specialists are a second audience. They create classes, assign phonics patterns, and look at which patterns a student keeps missing. Homeschooling families sit with the parents.

## Product Purpose

Word Wiz AI is a free reading tutor that runs in the browser. A child reads a sentence aloud, the server turns the recording into IPA phonemes, lines them up against the expected words, and finds which sounds inside which words came out wrong. The child then hears short spoken feedback, and the next sentence is written around the sounds they missed.

Success is a child who gets a reading scored, hears feedback that names a real sound, and comes back the next day. For the parent, success is knowing what their child is working on without needing phonics training.

## Positioning

Most reading apps check whether a whole word was right. Word Wiz listens one level lower and names the sound, for example that the /th/ at the start of a word became /f/. That is the unit phonics teaching acts on. It is also free with no ads, no subscription and no in-app purchases, and it runs in any modern browser, including school Chromebooks, with nothing to install.

## Operating Context

- Practice is spoken out loud into a microphone, usually on a laptop, tablet or Chromebook at home. Microphone quality varies a lot, and cheap built-in mics make the analysis worse.
- Sessions are short, a few sentences at a time.
- Practice modes are unlimited practice, stories, stories where the child picks what happens next, and phonics pattern sessions. The phonics path orders 113 patterns into 18 units. A pattern session reads word lines of up to five words, then sentences, and a pattern counts as mastered at 80%.
- `/try` lets a parent see it work on three sentences with no account. Recordings from that page are not saved. Each browser gets one guest record, which becomes the account when that browser signs up.
- Results stream back in steps (analysis, then written feedback, then the spoken audio), so practice screens have to hold a child's attention through a short wait between them.
- The mascot's moods are tied to moments (listening while the mic is on, talking while feedback plays, celebrating a great read). It stays still beside a sentence so a child's eyes stay on the words.
- Discovery is mostly organic search into prerendered guides, articles, comparisons and practice-word pages, plus some referrals from ChatGPT. The homepage is where visitors turn into signups.

## Capabilities and Constraints

- Accounts by email or Google, with teacher and student roles, classes, class joins, assignments, a progress dashboard, and settings with light and dark mode.
- Assignment status (not started, in progress, mastered, needs practice) is always computed from sessions and never stored.
- English only. No offline mode, since analysis happens on the server.
- Ages 5 to 8 is the current audience but not a binding limit (Bruce, 2026-10-23). The homepage says kindergarten through 3rd grade and the listing kit says Pre-K through 2nd, which still disagree.
- Scoring rules live in the backend and are mirrored in two places that design work touches. `WordBadge.tsx` colours words by PER on the practice screen, and the landing page sound sorter (`frontend/src/components/landing/soundSorter/model.ts`) acts out the same thresholds. A word is only corrected out loud when at least three of its sounds were wrong. Anything that shows scoring has to stay consistent with these.
- Where a recording goes is part of the product. It goes to the Word Wiz server, which scores each sound, and to Deepgram for speech-to-text, which does not train on it. Google Cloud Text-to-Speech voices the feedback and never receives a recording. Word Wiz does not save recordings, keeps scores, and never sells data or uses it for advertising. A surface that asks for the microphone should say this in plain words.
- Pages under `/practice` are skipped by the prerender step, so `/phonics` stays free for a public page.
- **Open:** Bruce marked one more binding commitment on 2026-10-23 without naming it. It still has to be written down here.

## Brand Commitments

- The name is Word Wiz AI, shortened to "Word Wiz" in running copy.
- Free forever, with no ads, no paid tier, no subscription and no in-app purchases (confirmed binding). The founder bio says it "is free, and it always will be."
- The wizard-hat mascot (`frontend/src/components/mascot/`) is also the logo in its still mood.
- Current copy speaks to parents as "your child" in plain, warm, specific sentences, and to children in short encouraging lines ("Keep practicing!", "Great job!"). The About page founder section is first person and direct. This is how the repo reads today, not a voice guide Bruce has signed off on.

## Evidence on Hand

- 2nd Place, Congressional App Challenge, California's 15th district.
- Built by Bruce Peters while in high school (founder section on `/about`, bios in `growth/LISTING_KIT.md`).
- Confirmed accurate by Bruce on 2026-10-23, the homepage trust badges "Ed Tech Indexed (Official App)", "100% Data Safety", "Backed with Real AI Research", "2 Clicks to Set Up" and "100% Free" (`frontend/src/components/TrustBadgeCarousel.tsx`), and the About page's description of the team. The listing kit still lists the EdTech Index as not submitted, so that row looks out of date.
- The speechocean762 accuracy benchmark set the scoring defaults (`BENCHMARK.md`, `backend/tests/benchmark/`).
- Ready-to-paste taglines, descriptions and founder bios in `growth/LISTING_KIT.md`.
- A social preview image at `frontend/public/og-image.png`, the mascot, and the landing page sound sorter figure.
- **Absent, do not fabricate.** No parent testimonials have been collected, and there is no demo video or finished screenshot set. Usage figures (signups, visitors, response time) go stale fast and need checking before anyone quotes them.

## Product Principles

1. **Name the sound, not just the word.** Feedback is only useful when it points at a specific sound in a specific word.
2. **The child reads, the adult decides.** Practice screens speak to a 5 to 8 year old in few words. Signup, progress and guides speak to a parent who may not know phonics.
3. **Keep eyes on the words.** While a sentence is on screen, motion and decoration step back.
4. **Free means free.** No paywalls, upsells, trial language or ads anywhere, so the product never has to walk any of it back.
5. **Say what happens.** Microphone limits, English only, and where a recording goes are stated plainly instead of hidden.

## Accessibility & Inclusion

- WCAG 2.2 AA is the target (confirmed). Recent work already raised text contrast, respected Reduce Motion, and made student cards open by keyboard.
- Children with dyslexia are a named audience. The readers are learning to read, so instructions for them should not depend on reading alone. Spoken feedback already carries the main message.
- Practice depends on a microphone and on speaking aloud, and the browser asks for mic permission on first use. Those moments need a calm, clear path for a parent setting it up.
