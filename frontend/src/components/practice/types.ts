import type { RefObject } from "react";

// What the backend's `analysis` event carries (a pandas frame as dicts keyed
// by row index).
export interface PronunciationAnalysis {
  pronunciation_dataframe: {
    type: Record<number, string>;
    per: Record<number, number | null>;
    ground_truth_word: Record<number, string | null>;
    predicted_word: Record<number, string | null>;
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
