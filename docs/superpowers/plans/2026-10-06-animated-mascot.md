# Animated mascot rollout — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Put the animated `<Mascot>` into the app, as a companion on the practice screen that listens, talks and celebrates, and as an idle mascot on the 404 and About pages.

**Architecture:** `<Mascot mood>` already exists in `frontend/src/components/mascot/` (CSS keyframes picked by `data-mood`). A pure function, `companionMood`, turns practice state into a mood. `useFeedbackAudio` reports when feedback audio is playing, both practice bases pass that through `PracticeStageState`, and `PracticeStage` owns the once-per-attempt celebration. A new `PracticeCompanion` replaces the old `FeedbackBubble`.

**Tech Stack:** React 19 + TypeScript + Tailwind v4 + framer-motion. Tests use `node:test`, since Node 24 runs `.ts` files directly and the frontend has no test library.

Spec: `docs/superpowers/specs/2026-10-06-animated-mascot-design.md`

Preview of every mood: run the `wordwiz-dev` launch config and open `http://localhost:5174/dev/mascot`.

**Working on `dev`:** other sessions commit to `dev` in the same checkout. Commit only the paths each task lists (`git commit -m ... -- <paths>`), never `git add -A` or `git commit -a`. (In the end the work was done on `feat/animated-mascot` in a worktree and merged into `dev`.)

`npm run typecheck` already fails on 11 errors in files this plan doesn't touch (`api.ts`, `About.tsx` unused variables, `errorHandling.ts`, ...). Each task checks that no *new* errors mention the files it changed.

## What changed during implementation

The tasks below are the plan as written. Review and testing changed several things, and the code (and the spec) are the source of truth. The differences are listed here.

- **Task 1.** A seventh test was added (talking beats the processing idle), so later steps expect `pass 7`. The `MascotMood` comment in `Mascot.tsx` now says idle also covers the short wait while a reading is checked.
- **Task 2.** `play()` also calls `setIsPlaying(false)` right after pausing the old clip, so a clip the browser refuses to start never leaves the flag on, and there's a fifth listener, `waiting` → false.
- **Task 3.** The comment on `setFeedback(null)` in `onProcessingStart` now says why it's load-bearing. `PracticeStage` pairs each new analysis with the feedback that follows it, so stale text must be gone first. The contract is also written on `PracticeStageState.feedback` in `types.ts`.
- **Task 4.**
  - The `attemptInFlight` ref was replaced. An `attemptOpen` state opens when recording starts, and an `analysisAtStart` ref remembers the analysis at that moment. The attempt closes on the first render, not recording, with a new analysis object and non-null feedback. This survives server events that land in one render and repeated "Great job!" text.
  - The companion gets `feedback={attemptOpen && !isRecording ? null : feedback}` and `quiet={isRecording}`. `PracticeCompanion` keeps quiet text in place with `invisible`, and its background only shows when there's visible feedback. This stops the old feedback popping back during the upload and stops the layout jumping when the child starts reading.
  - `AnimatePresence` was removed from `PracticeCompanion`. New feedback still fades in, keyed on its text, with no exit animation, and the fade-in is skipped under reduced motion.
