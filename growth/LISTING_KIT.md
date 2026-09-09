# Listing kit — Word Wiz AI

Every directory, roundup and award form asks for the same dozen things in
slightly different shapes. This file is the canonical answer to all of them, so
a submission is copy-paste rather than twenty minutes of rewriting.

**Before you paste anything, read "Numbers that need checking" at the bottom.**
Some figures here are carried over from earlier notes and may be stale. Never
submit a number you haven't confirmed.

---

## Identity

| Field | Value |
|---|---|
| Product name | Word Wiz AI |
| URL | https://wordwizai.com |
| Category | Education → Early literacy / Reading / Phonics |
| Audience | Parents and teachers of children ages 5–8 |
| Pricing | Free. No ads, no subscription, no in-app purchases |
| Platforms | Any modern web browser (desktop, tablet, Chromebook). No install |
| Account required | Optional — practice works without signing up |
| Founded | Built solo by a high school student |
| Recognition | 2nd Place, Congressional App Challenge (CA-15) |

---

## Taglines

Pick by the form's character limit. Counts are exact.

**≤ 50 characters** (44)
```
Free AI reading tutor that hears every sound
```

**≤ 60 characters** (52)
```
A free reading tutor that listens to your child read
```

**≤ 100 characters** (99)
```
Free AI reading tutor for ages 5-8. Listens to a child read aloud and corrects the sounds they miss
```

**≤ 160 characters** (156)
```
Free, browser-based reading tutor for ages 5-8. It listens to a child read aloud, finds the exact sounds they mispronounce, and adapts practice to fix them.
```

---

## Descriptions

**~250 characters** (248)
```
Word Wiz AI is a free reading tutor for children ages 5-8. A child reads a sentence aloud; the app analyses their speech sound by sound, shows exactly which ones were wrong, and builds the next sentence around those sounds. No ads, no subscription.
```

**~500 characters** (495)
```
Word Wiz AI is a free, browser-based reading tutor for children ages 5-8. A child reads a sentence aloud and the app analyses their speech at the phoneme level — the individual sounds inside a word — rather than just checking whether the whole word was right. It shows which sounds were mispronounced, explains them in child-friendly language, and generates the next sentence to target exactly those sounds. It runs in any browser with no install, and it is free with no ads and no subscription.
```

**~1000 characters** (979)
```
Word Wiz AI is a free, browser-based reading tutor for children ages 5-8, built to give the kind of feedback that normally requires a one-on-one tutor.

Most reading apps check whether a child got a word right. Word Wiz AI works a level below that. A child reads a sentence aloud, and the app transcribes their speech into phonemes — the individual sounds inside each word — then compares those against the expected pronunciation. The result is specific: not "that word was wrong", but "the /th/ at the start became /f/". Feedback is written in language a young child understands, and the next practice sentence is generated to target the exact sounds they missed.

It runs in any modern browser with nothing to install, works on a school Chromebook, and is free — no ads, no subscription, no in-app purchases. Practice does not require an account.

The app was built solo by a high school student and placed 2nd in the Congressional App Challenge for California's 15th district.
```

---

## What makes it different

Lead with these; they are what a reviewer or list-maintainer actually cares about.

1. **Phoneme-level feedback.** Almost every competitor scores whole words.
   This identifies the specific sound that was wrong, which is what phonics
   instruction actually acts on.
2. **Genuinely free.** Not a trial, not a freemium tier with the useful parts
   paywalled. Direct competitors run $10–20/month.
3. **No ads.** Relevant for a children's product, and a common disqualifier on
   school-facing lists.
4. **Nothing to install.** Runs on a browser, including locked-down school
   Chromebooks.
5. **Adaptive.** Practice sentences are generated from the child's own error
   history rather than drawn from a fixed bank.

## What to say when asked about limitations

Being straight here builds more credibility than dodging, and reviewers test it.

- **Microphone quality matters.** Speech analysis degrades on poor built-in
  mics. Cheap Chromebook microphones are a real constraint; say so.
- **Ages 5–8.** Not built for older struggling readers yet.
- **English only.**
- **No offline mode.** Analysis happens server-side.

