import { useContext, useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Mic, Home, Ellipsis } from "lucide-react";
import { Link } from "react-router-dom";
import { sendAudioRecording } from "@/api";
import { AuthContext } from "@/contexts/AuthContext";
// import {
//   MediaRecorder as ExtendedMediaRecorder,
//   register,
// } from "extendable-media-recorder";
// import { connect as connectWav } from "extendable-media-recorder-wav-encoder";
import { useAudioRecorder } from "@/hooks/useAudioRecorder";

const UnlimitedPractice = () => {
  const [currentSentence, setCurrentSentence] = useState(
    "The quick brown fox jumped over the lazy dog",
  );
  const [aiResponse, setAIResponse] = useState(null);
  const wordArray = currentSentence.split(" ");
  const { token } = useContext(AuthContext);
  const onFinish = async (audioFile: File) => {
    try {
      const response = await sendAudioRecording(
        audioFile,
        currentSentence,
        token,
      );
      console.log(response);
      setCurrentSentence(response.response.sentence);
      setAIResponse(response);
    } catch (error) {
      console.error(error);
    }
  };
  const { isRecording, startRecording, stopRecording } =
    useAudioRecorder(onFinish);

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
          {wordArray.map((word, idx) => (
            <Badge
              key={idx}
              variant="outline"
              className="rounded-xl px-4 py-2 text-4xl font-medium"
            >
              {word}
            </Badge>
          ))}
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
        <div className="flex "> {aiResponse?.response.feedback}</div>
      </div>
    </div>
  );
};

export default UnlimitedPractice;
