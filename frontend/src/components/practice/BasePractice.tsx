import { useContext, useEffect, useRef, useState, type ReactElement } from "react";
import { useAudioRecorder } from "@/hooks/useAudioRecorder";
import { useHybridAudioAnalysis } from "@/hooks/useHybridAudioAnalysis";
import { useFeedbackAudio } from "@/hooks/useFeedbackAudio";
import { AuthContext } from "@/contexts/AuthContext";
import { getCurrentSessionState, type Session } from "@/api";
import { showPracticeErrorToast } from "@/utils/errorHandling";
import type { SessionResult } from "@/lib/phonics";
import type { PracticeStageState, PronunciationAnalysis } from "./types";

export interface BasePracticeRenderProps extends PracticeStageState {
  currentSentence: string | null;
  isModelLoading: boolean;
  modelLoadProgress: number;
  displayNextSentence: () => void;
  nextSentence: string | null;
  showNextButton: boolean;
  // Phonics pattern sessions only: where the child is, the score once the
  // last line is read, and whether they've moved on to the finish screen.
  lineInfo: LineInfo | null;
  sessionResult: SessionResult | null;
  finished: boolean;
}

export interface LineInfo {
  index: number;
  count: number;
}

interface BasePracticeProps {
  session: Session;
  renderContent: (props: BasePracticeRenderProps) => ReactElement;
}

const FALLBACK_SENTENCE = "The quick brown fox jumped over the lazy dog";
const NEXT_AUDIO_WAIT_MS = 5000;

const BasePractice = ({ session, renderContent }: BasePracticeProps) => {
  const [currentSentence, setCurrentSentence] = useState<string | null>(null);
  const [analysisData, setAnalysisData] =
    useState<PronunciationAnalysis | null>(null);
  const [showHighlightedWords, setShowHighlightedWords] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [nextSentence, setNextSentence] = useState<string | null>(null);
  const [showNextButton, setShowNextButton] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  // A feedback clip that lands after the child taps Next belongs to a line they've left.
  const acceptAudio = useRef(true);
  const audioArrived = useRef(false);
  const [lineInfo, setLineInfo] = useState<LineInfo | null>(null);
  const [nextLineInfo, setNextLineInfo] = useState<LineInfo | null>(null);
  const [sessionResult, setSessionResult] = useState<SessionResult | null>(null);
  const [finished, setFinished] = useState(false);
  const { token } = useContext(AuthContext);
  const feedbackAudio = useFeedbackAudio();

  // Offer Next once this reading's spoken feedback has arrived, so a quick
  // tap can't skip it. Pattern sessions make no GPT call, so their next line
  // usually lands before the clip. Give up waiting after a few seconds in
  // case TTS failed.
  const revealNextWhenHeard = () => {
    const started = Date.now();
    const check = () => {
      if (audioArrived.current || Date.now() - started >= NEXT_AUDIO_WAIT_MS) {
        setShowNextButton(true);
      } else {
        setTimeout(check, 200);
      }
    };
    setTimeout(check, 1000);
  };

  const {
    processAudio,
    initializeModels,
    isModelLoading,
    modelLoadProgress,
    isClientExtractionEnabled,
  } = useHybridAudioAnalysis({
    onProcessingStart: () => {
      acceptAudio.current = true;
      audioArrived.current = false;
      setIsProcessing(true);
      // The old feedback belongs to the last attempt. Clearing it here also
      // stops PracticeStage pairing this attempt's analysis with that text.
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
      setNextLineInfo(
        data.line_index !== undefined && data.line_count !== undefined
          ? { index: data.line_index, count: data.line_count }
          : null
      );
      revealNextWhenHeard();
    },
    onSessionComplete: (result) => {
      // The last line of a pattern session. The arrow now leads to the
      // finish screen instead of another sentence.
      setSessionResult(result);
      revealNextWhenHeard();
    },
    onAudioFeedback: (url) => {
      if (acceptAudio.current) {
        audioArrived.current = true;
        feedbackAudio.play(url);
      } else URL.revokeObjectURL(url);
    },
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
        if (state.line_count !== undefined) {
          setLineInfo({ index: state.line_index ?? 0, count: state.line_count });
        }
        if (state.type === "full-feedback-state") {
          setCurrentSentence(state.data.gpt_response.sentence);
        } else if (state.data?.first_sentence) {
          // The activity's settings, or a pattern session's first line.
          setCurrentSentence(state.data.first_sentence);
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
    acceptAudio.current = false;
    if (sessionResult) {
      feedbackAudio.reset();
      setFinished(true);
      return;
    }
    if (nextLineInfo) setLineInfo(nextLineInfo);
    setNextLineInfo(null);
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
    lineInfo,
    sessionResult,
    finished,
  });
};

export default BasePractice;
