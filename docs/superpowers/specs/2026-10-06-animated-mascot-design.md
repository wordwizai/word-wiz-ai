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
waiting for it. It reads `matchMedia("(prefers-reduced-motion: reduce)")` at
the moment the mood becomes `celebrating`, because framer-motion's
`useReducedMotion` only checks once at mount. Testing showed that turning the
setting on after the page loaded left the mascot stuck in `celebrating`, since
the CSS skipped the hop while the hook still said motion was fine.

### Preview page

`/dev/mascot` shows every mood at large size and at 32, 36 and 64px. It is only
routed in dev builds (`import.meta.env.DEV`), and `scripts/prerender.mjs`
excludes `/dev` because it finds routes by reading `App.tsx`.

## Where it goes

| Surface | Moods | Reason |
|---------|-------|--------|
| Practice screen | listening, talking, celebrating, idle, still | The main reason for the animation. See below |
| Guest try page (`/try`) | same as practice | It renders `PracticeStage`, so it gets the companion. Its intro and ending screens keep the static `<img>` |
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

The old feedback is about the previous attempt, so it goes away once the child
reads again. While they read, it keeps its place but is invisible (the
`quiet` prop on `PracticeCompanion`). Hiding it outright would shrink the
bubble, and since the page centers vertically, the sentence and mic would jump
about 40px on a phone just as the child starts reading. Once they stop, it's
removed until the new feedback arrives, so the bubble shrinks after the
reading instead of during it. New feedback fades in, and there's no exit
animation, because `AnimatePresence`'s wait mode would hold the next feedback
back until a fade-out finished.

**Praise** means the feedback text is exactly `Great job!`. That is what
`generate_feedback` in `backend/core/phoneme_feedback_formatter.py` returns when
a read needs no correction, so the mascot celebrates exactly when the child
hears praise. It might be worth replacing the string match with a flag from
the backend later.

**Once per attempt.** `PracticeStage` opens an attempt when recording starts
and closes it on the first render with a new `analysisData` object and
non-null feedback. The analysis object is new for every attempt even when the
feedback text repeats, so two great reads in a row both celebrate, and it
still works when the server's events land in a single render (which would
hide `isProcessing` entirely). Anything that arrives while the child is still
reading belongs to an earlier attempt. Feedback restored with a saved
choice-story session never opened an attempt, so it can't celebrate.

Because of that matching, every caller of `PracticeStage` has to set
`feedback` back to null when a new attempt starts processing. Otherwise the
new analysis gets paired with the previous attempt's text, and a stale "Great
job!" could celebrate over a bad read. Both practice bases do it in
`onProcessingStart` and the guest try page does it when it sends the
recording. The contract is written on `PracticeStageState.feedback`.

**Talking** needs to know when the feedback audio is actually playing.
`useFeedbackAudio` has an `isPlaying` flag driven by the audio element's
`playing`, `pause`, `ended`, `waiting` and `error` events. Only the current
clip may change it, `play()` sets it to false until the new clip is really
playing (so a clip the browser refuses to start never talks), and `reset()`
clears it.

### Known tradeoffs

- A recording that gets thrown away ("That was too short", "We didn't hear
  anything", a connection error) leaves the attempt open, so the old feedback
  and its replay button stay hidden until the next real read. Starting the
  attempt at hand-off instead would fix that, but a socket that closes before
  the server answers would then leave the mic disabled behind a spinner.
- Between the child stopping and the server's `processing_started` (upload and
  any in-browser extraction), the mood is `still`, not `idle`.
- The idle float on About and the 404 page runs for as long as the page is
  open. That costs a little paint work and arguably falls under WCAG 2.2.2
  (moving content longer than 5 seconds). Capping it at a few cycles might be
  worth considering.
- It has only been tested in Chromium. The hop relies on an animated element
  inside a `<clipPath>`, which WebKit has had bugs with, so a quick look at
  `/dev/mascot` on an iPad might be worth it.

## Not in scope

- Eyes or a face. That's a design change in Figma, not animation, and might be
  worth trying next since eyes do the most to make a character feel alive.
- Talking along with the "Hear what to do" help speech.
- Pausing the old feedback audio when the child taps the mic. Today it keeps
  playing over the new reading (the mic can pick it up), which was already
  true before this work. With the mascot it also means a little talking with
  no bubble showing. Pausing it, not `reset()`, would keep "Hear this again".
- The landing page demo (`AnimatedPracticeDemo`). It could show the companion
  talking and celebrating for parents, but that file is being reworked in
  another branch right now, so it may deserve its own follow-up once that lands.
- Lottie or Rive.

## Testing

- The mood order and the praise check are pure functions, tested with
  `node:test` (7 tests, `npm test`). Node runs TypeScript directly from 22.18
  and 23.6 on, so no test library is added. Older Node can't run them.
- The moods themselves are checked on `/dev/mascot`.
- The practice flow was checked end to end in headless Chrome against
  `backend/dev_server.py`, with Chrome's fake microphone playing
  `backend/tests/system/test_case_02/audio.wav` (the fallback sentence "The
  quick brown fox jumped over the lazy dog"). The run covered listening, idle
  and talking on a real read, two praised reads in a row, "Hear this again",
  tapping the mic mid-hop, the next read's feedback appearing, no layout jump
  while recording at desktop and phone width, and reduced motion turned on
  before and after the page loaded. Praise was forced by rewriting the
  `feedback` event in the page, since the recording earns a correction.
- A hidden browser pane pauses animation frames, which makes framer-motion and
  CSS animations look stuck. Animation checks need a visible or headless
  browser.
