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

test("talking wins over the processing idle", () => {
  assert.equal(
    companionMood({ ...quiet, isProcessing: true, isFeedbackPlaying: true }),
    "talking",
  );
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
