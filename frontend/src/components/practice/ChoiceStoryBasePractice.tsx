import { useContext, useEffect, useState, type ReactElement } from "react";
import { useAudioRecorder } from "@/hooks/useAudioRecorder";
import { useHybridAudioAnalysis } from "@/hooks/useHybridAudioAnalysis";
import { useFeedbackAudio } from "@/hooks/useFeedbackAudio";
import { AuthContext } from "@/contexts/AuthContext";
import { getCurrentSessionState, type Session } from "@/api";
import { showPracticeErrorToast } from "@/utils/errorHandling";
import type {
  PracticeStageState,
  PronunciationAnalysis,
  SentenceOptions,
} from "./types";

export interface ChoiceStoryRenderProps extends PracticeStageState {
  currentSentence: string | null;
  isModelLoading: boolean;
  modelLoadProgress: number;
  displayNextSentence: (nextSentence: string) => void;
  sentenceOptions: SentenceOptions | null;
  showSentenceOptions: boolean;
}

interface ChoiceStoryBasePracticeProps {
  session: Session;
  renderContent: (props: ChoiceStoryRenderProps) => ReactElement;
}

const isValidOptions = (value: unknown): value is SentenceOptions => {
  const options = value as SentenceOptions | null | undefined;
  return (
    typeof options?.option_1?.sentence === "string" &&
    typeof options?.option_1?.action === "string" &&
    typeof options?.option_2?.sentence === "string" &&
    typeof options?.option_2?.action === "string"
  );
};

const ChoiceStoryBasePractice = ({
  session,
  renderContent,
}: ChoiceStoryBasePracticeProps) => {
  const [currentSentence, setCurrentSentence] = useState<string | null>(null);
  const [analysisData, setAnalysisData] =
    useState<PronunciationAnalysis | null>(null);
  const [showHighlightedWords, setShowHighlightedWords] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [sentenceOptions, setSentenceOptions] =
    useState<SentenceOptions | null>(null);
  const [showSentenceOptions, setShowSentenceOptions] = useState(false);
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
    },
    onProcessingEnd: () => {
      setIsProcessing(false);
    },
    onAnalysis: (data) => {
      setShowHighlightedWords(true);
      setAnalysisData(data);
    },
    // The server sends feedback text and the two story branches as separate
    // events (`feedback`, then `next_sentence` with {option_1, option_2}).
    // This page used to wait for a single combined GPT event that no longer
    // exists, so the choices never appeared.
    onFeedback: (data) => {
      setFeedback(data.text);
    },
    onNextSentence: (data) => {
      if (!isValidOptions(data?.sentence)) {
        console.error("Invalid sentence options received", data);
        showPracticeErrorToast("We couldn't load the next part of the story. Please try reading again.");
        return;
      }
      setSentenceOptions(data.sentence);
      setShowSentenceOptions(true);
    },
    onAudioFeedback: feedbackAudio.play,
    onError: () => {
      // useAudioTransport already showed the message; just reset the UI.
      setIsProcessing(false);
    },
    sessionId: session.id,
  });

  useEffect(() => {
    if (isClientExtractionEnabled) {
      initializeModels();
    }
  }, [isClientExtractionEnabled]);

  useEffect(() => {
    const getCurrentSentence = async () => {
      const state = await getCurrentSessionState(token ?? "", session.id);
      if (state.type === "full-feedback-state") {
        setCurrentSentence(state.data.sentence);
        setFeedback(state.data.gpt_response?.feedback || null);
        const options = state.data.gpt_response?.sentence;
        if (isValidOptions(options)) {
          setSentenceOptions(options);
          setShowSentenceOptions(true);
        } else {
          setSentenceOptions(null);
          setShowSentenceOptions(false);
        }
        setAnalysisData(state.data.phoneme_analysis);
        setShowHighlightedWords(true);
      } else if (state.type === "activity-settings") {
        setCurrentSentence(state.data.first_sentence);
        setFeedback(null);
        setSentenceOptions(null);
        setShowSentenceOptions(false);
      } else {
        setCurrentSentence("The quick brown fox jumped over the lazy dog");
      }
    };
    getCurrentSentence();
  }, [session.id, token]);

  const { isRecording, startRecording, stopRecording, levelRef } =
    useAudioRecorder((audioFile: File) => {
      processAudio(audioFile, currentSentence ?? "");
    });

  const displayNextSentence = (nextSentence: string) => {
    if (!nextSentence) {
      console.error("No next sentence provided");
      return;
    }
    setShowHighlightedWords(false);
    setAnalysisData(null);
    setCurrentSentence(nextSentence);
    setSentenceOptions(null);
    setFeedback(null);
    setShowSentenceOptions(false);
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
    audioLevel: levelRef,
    isModelLoading,
    modelLoadProgress,
    onStartRecording: startRecording,
    onStopRecording: stopRecording,
    onReplayFeedback: feedbackAudio.replay,
    displayNextSentence,
    sentenceOptions,
    showSentenceOptions,
  });
};

export default ChoiceStoryBasePractice;
