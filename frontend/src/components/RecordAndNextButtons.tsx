import { Button } from "@/components/ui/button";
import { Mic, Ellipsis, SkipForward, Loader2 } from "lucide-react";

interface RecordAndNextButtonsProps {
  isRecording: boolean;
  isProcessing?: boolean;
  onStartRecording: () => void;
  onStopRecording: () => void;
  showNextButton?: boolean;
  onNext?: () => void;
}

export const RecordAndNextButtons = ({
  isRecording,
  isProcessing = false,
  onStartRecording,
  onStopRecording,
  showNextButton = false,
  onNext = () => {
    console.warn("Next button clicked, but no handler provided");
  },
}: RecordAndNextButtonsProps) => {
  const renderRecordButton = () => {
    if (isProcessing) {
      // Processing state: show spinner with status text
      return (
        <Button
          className="w-24 h-24 shadow-inner transition-colors rounded-full bg-gradient-to-br from-purple-200 to-fuchsia-200 hover:from-purple-300 hover:to-fuchsia-300 cursor-default"
          variant="secondary"
          disabled
        >
          <Loader2 className="size-10 text-purple-700 animate-spin" />
        </Button>
      );
    }

    if (isRecording) {
      // Recording state: show ellipsis with pulse animation
      return (
        <Button
          className="w-24 h-24 animate-pulse shadow-inner transition-colors rounded-full bg-fuchsia-200 hover:bg-fuchsia-300"
          variant="secondary"
          onClick={onStopRecording}
        >
          <Ellipsis className="size-10 text-purple-700" />
        </Button>
      );
    }

    // Idle state: show microphone icon with inviting ring
    return (
      <div className="relative flex items-center justify-center">
        {/* Animated outer ring */}
        <span className="absolute w-32 h-32 rounded-full bg-primary/10 animate-ping" style={{ animationDuration: "2s" }} />
        <Button
          className="relative w-24 h-24 shadow-inner transition-all duration-300 rounded-full bg-gradient-to-br from-primary/10 to-purple-100 hover:from-primary/20 hover:to-fuchsia-200 hover:scale-105 hover:shadow-lg border-2 border-primary/20"
          variant="secondary"
          onClick={onStartRecording}
        >
          <Mic className="size-10 text-purple-700" />
        </Button>
      </div>
    );
  };

  const getLabel = () => {
    if (isProcessing) return "Analyzing...";
    if (isRecording) return "Tap to stop";
    return "Tap to record";
  };

  return (
    <div className="flex flex-col items-center gap-3">
      <div className="flex justify-center items-center gap-4">
        {renderRecordButton()}
        {showNextButton && (
          <Button
            variant="outline"
            onClick={onNext}
            className="w-24 h-24 shadow-inner rounded-full hover:scale-105 transition-all duration-300"
          >
            <SkipForward className="size-10" />
          </Button>
        )}
      </div>
      <span className="text-xs font-medium text-muted-foreground tracking-wide">
        {getLabel()}
      </span>
    </div>
  );
};
