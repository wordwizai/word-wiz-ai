import { useContext, useEffect, useState } from "react";
import { useAudioRecorder } from "@/hooks/useAudioRecorder";
import { useHybridAudioAnalysis } from "@/hooks/useHybridAudioAnalysis";
import { AuthContext } from "@/contexts/AuthContext";
import { getCurrentSessionState, type Session } from "@/api";

interface BasePracticeProps {
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
    displayNextSentence: () => void;
    nextSentence: string | null;
    showNextButton: boolean;
  }) => JSX.Element;
}

const BasePractice = ({ session, renderContent }: BasePracticeProps) => {
  const [currentSentence, setCurrentSentence] = useState<string | null>(null);
  const [analysisData, setAnalysisData] = useState<{
    pronunciation_dataframe: { per: number[]; ground_truth_word: string[] };
  } | null>(null);
  const [showHighlightedWords, setShowHighlightedWords] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [nextSentence, setNextSentence] = useState<string | null>(null);
  const [showNextButton, setShowNextButton] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const { token } = useContext(AuthContext);

  // Initialize hybrid audio analysis
  const {
    processAudio,
    initializeModel,
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
    onGptResponse: (data) => {
      setNextSentence(data.sentence);
      setFeedback(data.feedback);
      setTimeout(() => {
        setShowNextButton(true);
      }, 1000);
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

  // Initialize the phoneme model when component mounts (if client extraction is enabled)
  useEffect(() => {
    if (isClientExtractionEnabled) {
      initializeModel();
    }
  }, [isClientExtractionEnabled]);

  useEffect(() => {
    const getCurrentSentence = async () => {
      const fetchedSentence = await getCurrentSessionState(
        token ?? "",
        session.id
      );
      if (fetchedSentence.type === "full-feedback-state") {
        setCurrentSentence(fetchedSentence.data.gpt_response.sentence);
      } else if (session.activity.activity_settings?.first_sentence) {
        setCurrentSentence(session.activity.activity_settings?.first_sentence);
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

  const displayNextSentence = () => {
    setShowHighlightedWords(false);
    setAnalysisData(null);
    setCurrentSentence(
      nextSentence || "The quick brown fox jumped over the lazy dog"
    );
    setNextSentence(null);
    setFeedback(null);
    setShowNextButton(false);
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
    nextSentence,
    showNextButton,
  });
};

export default BasePractice;
