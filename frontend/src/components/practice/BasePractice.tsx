import { useContext, useEffect, useState } from "react";
import { useAudioRecorder } from "@/hooks/useAudioRecorder";
import { useAudioAnalysisStream } from "@/hooks/useAudioAnalysisStream";
import { useIOSCompatibleAudio } from "@/hooks/useIOSCompatibleAudio";
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
  const { initializeAudioContext, playAudio } = useIOSCompatibleAudio();

  useEffect(() => {
    const getCurrentSentence = async () => {
      const fetchedSentence = await getCurrentSessionState(
        token ?? "",
        session.id,
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

  const { start } = useAudioAnalysisStream({
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
      playAudio(url);
    },
    onError: (err) => {
      console.error("Stream error:", err);
      setIsProcessing(false); // Make sure to clear processing state on error
    },
    sessionId: session.id,
  });

  const { isRecording, startRecording, stopRecording } = useAudioRecorder(
    (audioFile: File) => {
      start(audioFile, currentSentence ?? "");
    },
  );

  // Enhanced startRecording that initializes audio context for iOS compatibility
  const handleStartRecording = () => {
    // Initialize audio context during user gesture for iOS compatibility
    initializeAudioContext();
    startRecording();
  };

  const displayNextSentence = () => {
    setShowHighlightedWords(false);
    setAnalysisData(null);
    setCurrentSentence(
      nextSentence || "The quick brown fox jumped over the lazy dog",
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
    onStartRecording: handleStartRecording,
    onStopRecording: stopRecording,
    displayNextSentence,
    nextSentence,
    showNextButton,
  });
};

export default BasePractice;