---

## Founder bio

**Short (≤ 200 chars)** (192)
```
Bruce Peters is a high school student who built Word Wiz AI solo — a free reading tutor using speech recognition to give phoneme-level feedback. 2nd Place, Congressional App Challenge (CA-15).
```

**Long**
```
Bruce Peters built Word Wiz AI solo while in high school, after realising that the pronunciation feedback a struggling reader needs most is exactly what reading apps skip: not whether a word was right, but which sound inside it was wrong.

The app uses a speech recognition model that outputs phonemes rather than words, so it can compare a child's actual pronunciation against the expected one sound by sound. It placed 2nd in the Congressional App Challenge for California's 15th district. It is free, and it always will be.
```

---

## Common form fields

| Question | Answer |
|---|---|
| Is there a free version? | The entire product is free. |
| Do you collect data from children? | Audio is processed for pronunciation analysis. See https://wordwizai.com/privacy |
| COPPA / student data privacy | Point to the privacy policy; be prepared for a privacy review |
| Does it require an account? | No — practice works without one. Accounts only save progress |
| What grades? | Pre-K through 2nd (ages 5–8) |
| Subjects | Reading, phonics, early literacy, speech |
| Accessibility | Browser-based; keyboard navigable. No formal WCAG audit yet — say so |
| Open source? | No |
| Pricing model | Free |

---

## Assets you still need to produce

These are the actual blocker on most submissions. Nothing here can be
generated from the repo.

- [ ] **Logo** — square, 512×512 PNG, transparent background
- [ ] **Screenshots** — 3–5, 1280×800, showing a practice session mid-feedback
- [ ] **Social preview image** — 1200×630 PNG at `public/og-image.png`.
      Until it exists, `SeoHead` omits `og:image` entirely, so link previews
      show text with no image. That is deliberate: `og-image.png` does not
      exist, and because the SPA rewrite returns `index.html` with a **200**
      for any missing path, pointing at it served crawlers HTML labelled as a
      PNG — a broken preview that looks like a success. Ship the image, then
      pass `ogImage` to `SeoHead`
- [ ] **Demo video** — 60–90s screen recording. Required by Product Hunt and
      several award programs
- [ ] **2–3 parent testimonials** — the single highest-value missing item

---

## Target list

Ordered by value, not ease.

| Target | Status | Notes |
|---|---|---|
| Common Sense **Privacy** Rating | Not submitted | Their editorial edtech reviews **paused Feb 2026**; the privacy rating still runs and matters more for a kids' audio product |
| ISTE+ASCD EdTech Index | Not submitted | The named replacement for Common Sense reviews. Badge-based: research design, privacy, accessibility |
| Homeschooling with Dyslexia | Not contacted | Maintains app roundups. Dyslexia families are the sharpest fit for phoneme-level feedback |
| EducationalAppStore | Not contacted | Runs a review/certification programme |
| The Edvocate | Not contacted | Publishes dyslexia tool roundups |
| Tech & Learning | Not contacted | Publishes tool overviews; named as a Common Sense alternative |
| Product Hunt | Not launched | One shot — needs the demo video and screenshots first |
| AlternativeTo | Not submitted | "Free alternative to Hooked on Phonics" is a real search |
| AI tool directories | Not submitted | High volume, low value each. The most mechanical work here |
| Local press / district newsletter | Not contacted | "Local student builds free reading tutor" writes itself |

**Common Sense Education paused edtech reviews in February 2026** and removed
existing review pages. If an older plan of yours lists it as a target, that
part is out of date.

---

## Numbers that need checking

Do not paste these until you've confirmed them — they are carried from notes
dated **June 2026** and are around three months stale.

| Figure | Last known | Action |
|---|---|---|
| Signups | 140+ | Check the database before quoting |
| Site visitors | ~9,000 | Check Vercel Analytics |
| Response latency | ~2s | Still accurate as far as the repo shows |
| Testimonials | 0 collected | Blocks the strongest version of every pitch |

Two claims are always safe because they are structural facts, not metrics:
**it is free with no ads**, and **2nd Place, Congressional App Challenge
(CA-15)**.