- **Task 5.** It was run in headless Chrome with a fake microphone instead of by hand, plus layout checks at desktop and phone width and reduced motion turned on after the page loaded (see the spec's Testing section).
- **Reduced motion.** `Mascot.tsx` reads the media query live when celebrating instead of using framer-motion's `useReducedMotion`, which only checks at mount.
- **Guest try page.** `dev` gained `frontend/src/pages/TryPage.tsx`, which renders `PracticeStage` directly. After merging `dev` it passes `isFeedbackPlaying` and clears `feedback` when it sends a recording.

---

## Files

| File | Change |
|------|--------|
| `frontend/package.json` | Add a `test` script |
| `frontend/src/components/practice/companionMood.ts` | New. `companionMood` and `isPraise` |
| `frontend/src/components/practice/companionMood.test.ts` | New. Tests for both |
| `frontend/src/hooks/useFeedbackAudio.ts` | Add `isPlaying` |
| `frontend/src/components/practice/types.ts` | Add `isFeedbackPlaying` to `PracticeStageState` |
| `frontend/src/components/practice/BasePractice.tsx` | Pass `isFeedbackPlaying`; clear feedback when processing starts |
| `frontend/src/components/practice/ChoiceStoryBasePractice.tsx` | Same two changes |
| `frontend/src/components/practice/PracticeCompanion.tsx` | New. The mascot spot under the sentence |
| `frontend/src/components/practice/PracticeStage.tsx` | Celebration state; render `PracticeCompanion`; delete `FeedbackBubble` |
| `frontend/src/pages/NotFoundPage.tsx` | Idle mascot |
| `frontend/src/pages/About.tsx` | Idle mascot |

---

### Task 1: Mood logic

**Files:**
- Modify: `frontend/package.json` (the `scripts` block)
- Create: `frontend/src/components/practice/companionMood.test.ts`
- Create: `frontend/src/components/practice/companionMood.ts`

- [ ] **Step 1: Add the test script**

In `frontend/package.json`, add a `test` line after `lint`:

```json
    "lint": "eslint .",
    "test": "node --test \"src/**/*.test.ts\"",
```

The quotes let Node expand the glob itself, which works the same in cmd, PowerShell and bash.

- [ ] **Step 2: Write the failing test**

Create `frontend/src/components/practice/companionMood.test.ts`:

```ts
import { test } from "node:test";
import assert from "node:assert/strict";
import { companionMood, isPraise } from "./companionMood.ts";

const quiet = {
  isRecording: false,
  isProcessing: false,
  isFeedbackPlaying: false,
  celebrating: false,
};

test("listens while recording, whatever else is going on", () => {
  assert.equal(
    companionMood({
      isRecording: true,
      isProcessing: true,
      isFeedbackPlaying: true,
      celebrating: true,
    }),
    "listening",
  );
});

test("a celebration plays over the praise audio", () => {
  assert.equal(
    companionMood({ ...quiet, celebrating: true, isFeedbackPlaying: true }),
    "celebrating",
  );
});

test("talks while the feedback audio plays", () => {
  assert.equal(companionMood({ ...quiet, isFeedbackPlaying: true }), "talking");
});

test("idles while the server checks the reading", () => {
  assert.equal(companionMood({ ...quiet, isProcessing: true }), "idle");
});

test("stays still the rest of the time", () => {
  assert.equal(companionMood(quiet), "still");
});

test("praise is the formatter's exact 'Great job!'", () => {
  assert.equal(isPraise("Great job!"), true);
  assert.equal(isPraise("  Great job!  "), true);
  assert.equal(isPraise("Keep practicing!"), false);
  assert.equal(isPraise("Great job! Now try the 'sh' in 'ship'."), false);
  assert.equal(isPraise(null), false);
});
```

- [ ] **Step 3: Run it to make sure it fails**

Run (from `frontend/`): `npm test`
Expected: FAIL with `ERR_MODULE_NOT_FOUND` for `companionMood.ts`.

- [ ] **Step 4: Write the implementation**

Create `frontend/src/components/practice/companionMood.ts`:

```ts
import type { MascotMood } from "@/components/mascot/Mascot";

export interface CompanionState {
  isRecording: boolean;
  isProcessing: boolean;
  isFeedbackPlaying: boolean;
  // True for one hop after a live attempt earns praise.
  celebrating: boolean;
}

// What the practice-screen mascot is doing, most important first.
export function companionMood({
  isRecording,
  isProcessing,
  isFeedbackPlaying,
  celebrating,
}: CompanionState): MascotMood {
  if (isRecording) return "listening";
  if (celebrating) return "celebrating";
  if (isFeedbackPlaying) return "talking";
  if (isProcessing) return "idle";
  return "still";
}

// generate_feedback in backend/core/phoneme_feedback_formatter.py returns
// exactly this when a read needs no correction.
const PRAISE = "Great job!";

export function isPraise(feedback: string | null): boolean {
  return feedback?.trim() === PRAISE;
}
```

The `import type` line is erased before Node runs the file, so the `@/` alias never has to resolve under `node --test`. Keep this file free of runtime imports.

- [ ] **Step 5: Run the tests to make sure they pass**

Run (from `frontend/`): `npm test`
Expected: `ℹ tests 6`, `ℹ pass 6`, `ℹ fail 0`.

- [ ] **Step 6: Lint and typecheck**

Run (from `frontend/`):
```bash
npx eslint src/components/practice/companionMood.ts src/components/practice/companionMood.test.ts
npm run typecheck 2>&1 | grep companionMood
```
Expected: no output from either.

- [ ] **Step 7: Commit**

```bash
git add frontend/package.json frontend/src/components/practice/companionMood.ts frontend/src/components/practice/companionMood.test.ts
git commit -m "Pick the practice mascot's mood from practice state" -- frontend/package.json frontend/src/components/practice/companionMood.ts frontend/src/components/practice/companionMood.test.ts
```

---

### Task 2: Know when feedback audio is playing

**Files:**
- Modify: `frontend/src/hooks/useFeedbackAudio.ts` (whole file)

There's no DOM in `node:test`, so this hook is checked in the browser in Task 5.

- [ ] **Step 1: Replace the hook**

Replace all of `frontend/src/hooks/useFeedbackAudio.ts` with:

```ts
import { useCallback, useEffect, useRef, useState } from "react";
import { showAudioPlaybackError } from "@/utils/errorHandling";

// Plays the tutor's spoken feedback and keeps it around so a child who
// can't read the feedback text yet can hear it again.
export function useFeedbackAudio() {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [hasAudio, setHasAudio] = useState(false);
  // True while the feedback is coming out of the speakers, so the mascot
  // can talk along with it.
  const [isPlaying, setIsPlaying] = useState(false);

  const start = (audio: HTMLAudioElement) =>
    audio.play().catch((error) => {
      console.error("[AudioFeedback] Failed to play audio:", error);
      showAudioPlaybackError(error);
    });

  const play = useCallback((url: string) => {
    audioRef.current?.pause();
    const audio = new Audio(url);
    // Only the current clip may change isPlaying. A replaced clip's late
    // pause event would otherwise cut the new clip's talking short.
    const track = (playing: boolean) => () => {
      if (audioRef.current === audio) setIsPlaying(playing);
    };
    audio.addEventListener("playing", track(true));
    audio.addEventListener("pause", track(false));
    audio.addEventListener("ended", track(false));
    audio.addEventListener("error", () => {
      console.error("[AudioFeedback] Playback error:", audio.error?.message);
      track(false)();
    });
    audioRef.current = audio;
    setHasAudio(true);
    start(audio);
  }, []);

  const replay = useCallback(() => {
    const audio = audioRef.current;
    if (!audio) return;
    audio.currentTime = 0;
    start(audio);
  }, []);

  const reset = useCallback(() => {
    audioRef.current?.pause();
    audioRef.current = null;
    setHasAudio(false);
    // The pause above is ignored by `track` once the ref is cleared.
    setIsPlaying(false);
  }, []);

  useEffect(() => () => audioRef.current?.pause(), []);

  return { play, replay: hasAudio ? replay : null, reset, isPlaying };
}
```

The only changes are the `isPlaying` state, the four listeners, the `setIsPlaying(false)` in `reset`, and `isPlaying` in the return value.

- [ ] **Step 2: Lint and typecheck**

Run (from `frontend/`):
```bash
npx eslint src/hooks/useFeedbackAudio.ts
npm run typecheck 2>&1 | grep useFeedbackAudio
```
Expected: no output from either.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/hooks/useFeedbackAudio.ts
git commit -m "Report when the spoken feedback is playing" -- frontend/src/hooks/useFeedbackAudio.ts
```

---

### Task 3: Pass playback state through, and clear old feedback

**Files:**
- Modify: `frontend/src/components/practice/types.ts` (`PracticeStageState`)
- Modify: `frontend/src/components/practice/BasePractice.tsx` (`onProcessingStart`, `renderContent` call)
- Modify: `frontend/src/components/practice/ChoiceStoryBasePractice.tsx` (`onProcessingStart`, `renderContent` call)

Clearing feedback when processing starts matters because `PracticeStage` celebrates when `feedback` *changes* to praise. Without it, two great reads in a row leave `feedback` at `"Great job!"` and the second never celebrates.

- [ ] **Step 1: Add the field to the shared state**

In `frontend/src/components/practice/types.ts`, inside `PracticeStageState`, change

```ts
  isRecording: boolean;
  isProcessing: boolean;
```

to

```ts
  isRecording: boolean;
  isProcessing: boolean;
  // True while the spoken feedback is playing.
  isFeedbackPlaying: boolean;
```

- [ ] **Step 2: Typecheck to see where it's missing**

Run (from `frontend/`): `npm run typecheck 2>&1 | grep -i "practice"`
Expected: two errors saying `isFeedbackPlaying` is missing, one in `BasePractice.tsx` and one in `ChoiceStoryBasePractice.tsx`, at their `renderContent({` calls.

- [ ] **Step 3: Update `BasePractice.tsx`**

Change

```ts
    onProcessingStart: () => {
      setIsProcessing(true);
    },
```

to

```ts
    onProcessingStart: () => {
      setIsProcessing(true);
      // The old feedback is about the last attempt. Clearing it also lets
      // the mascot celebrate two great reads in a row.
      setFeedback(null);
    },
```

and in the `renderContent({ ... })` call at the bottom, change

```ts
    isRecording,
    isProcessing,
```

to

```ts
    isRecording,
    isProcessing,
    isFeedbackPlaying: feedbackAudio.isPlaying,
```

- [ ] **Step 4: Update `ChoiceStoryBasePractice.tsx`**

It has the same two spots. Change

```ts
    onProcessingStart: () => {
      setIsProcessing(true);
    },
```

to

```ts
    onProcessingStart: () => {
      setIsProcessing(true);
      // The old feedback is about the last attempt. Clearing it also lets
      // the mascot celebrate two great reads in a row.
      setFeedback(null);
    },
```

and in its `renderContent({ ... })` call, change

```ts
    isRecording,
    isProcessing,
```

to

```ts
    isRecording,
    isProcessing,
    isFeedbackPlaying: feedbackAudio.isPlaying,
```

- [ ] **Step 5: Typecheck and lint**

Run (from `frontend/`):
```bash
npm run typecheck 2>&1 | grep -i "practice"
npx eslint src/components/practice/types.ts src/components/practice/BasePractice.tsx src/components/practice/ChoiceStoryBasePractice.tsx
```
Expected: no output from either. `GenericPractice` spreads `{...props}` into `PracticeStage`, so the new field reaches it without changes.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/practice/types.ts frontend/src/components/practice/BasePractice.tsx frontend/src/components/practice/ChoiceStoryBasePractice.tsx
git commit -m "Pass feedback playback to the practice stage; clear old feedback per attempt" -- frontend/src/components/practice/types.ts frontend/src/components/practice/BasePractice.tsx frontend/src/components/practice/ChoiceStoryBasePractice.tsx
```

---

### Task 4: The practice companion

**Files:**
- Create: `frontend/src/components/practice/PracticeCompanion.tsx`
- Modify: `frontend/src/components/practice/PracticeStage.tsx` (imports, props, a celebration block, the feedback block, delete `FeedbackBubble`)

- [ ] **Step 1: Create the companion**

Create `frontend/src/components/practice/PracticeCompanion.tsx`:

```tsx
import { AnimatePresence, motion } from "framer-motion";
import { Volume2 } from "lucide-react";
import Mascot, { type MascotMood } from "@/components/mascot/Mascot";
import { FeedbackAnimatedText } from "@/components/FeedbackAnimatedText";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

// The mascot's spot under the sentence. It stays put the whole time so the
// child gets used to it. It listens while they read, and the speech bubble
// fills in beside it when the feedback arrives.
interface PracticeCompanionProps {
  mood: MascotMood;
  // Null while there's nothing to say. Then only the mascot shows.
  feedback: string | null;
  onReplay: (() => void) | null;
  onCelebrateEnd: () => void;
}

const PracticeCompanion = ({
  mood,
  feedback,
  onReplay,
  onCelebrateEnd,
}: PracticeCompanionProps) => (
  <div
    className={cn(
      "flex w-full max-w-2xl items-start gap-3 rounded-2xl p-3 transition-colors duration-300 sm:p-4",
      feedback ? "bg-muted/70" : "bg-transparent",
    )}
  >
    <span className="flex size-12 shrink-0 items-center justify-center rounded-xl bg-card shadow-xs">
      <Mascot mood={mood} onCelebrateEnd={onCelebrateEnd} className="size-9" />
    </span>
    <AnimatePresence mode="wait">
      {feedback && (
        <motion.div
          key={feedback}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0 }}
          className="flex min-h-12 flex-1 items-start gap-3"
        >
          <FeedbackAnimatedText
            feedback={feedback}
            className="flex-1 self-center text-base text-foreground sm:text-lg"
          />
          {onReplay && (
            <Button
              variant="ghost"
              size="icon"
              onClick={onReplay}
              aria-label="Hear this again"
              className="shrink-0 rounded-xl text-primary hover:bg-card"
            >
              <Volume2 className="size-5" />
            </Button>
          )}
        </motion.div>
      )}
    </AnimatePresence>
  </div>
);

export default PracticeCompanion;
```

The bubble styles, text and replay button are copied from the old `FeedbackBubble`. The mascot tile grows from `size-11` to `size-12` and the mascot from `size-8` to `size-9` so the moods read better.

- [ ] **Step 2: Update the imports in `PracticeStage.tsx`**

Delete these two lines:

```tsx
import { FeedbackAnimatedText } from "@/components/FeedbackAnimatedText";
```

```tsx
import { wordWizIcon } from "@/assets";
```

and change

```tsx
import type { PracticeStageState, SentenceOptions } from "./types";
```

to

```tsx
import type { PracticeStageState, SentenceOptions } from "./types";
import PracticeCompanion from "./PracticeCompanion";
import { companionMood, isPraise } from "./companionMood";
```

- [ ] **Step 3: Take the new prop**

In the `PracticeStage` parameter list, change

```tsx
  isRecording,
  isProcessing,
  audioLevel,
```

to

```tsx
  isRecording,
  isProcessing,
  isFeedbackPlaying,
  audioLevel,
```

- [ ] **Step 4: Add the celebration state and mood**

Right after the line

```tsx
  const hasAttempted = showHighlightedWords || !!feedback;
```

add

```tsx
  // Celebrate a read the tutor praises, once per attempt. Feedback that
  // comes back with a saved session isn't an attempt, so the trigger waits
  // until this screen has seen the attempt being processed.
  const [celebrating, setCelebrating] = useState(false);
  const attemptInFlight = useRef(false);

  useEffect(() => {
    if (isRecording) setCelebrating(false);
    if (isProcessing) attemptInFlight.current = true;
  }, [isRecording, isProcessing]);

  useEffect(() => {
    if (!feedback || !attemptInFlight.current) return;
    attemptInFlight.current = false;
    if (isPraise(feedback)) setCelebrating(true);
  }, [feedback]);

  const mascotMood = companionMood({
    isRecording,
    isProcessing,
    isFeedbackPlaying,
    celebrating,
  });
```

`setCelebrating(false)` on recording matters. If the child taps the mic mid-hop, the mood switches to listening, the hop never finishes, and `onCelebrateEnd` never fires. Without the reset, the hop would replay as soon as recording stopped.

- [ ] **Step 5: Render the companion instead of the bubble**

In the JSX, replace

```tsx
          <AnimatePresence>
            {feedback && (
              <FeedbackBubble
                key="feedback"
                feedback={feedback}
                onReplay={onReplayFeedback}
              />
            )}
          </AnimatePresence>
```

with

```tsx
          {/* Old feedback is about the last attempt, so hide it while the
              child reads again. */}
          <PracticeCompanion
            mood={mascotMood}
            feedback={isRecording || isProcessing ? null : feedback}
            onReplay={onReplayFeedback}
            onCelebrateEnd={() => setCelebrating(false)}
          />
```

- [ ] **Step 6: Delete `FeedbackBubble`**

Delete the whole `const FeedbackBubble = ({ ... }) => ( ... );` component, from `const FeedbackBubble = ({` to its closing `);` just above `const ChoicePicker`.

- [ ] **Step 7: Typecheck and lint**

Run (from `frontend/`):
```bash
npm run typecheck 2>&1 | grep -i "practice"
npx eslint src/components/practice
```
Expected: no output from either. If eslint reports `wordWizIcon`, `FeedbackAnimatedText` or `Volume2` as unused, recheck Step 2. `Volume2` should still be used by the "Hear what to do" button, and `AnimatePresence` by the next-sentence arrow.

- [ ] **Step 8: Commit**

```bash
git add frontend/src/components/practice/PracticeCompanion.tsx frontend/src/components/practice/PracticeStage.tsx
git commit -m "Give the practice screen a mascot that listens, talks and celebrates" -- frontend/src/components/practice/PracticeCompanion.tsx frontend/src/components/practice/PracticeStage.tsx
```

---

### Task 5: Check the practice flow in the browser

**Files:** none (verification only). This needs a microphone, so it may have to be done by hand.

- [ ] **Step 1: Start the servers**

Start the `wordwiz-backend-dev` launch config (`backend/dev_server.py`, local SQLite, seeded; never `main.py`, which uses the shared RDS database) and the `wordwiz-dev` launch config (frontend on `http://localhost:5174`). `frontend/.env` already points the frontend at `http://localhost:8000`.

- [ ] **Step 2: Sign in and open a practice session**

Sign in with the demo account (`DEMO_EMAIL` / `DEMO_PASSWORD` in `backend/dev_server.py`), go to `/practice`, and start any activity.

- [ ] **Step 3: Walk through the moods**

Check each of these.

1. Before the first attempt, the mascot sits still in its tile under the sentence, with no bubble background.
2. Tapping the mic makes it lean in and pulse (listening).
3. After stopping, it floats (idle) once the mic button shows its spinner.
4. When feedback arrives, the bubble fills in and the mascot bobs (talking) while the audio plays, then goes still when the audio ends.
5. Read a sentence perfectly. The mascot hops once over "Great job!", then talks or goes still.
6. Tap the mic again and read it perfectly again. It celebrates again.
7. Tap "Hear this again". It talks along with the replay.
8. Tap the mic in the middle of a hop. It switches to listening and doesn't hop again after you stop.
9. In a choice story, read until you get "Great job!", then reload the page. The restored feedback shows, and the mascot does not celebrate.
10. In DevTools, open Rendering and emulate `prefers-reduced-motion: reduce`. Nothing moves, and the screen still works.

- [ ] **Step 4: Fix anything that fails, then repeat Step 3**

If a fix touches the Task 1 logic, add a test for it in `companionMood.test.ts` first.

---

### Task 6: Idle mascot on the 404 and About pages

**Files:**
- Modify: `frontend/src/pages/NotFoundPage.tsx` (import line, the `<img>`)
- Modify: `frontend/src/pages/About.tsx` (import line, the hero `<img>`)

- [ ] **Step 1: Update `NotFoundPage.tsx`**

Change

```tsx
import { wordWizIcon } from "@/assets";
```

to

```tsx
import Mascot from "@/components/mascot/Mascot";
```

and change

```tsx
        <img src={wordWizIcon} alt="" className="mx-auto size-16" />
```

to

```tsx
        <Mascot mood="idle" className="mx-auto size-16" />
```

- [ ] **Step 2: Update `About.tsx`**

Change

```tsx
import { wordWizIcon } from "@/assets";
```

to

```tsx
import Mascot from "@/components/mascot/Mascot";
```

and change

```tsx
            <img src={wordWizIcon} alt="Word Wiz AI" className="w-14 h-14" />
```

to

```tsx
            <Mascot mood="idle" label="Word Wiz AI" className="size-14" />
```

- [ ] **Step 3: Typecheck and lint**

Run (from `frontend/`):
```bash
npm run typecheck 2>&1 | grep -E "NotFoundPage|About" | grep -v "staggerContainer\|childVariant"
npx eslint src/pages/NotFoundPage.tsx src/pages/About.tsx
```
Expected: no output from the first command. `About.tsx` already has two unused-variable errors (`staggerContainer`, `childVariant`) that this task leaves alone. eslint may print warnings that existed before this change, but no errors that mention `Mascot` or `wordWizIcon`.

- [ ] **Step 4: Check them in the browser**

With the `wordwiz-dev` server running, open `http://localhost:5174/about` and `http://localhost:5174/no-such-page`. On each, the mascot should float with twinkling sparkles. In the console:

```js
[...document.querySelectorAll("svg.mascot")].map((s) => [s.dataset.mood, s.getAnimations({ subtree: true }).length])
```

Expected: `[["idle", 6]]` on each page (float, sway and four sparkles).

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/NotFoundPage.tsx frontend/src/pages/About.tsx
git commit -m "Let the mascot float on the 404 and About pages" -- frontend/src/pages/NotFoundPage.tsx frontend/src/pages/About.tsx
```

---

### Task 7: Final checks

**Files:** none

- [ ] **Step 1: Tests and lint**

Run (from `frontend/`):
```bash
npm test
npx eslint src/components/mascot src/components/practice src/hooks/useFeedbackAudio.ts src/pages/NotFoundPage.tsx src/pages/About.tsx src/pages/MascotPreview.tsx
```
Expected: `ℹ pass 7`, `ℹ fail 0`, and no eslint errors.

- [ ] **Step 2: Production build without the preview page**

Run (from `frontend/`):
```bash
npm run build:only
grep -rl "Mascot moods" dist/assets || echo "preview page not in the build"
```
Expected: the build succeeds and the second command prints `preview page not in the build`.

- [ ] **Step 3: Prerendered build**

Run (from `frontend/`): `npm run build`
Expected: it finishes without errors, and `dist/sitemap.xml` has no `/dev/` URL (`grep -c "/dev/" dist/sitemap.xml` prints `0`).
