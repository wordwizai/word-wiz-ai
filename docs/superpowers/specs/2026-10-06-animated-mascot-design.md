# Animated mascot

## Goal

Make the Word Wiz hat mascot feel alive by having it react to what the child is
doing (listening while they read, talking while feedback plays, celebrating a
great read) without pulling their eyes off the sentence.

## The component (built)

`frontend/src/components/mascot/` holds three files.

| File | What it does |
|------|--------------|
| `mascotArt.ts` | The shapes from the Figma export (`src/assets/wordwizIcon.svg`), broken into the pieces that move separately, plus each sparkle's burst direction and twinkle delay |
| `mascot.css` | One block of keyframes per mood, selected by `data-mood` |
| `Mascot.tsx` | The `<Mascot>` component |

```tsx
<Mascot mood="talking" className="size-9" />
<Mascot mood="celebrating" onCelebrateEnd={() => setCelebrating(false)} />
<Mascot label="Word Wiz AI" />   // label only where it isn't decoration
```

The exported SVG was already made of separate shapes (head, head shine, brim,
cone, cone shade, three hat stars, four sparkles), so no new art was needed.

### Moods

| Mood | Motion | Meant for |
|------|--------|-----------|
| `still` (default) | None. Same as the old `<img>` | Anywhere the mascot is just the logo |
| `idle` | Slow float, small hat sway, sparkles twinkling out of step | Pages with no reading task (404, About) |
| `talking` | Hat bobs and the head squashes on each beat | While spoken feedback plays |
| `listening` | Head and hat lean in together, sparkles pulse in step | While the mic is on |
| `celebrating` | Squash, hop, the hat pops up, sparkles burst. Plays once | A read the tutor praises |

### Details settled in review

- The stars on the hat never move on their own. They only move with the hat.
- Listening tilts the head and hat as one piece. Tilting only the hat showed
  the flat top edge of the head on both sides.
- The art's head is only the lower half of a circle, hidden under the brim.
  Celebrating lifts the hat, so the component adds the top half of the circle
  and clips it to the area below the brim's top edge. The clip runs the same
  keyframes as the hat, so the round head only ever shows under the brim and
  never beside the cone. The clip edge sits 8 units inside the brim, because
  putting it exactly on the brim's edge left a one-pixel seam. This was checked
  frame by frame with the hidden head-top colored red. Across the hop there
  were 0 stray pixels outside the brim, and the only red was under the lifted
  right side of the brim, which is where it belongs.
- Celebrating plays once and fires `onCelebrateEnd` when it lands. To celebrate
  again the mood has to change first.

### Why CSS keyframes and not framer-motion

framer-motion is already in the app, but the hop needs the hat and the clip
that follows it to stay in exact lockstep, and two elements on the same CSS
keyframes do that for free. CSS also means no JavaScript runs per frame, the
animation works in prerendered HTML, and reduced motion is one media query.

### Reduced motion

Under `prefers-reduced-motion: reduce` nothing animates. Since the hop never
runs, `<Mascot>` calls `onCelebrateEnd` right away so callers aren't left
waiting for it.

### Preview page

`/dev/mascot` shows every mood at large size and at 32, 36 and 64px. It is only
routed in dev builds (`import.meta.env.DEV`), and `scripts/prerender.mjs`
excludes `/dev` because it finds routes by reading `App.tsx`.

## Where it goes

| Surface | Moods | Reason |
|---------|-------|--------|
| Practice screen | listening, talking, celebrating, idle, still | The main reason for the animation. See below |
| 404 page | idle | No reading task, and a little life softens a dead end |
| About page hero | idle | Marketing page, no reading task |
| Sidebar, landing navbar, login, sign-up | stay a static `<img>` | Steady motion beside the reading task (sidebar) or a form is a distraction, and at 32–36px idle barely shows anyway |

### Practice screen

The feedback bubble's icon becomes a permanent companion spot under the
sentence. It's always there, so the child gets used to it. Before the first
attempt it sits still. When feedback arrives, the speech bubble fills in next
to it as it does today.

Its mood comes from practice state, in this order of priority.

1. `listening` while recording
2. `celebrating` once, after a live attempt whose feedback is praise
3. `talking` while the feedback audio is playing
4. `idle` while the server is processing (reads as thinking)
5. `still` otherwise

While recording or processing, the bubble hides the old feedback text and only
the mascot shows, since that text is about the previous attempt.

**Praise** means the feedback text is exactly `Great job!`. That is what
`generate_feedback` in `backend/core/phoneme_feedback_formatter.py` returns when
a read needs no correction, so the mascot celebrates exactly when the child
hears praise. It might be worth replacing the string match with a flag from
the backend later.

**Once per attempt.** Two great reads in a row would leave `feedback` unchanged
and skip the second celebration, so both practice bases clear `feedback` when
processing starts. Feedback restored with a saved choice-story session must not
celebrate, so the trigger only fires after the stage has seen `isProcessing`
for the current attempt.

**Talking** needs to know when the feedback audio is actually playing.
`useFeedbackAudio` gains an `isPlaying` flag driven by the audio element's
`playing`, `pause`, `ended` and `error` events.

## Not in scope

- Eyes or a face. That's a design change in Figma, not animation, and might be
  worth trying next since eyes do the most to make a character feel alive.
- Talking along with the "Hear what to do" help speech.
- The landing page demo (`AnimatedPracticeDemo`). It could show the companion
  talking and celebrating for parents, but that file is being reworked in
  another branch right now, so it may deserve its own follow-up once that lands.
- Lottie or Rive.

## Testing

- The mood order and the praise check are pure functions, tested with
  `node:test`. Node 24 runs TypeScript directly, so no test library is added.
- The moods themselves are checked on `/dev/mascot`.
- The practice flow is checked by hand against `backend/dev_server.py`.
