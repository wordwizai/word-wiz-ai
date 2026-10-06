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
