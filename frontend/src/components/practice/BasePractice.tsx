import { useContext, useEffect, useState, type ReactElement } from "react";
import { useAudioRecorder } from "@/hooks/useAudioRecorder";
import { useHybridAudioAnalysis } from "@/hooks/useHybridAudioAnalysis";
import { useFeedbackAudio } from "@/hooks/useFeedbackAudio";
import { AuthContext } from "@/contexts/AuthContext";
import { getCurrentSessionState, type Session } from "@/api";
import { showPracticeErrorToast } from "@/utils/errorHandling";
import type { PracticeStageState, PronunciationAnalysis } from "./types";

export interface BasePracticeRenderProps extends PracticeStageState {
  currentSentence: string | null;
  isModelLoading: boolean;
  modelLoadProgress: number;
  displayNextSentence: () => void;
  nextSentence: string | null;
  showNextButton: boolean;
}

interface BasePracticeProps {
  session: Session;
  renderContent: (props: BasePracticeRenderProps) => ReactElement;
}

const FALLBACK_SENTENCE = "The quick brown fox jumped over the lazy dog";

const BasePractice = ({ session, renderContent }: BasePracticeProps) => {
  const [currentSentence, setCurrentSentence] = useState<string | null>(null);
  const [analysisData, setAnalysisData] =
    useState<PronunciationAnalysis | null>(null);
  const [showHighlightedWords, setShowHighlightedWords] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [nextSentence, setNextSentence] = useState<string | null>(null);
  const [showNextButton, setShowNextButton] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const { token } = useContext(AuthContext);
  const feedbackAudio = useFeedbackAudio();

  const {
    processAudio,
    initializeModels,
    isModelLoading,
    modelLoadProgress,
    isClientExtractionEnabled,
  } = useHybridAudioAnalysis({
    onProcessingStart: () => {
      setIsProcessing(true);
      // The old feedback is about the last attempt. Clearing it also lets
      // the mascot celebrate two great reads in a row.
      setFeedback(null);
    },
    onProcessingEnd: () => {
      setIsProcessing(false);
    },
    onAnalysis: (data) => {
      setShowHighlightedWords(true);
      setAnalysisData(data);
    },
    onFeedback: (data) => {
      // Arrives immediately after analysis (locally generated, no GPT).
      setFeedback(data.text);
    },
    onNextSentence: (data) => {
      // Arrives after the GPT call (in parallel with TTS audio). This is the
      // sentence the child reads next; it is not spoken aloud.
      setNextSentence(data.sentence);
      setTimeout(() => {
        setShowNextButton(true);
      }, 1000);
    },
    onAudioFeedback: feedbackAudio.play,
    onError: () => {
      // useAudioTransport already showed the message; just reset the UI.
      setIsProcessing(false);
    },
    sessionId: session.id,
  });

  // Load the in-browser models up front when client extraction is enabled.
  useEffect(() => {
    if (isClientExtractionEnabled) {
      initializeModels();
    }
  }, [isClientExtractionEnabled]);

  useEffect(() => {
    const getCurrentSentence = async () => {
      try {
        const state = await getCurrentSessionState(token ?? "", session.id);
        if (state.type === "full-feedback-state") {
          setCurrentSentence(state.data.gpt_response.sentence);
        } else if (session.activity.activity_settings?.first_sentence) {
          setCurrentSentence(session.activity.activity_settings.first_sentence);
        } else {
          setCurrentSentence(FALLBACK_SENTENCE);
        }
      } catch (error) {
        console.error("Failed to fetch session state:", error);
        // showErrorToast would recategorize this as a model-loading failure.
        showPracticeErrorToast("We couldn't load this practice session. Please refresh the page.");
        if (session.activity.activity_settings?.first_sentence) {
          setCurrentSentence(session.activity.activity_settings.first_sentence);
        }
      }
    };
    getCurrentSentence();
  }, [session.id, token]);

  const { isRecording, startRecording, stopRecording, levelRef } =
    useAudioRecorder((audioFile: File) => {
      processAudio(audioFile, currentSentence ?? "");
    });

  const displayNextSentence = () => {
    setShowHighlightedWords(false);
    setAnalysisData(null);
    setCurrentSentence(nextSentence || FALLBACK_SENTENCE);
    setNextSentence(null);
    setFeedback(null);
    setShowNextButton(false);
    setIsProcessing(false);
    feedbackAudio.reset();
  };

  const wordArray =
    typeof currentSentence === "string" ? currentSentence.split(" ") : [];

  return renderContent({
    currentSentence,
    wordArray,
    analysisData,
    feedback,
    showHighlightedWords,
    isRecording,
    isProcessing,
    isFeedbackPlaying: feedbackAudio.isPlaying,
    audioLevel: levelRef,
    isModelLoading,
    modelLoadProgress,
    onStartRecording: startRecording,
    onStopRecording: stopRecording,
    onReplayFeedback: feedbackAudio.replay,
    displayNextSentence,
    nextSentence,
    showNextButton,
  });
};

export default BasePractice;
