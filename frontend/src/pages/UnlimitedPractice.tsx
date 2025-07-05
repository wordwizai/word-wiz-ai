import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Mic, Home, Ellipsis } from "lucide-react";
import { Link } from "react-router-dom";
import { useAudioRecorder } from "@/hooks/useAudioRecorder";
import { useAudioAnalysisStream } from "@/hooks/useAudioAnalysisStream";

const UnlimitedPractice = () => {
  const [currentSentence, setCurrentSentence] = useState(
    "The quick brown fox jumped over the lazy dog",
  );
  const [analysisData, setAnalysisData] = useState<any>(null);
  const [showHighlightedWords, setShowHighlightedWords] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);
  const wordArray = currentSentence.split(" ");
  const { start, stop } = useAudioAnalysisStream({
    onAnalysis: (data) => {
      console.log("Analysis:", data);
      setShowHighlightedWords(true);
      setAnalysisData(data);
    },
    onGptResponse: (data) => {
      console.log("GPT:", data);
      setShowHighlightedWords(false);
      setCurrentSentence(data.sentence);
      setFeedback(data.feedback);
    },
    onAudioFeedback: (url) => {
      const audio = new Audio(url);
      audio.play();
    },
    onError: (err) => console.error("Stream error:", err),
  });
  const { isRecording, startRecording, stopRecording } = useAudioRecorder(
    (audioFile: File) => {
      start(audioFile, currentSentence);
    },
  );

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
        <div className="flex flex-row items-center justify-center gap-4 w-full flex-wrap max-w-2/3">
          {wordArray.map((word, idx) => {
            let textClass = "rounded-xl px-4 py-2 text-4xl font-medium";
            let style = undefined;
            if (analysisData !== null && showHighlightedWords) {
              const per = analysisData.pronunciation_dataframe.per[idx];
              const p = Math.max(0, Math.min(1, per));
              let r, g, b;
              if (p < 0.5) {
                // Green to Yellow
                r = Math.round(2 * 255 * p);
                g = 255;
              } else {
                // Yellow to Red
                r = 255;
                g = Math.round(255 * (1 - 2 * (p - 0.5)));
              }
              b = 100; // No blue component
              style = { backgroundColor: `rgb(${r},${g},${b})` };
              textClass += p > 0.5 ? " text-white" : " text-black";
            }
            return (
              <Badge
                key={idx}
                variant="outline"
                className={textClass}
                style={style}
              >
                {word}
              </Badge>
            );
          })}
        </div>
        <div className="flex justify-center">
          {isRecording ? (
            <Button
              className="w-24 h-24 not-hover:animate-pulse shadow-inner transition-colors rounded-full bg-fuchsia-200 hover:bg-fuchsia-300"
              variant="secondary"
              onClick={stopRecording}
            >
              <Ellipsis className="size-10 text-purple-700" />
            </Button>
          ) : (
            <Button
              className="w-24 h-24 not-hover:animate-pulse shadow-inner transition-colors rounded-full hover:bg-fuchsia-200"
              variant="secondary"
              onClick={startRecording}
            >
              <Mic className="size-10 text-purple-700" />
            </Button>
          )}
        </div>
        {/* Feedback text */}
        <div className="flex "> {feedback}</div>
      </div>
    </div>
  );
};

export default UnlimitedPractice;
