import { test } from "node:test";
import assert from "node:assert/strict";
import {
  assignSummary,
  finishMessage,
  lineLabel,
  orderAssignments,
  unitTone,
  type PatternStatus,
} from "./phonics.ts";

test("a mastered session celebrates and gives the count", () => {
  assert.deepEqual(
    finishMessage({ words_correct: 12, words_total: 14, mastered: true, pattern_name: "-at Word Family" }),
    { title: "You've got it!", detail: "You read 12 of 14 words right." },
  );
});

test("a session under the mark stays encouraging and never says needs practice", () => {
  const message = finishMessage({ words_correct: 6, words_total: 14, mastered: false, pattern_name: "x" });
  assert.equal(message.title, "Nice reading!");
  assert.equal(message.detail, "You read 6 of 14 words right. Let's practice these again soon.");
  assert.doesNotMatch(`${message.title} ${message.detail}`, /needs practice/i);
});

test("a session with no scored words still finishes kindly", () => {
  const message = finishMessage({ words_correct: 0, words_total: 0, mastered: false, pattern_name: "x" });
  assert.match(message.detail, /^You read every line\./);
});

test("open assignments come before mastered ones, keeping their order", () => {
  const items: { id: number; status: PatternStatus }[] = [
    { id: 1, status: "mastered" },
    { id: 2, status: "not_started" },
    { id: 3, status: "needs_practice" },
  ];
  assert.deepEqual(orderAssignments(items).map((item) => item.id), [2, 3, 1]);
});

test("grid cells shade by how much of the unit is mastered", () => {
  assert.equal(unitTone(0, 7), "bg-muted text-muted-foreground");
  assert.equal(unitTone(3, 7), "bg-pastel-yellow text-pastel-yellow-foreground");
  assert.equal(unitTone(7, 7), "bg-pastel-mint text-pastel-mint-foreground");
});

test("labels", () => {
  assert.equal(lineLabel(2, 7), "Line 3 of 7");
  assert.equal(assignSummary(1, 1), "Assign 1 pattern to 1 student");
  assert.equal(assignSummary(7, 22), "Assign 7 patterns to 22 students");
});
