import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Home } from "lucide-react";
import { Link } from "react-router-dom";
import { useAudioRecorder } from "@/hooks/useAudioRecorder";
import { useAudioAnalysisStream } from "@/hooks/useAudioAnalysisStream";
import { WordBadge } from "@/components/WordBadge";
import { FeedbackAnimatedText } from "@/components/FeedbackAnimatedText";
import { RecordAndNextButtons } from "@/components/RecordAndNextButtons";
import type { Session } from "@/api";

interface UnlimitedPracticeProps {
  session: Session;
}

const UnlimitedPractice = (props: UnlimitedPracticeProps) => {
  const [currentSentence, setCurrentSentence] = useState(
    "The quick brown fox jumped over the lazy dog",
  );
  const [analysisData, setAnalysisData] = useState<{
    pronunciation_dataframe: { per: number[]; ground_truth_word: string[] };
  } | null>(null);
  const [showHighlightedWords, setShowHighlightedWords] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [nextSentence, setNextSentence] = useState<string | null>(null);
  const [showNextButton, setShowNextButton] = useState(false);
  const wordArray = currentSentence.split(" ");

  // Analysis stream (for communicating with the backend)
  const { start } = useAudioAnalysisStream({
    onAnalysis: (data) => {
      console.log("Analysis:", data);
      setShowHighlightedWords(true);
      setAnalysisData(data);
    },
    onGptResponse: (data) => {
      console.log("GPT:", data);
      setNextSentence(data.sentence);
      setFeedback(data.feedback);
    },
    onAudioFeedback: (url) => {
      const audio = new Audio(url);
      audio.play();
      setTimeout(() => {
        setShowNextButton(true);
      }, 1000);
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

  const displayNextSentence = () => {
    setShowHighlightedWords(false);
    setAnalysisData(null);
    setCurrentSentence(
      nextSentence || "The quick brown fox jumped over the lazy dog",
    );
    setNextSentence(null);
    setFeedback(null);
    setShowNextButton(false);
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
          Unlimited Practice
        </h1>
        <div className="w-16" />
      </div>
      <div className="w-full flex flex-col items-center justify-center gap-6 flex-1">
        <motion.div
          className="flex flex-row items-center justify-center gap-4 w-full flex-wrap max-w-2/3"
          layout
        >
          <AnimatePresence>
            {wordArray.map((word, idx) => {
              return (
                <WordBadge
                  word={word}
                  idx={idx}
                  showHighlighted={showHighlightedWords}
                  analysisPer={
                    analysisData?.pronunciation_dataframe.per[
                      Object.values(
                        analysisData?.pronunciation_dataframe
                          .ground_truth_word || [],
                      ).indexOf(word)
                    ]
                  }
                  key={word + idx}
                />
              );
            })}
          </AnimatePresence>
        </motion.div>
        {/* Recording Button */}
        <RecordAndNextButtons
          isRecording={isRecording}
          onStartRecording={startRecording}
          onStopRecording={stopRecording}
          showNextButton={showNextButton}
          onNext={displayNextSentence}
        />
      </div>
      {/* Feedback text */}
      <FeedbackAnimatedText feedback={feedback} />
    </div>
  );
};

export default UnlimitedPractice;
