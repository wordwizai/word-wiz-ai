// Wording and colours for the phonics path and teacher assignments. No
// imports, so the node test runner can load it directly.

export type PatternStatus =
  | "not_started"
  | "in_progress"
  | "mastered"
  | "needs_practice";

// What teachers see.
export const STATUS_LABEL: Record<PatternStatus, string> = {
  not_started: "Not started",
  in_progress: "In progress",
  mastered: "Mastered",
  needs_practice: "Needs practice",
};

// What children (and the parents beside them) see. Gentler, and never
// "Needs practice".
export const STUDENT_LABEL: Record<PatternStatus, string> = {
  not_started: "New",
  in_progress: "Keep going",
  mastered: "Got it",
  needs_practice: "Try again",
};

// Pastel pairs, because they have dark-mode values (see classes/accuracy.ts).
export const STATUS_TONE: Record<PatternStatus, string> = {
  mastered: "bg-pastel-mint text-pastel-mint-foreground",
  needs_practice: "bg-pastel-yellow text-pastel-yellow-foreground",
  in_progress: "bg-pastel-blue text-pastel-blue-foreground",
  not_started: "bg-muted text-muted-foreground",
};

// The `session_complete` event's data (backend crud/phonics_sessions.py).
export interface SessionResult {
  words_correct: number | null;
  words_total: number | null;
  mastered: boolean;
  // Null if the pattern was removed from the data after the session began.
  pattern_name: string | null;
}

export function finishMessage(result: SessionResult): { title: string; detail: string } {
  const { words_correct: correct, words_total: total } = result;
  const count = total
    ? `You read ${correct ?? 0} of ${total} words right.`
    : "You read every line.";
  return {
    title: result.mastered ? "You've got it!" : "Nice reading!",
    detail: result.mastered ? count : `${count} Let's practice these again soon.`,
  };
}

// Open work first, in the order given (the API's curriculum order), then
// what's already mastered.
export function orderAssignments<T extends { status: PatternStatus }>(items: T[]): T[] {
  return [
    ...items.filter((item) => item.status !== "mastered"),
    ...items.filter((item) => item.status === "mastered"),
  ];
}

// A class grid cell's shade for how much of one unit a student has mastered.
export function unitTone(mastered: number, total: number): string {
  if (total === 0 || mastered === 0) return "bg-muted text-muted-foreground";
  if (mastered === total) return "bg-pastel-mint text-pastel-mint-foreground";
  return "bg-pastel-yellow text-pastel-yellow-foreground";
}

export function lineLabel(index: number, count: number): string {
  return `Line ${index + 1} of ${count}`;
}

export function assignSummary(patterns: number, students: number): string {
  const p = `${patterns} pattern${patterns === 1 ? "" : "s"}`;
  const s = `${students} student${students === 1 ? "" : "s"}`;
  return `Assign ${p} to ${s}`;
}
