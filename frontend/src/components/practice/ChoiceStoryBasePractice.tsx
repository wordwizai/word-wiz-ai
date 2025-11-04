import { useContext, useEffect, useState } from "react";
import { useAudioRecorder } from "@/hooks/useAudioRecorder";
import { useHybridAudioAnalysis } from "@/hooks/useHybridAudioAnalysis";
import { AuthContext } from "@/contexts/AuthContext";
import { getCurrentSessionState, type Session } from "@/api";

interface SentenceOption {
  sentence: string;
  icon: string;
  action: string;
}

interface SentenceOptions {
  option_1: SentenceOption;
  option_2: SentenceOption;
}

interface ChoiceStoryBasePracticeProps {
  session: Session;
  renderContent: (props: {
    currentSentence: string | null;
    wordArray: string[];
    analysisData: {
      pronunciation_dataframe: { per: number[]; ground_truth_word: string[] };
    } | null;
    feedback: string | null;
    showHighlightedWords: boolean;
    isRecording: boolean;
    isProcessing: boolean;
    isModelLoading: boolean;
    modelLoadProgress: number;
    onStartRecording: () => void;
    onStopRecording: () => void;
    displayNextSentence: (nextSentence: string) => void;
    sentenceOptions: SentenceOptions | null;
    showSentenceOptions: boolean;
  }) => JSX.Element;
}

const ChoiceStoryBasePractice = ({
  session,
  renderContent,
}: ChoiceStoryBasePracticeProps) => {
  const [currentSentence, setCurrentSentence] = useState<string | null>(null);
  const [analysisData, setAnalysisData] = useState<{
    pronunciation_dataframe: { per: number[]; ground_truth_word: string[] };
  } | null>(null);
  const [showHighlightedWords, setShowHighlightedWords] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [sentenceOptions, setSentenceOptions] =
    useState<SentenceOptions | null>(null);
  const [showSentenceOptions, setShowSentenceOptions] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const { token } = useContext(AuthContext);

  // Initialize hybrid audio analysis
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
      console.log("Analysis:", data);
      setShowHighlightedWords(true);
      setAnalysisData(data);
    },
    onGptResponse: (data) => {
      console.log("GPT:", data);
      setSentenceOptions(data.sentence);
      setFeedback(data.feedback);
      setShowSentenceOptions(true);
    },
    onAudioFeedback: (url) => {
      const audio = new Audio(url);
      audio.play();
    },
    onError: (err) => {
      console.error("Stream error:", err);
      setIsProcessing(false);
    },
    sessionId: session.id,
  });

  // Initialize both models when component mounts (if client extraction is enabled)
  useEffect(() => {
    if (isClientExtractionEnabled) {
      initializeModels();
    }
  }, [isClientExtractionEnabled]);

  useEffect(() => {
    const getCurrentSentence = async () => {
      const fetchedSentence = await getCurrentSessionState(
        token ?? "",
        session.id
      );
      console.log("Fetched sentence:", fetchedSentence);
      if (fetchedSentence.type === "full-feedback-state") {
        setCurrentSentence(fetchedSentence.data.sentence);
        setFeedback(fetchedSentence.data.gpt_response.feedback);
        setSentenceOptions(fetchedSentence.data.gpt_response.sentence);
        setAnalysisData(fetchedSentence.data.phoneme_analysis);
        setShowSentenceOptions(true);
        setShowHighlightedWords(true);
      } else if (fetchedSentence.type === "activity-settings") {
        setCurrentSentence(fetchedSentence.data.first_sentence);
        setFeedback(null);
        setSentenceOptions(null);
        setShowSentenceOptions(false);
      } else {
        setCurrentSentence("The quick brown fox jumped over the lazy dog");
      }
    };
    getCurrentSentence();
  }, [session.id, token]);

  const { isRecording, startRecording, stopRecording } = useAudioRecorder(
    (audioFile: File) => {
      processAudio(audioFile, currentSentence ?? "");
    }
  );

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
    setIsProcessing(false); // Clear processing state when moving to next sentence
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
    isModelLoading,
    modelLoadProgress,
    onStartRecording: startRecording,
    onStopRecording: stopRecording,
    displayNextSentence,
    sentenceOptions,
    showSentenceOptions,
  });
};

export default ChoiceStoryBasePractice;
