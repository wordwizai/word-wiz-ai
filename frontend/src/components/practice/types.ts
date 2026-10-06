import type { RefObject } from "react";

// One sound inside a word, in reading order. The four names match the
// word-level `type`: read right, read as a different sound, left out, or
// added. `expected` is null for an added sound, `actual` for a left-out one.
export interface PhonemeOp {
  type: "match" | "substitution" | "deletion" | "insertion";
  expected: string | null;
  actual: string | null;
}

// What the backend's `analysis` event carries (a pandas frame as dicts keyed
// by row index).
export interface PronunciationAnalysis {
  pronunciation_dataframe: {
    type: Record<number, string>;
    per: Record<number, number | null>;
    ground_truth_word: Record<number, string | null>;
    predicted_word: Record<number, string | null>;
    // Absent on analyses saved before per-sound results existed.
    phoneme_alignment?: Record<number, PhonemeOp[] | null>;
  };
}

export interface SentenceOption {
  sentence: string;
  icon: string;
  action: string;
}

export interface SentenceOptions {
  option_1: SentenceOption;
  option_2: SentenceOption;
}

// The state every practice mode hands to the shared PracticeStage.
export interface PracticeStageState {
  wordArray: string[];
  analysisData: PronunciationAnalysis | null;
  feedback: string | null;
  showHighlightedWords: boolean;
  isRecording: boolean;
  isProcessing: boolean;
  audioLevel: RefObject<number>;
  onStartRecording: () => void;
  onStopRecording: () => void;
  // Null until the spoken feedback for this sentence has arrived.
  onReplayFeedback: (() => void) | null;
}
