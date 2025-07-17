import { useContext, useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Home } from "lucide-react";
import { Link } from "react-router-dom";
import { useAudioRecorder } from "@/hooks/useAudioRecorder";
import { useAudioAnalysisStream } from "@/hooks/useAudioAnalysisStream";
import { FeedbackAnimatedText } from "@/components/FeedbackAnimatedText";
import { RecordAndNextButtons } from "@/components/RecordAndNextButtons";
import { getLatestSessionFeedback, type Session } from "@/api";
import WordBadgeRow from "@/components/WordBadgeRow";
import { AuthContext } from "@/contexts/AuthContext";

interface ChoiceStoryPracticeProps {
  session: Session;
}
interface SentenceOption {
  sentence: string;
  icon: string;
  action: string;
}

interface SentenceOptions {
  option_1: SentenceOption;
  option_2: SentenceOption;
}

const ChoiceStoryPractice = (props: ChoiceStoryPracticeProps) => {
  const [currentSentence, setCurrentSentence] = useState<string | null>(null);
  const [analysisData, setAnalysisData] = useState<{
    pronunciation_dataframe: { per: number[]; ground_truth_word: string[] };
  } | null>(null);
  const [showHighlightedWords, setShowHighlightedWords] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [sentenceOptions, setSentenceOptions] =
    useState<SentenceOptions | null>(null);
  const [showSentenceOptions, setShowSentenceOptions] = useState(false);
  const wordArray =
    typeof currentSentence === "string" ? currentSentence.split(" ") : [];

  const { token } = useContext(AuthContext);

  useEffect(() => {
    // Initialize with a default sentence
    const getCurrentSentence = async () => {
      // You can replace this with an API call to fetch a random sentence
      const fetchedSentence = await getLatestSessionFeedback(
        token ?? "",
        props.session.id,
      );
      console.log("Fetched sentence:", fetchedSentence);
      if (fetchedSentence) {
        setCurrentSentence(fetchedSentence.sentence);
        setFeedback(fetchedSentence.gpt_response.feedback);
        setSentenceOptions(fetchedSentence.gpt_response.sentence);
        setShowSentenceOptions(true);
      } else {
        setCurrentSentence("The quick brown fox jumped over the lazy dog");
      }
    };
    getCurrentSentence();
  }, [props.session.id, token]);

  // Analysis stream (for communicating with the backend)
  const { start } = useAudioAnalysisStream({
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
    onError: (err) => console.error("Stream error:", err),
    sessionId: props.session.id,
  });
  // Recording functionality
  const { isRecording, startRecording, stopRecording } = useAudioRecorder(
    (audioFile: File) => {
      start(audioFile, currentSentence);
    },
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
  };

  return (
    <div className="min-h-screen px-4 py-4 flex flex-col items-center gap-6">
      <div className="w-full flex justify-between items-center">
        <Link to="/dashboard">
          <Button variant="ghost" className="text-muted-foreground group">
            <Home className="size-5" />
            <span className="opacity-0 translate-x-[-16px] transition-all duration-200 group-hover:opacity-100 group-hover:translate-x-0">
              Home
            </span>
          </Button>
        </Link>
        <h1 className="scroll-m-20 text-3xl font-semibold tracking-tight first:mt-0">
          Choice Story Practice
        </h1>
        <div className="w-16" />
      </div>
      <div className="w-full flex flex-col items-center justify-center gap-6 flex-1">
        {/* Word Row */}
        <WordBadgeRow
          showHighlightedWords={showHighlightedWords}
          wordArray={wordArray}
          analysisData={analysisData}
        />
        <div className="w-full flex justify-center items-center gap-4">
          {showSentenceOptions && (
            <Button
              className="h-24 shadow-inner rounded-full hover:bg-fuchsia-200"
              variant="secondary"
              onClick={() =>
                displayNextSentence(sentenceOptions?.option_1?.sentence ?? "")
              }
            >
              <span className="text-4xl">
                {sentenceOptions?.option_1?.icon}
              </span>
              <span className="text-lg">
                {sentenceOptions?.option_1?.action}
              </span>
            </Button>
          )}
          {/* Recording Button */}
          <RecordAndNextButtons
            isRecording={isRecording}
            onStartRecording={startRecording}
            onStopRecording={stopRecording}
          />
          {showSentenceOptions && (
            <Button
              className="h-24 shadow-inner rounded-full hover:bg-fuchsia-200"
              variant="secondary"
              onClick={() =>
                displayNextSentence(sentenceOptions?.option_2?.sentence ?? "")
              }
            >
              <span className="text-4xl">
                {sentenceOptions?.option_2?.icon}
              </span>
              <span className="text-lg">
                {sentenceOptions?.option_2?.action}
              </span>
            </Button>
          )}
        </div>
      </div>
      {/* Feedback text */}
      <FeedbackAnimatedText feedback={feedback} />
    </div>
  );
};

export default ChoiceStoryPractice;
