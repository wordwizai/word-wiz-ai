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
        <div className="flex flex-col items-center gap-2">
          <Button
            className="w-24 h-24 shadow-inner transition-colors rounded-full bg-gradient-to-br from-purple-200 to-fuchsia-200 hover:from-purple-300 hover:to-fuchsia-300 cursor-default"
            variant="secondary"
            disabled
          >
            <Loader2 className="size-10 text-purple-700 animate-spin" />
          </Button>
          <div className="flex flex-col items-center gap-1">
            <div className="text-sm font-medium text-purple-700">Processing...</div>
            <div className="w-32 h-1 bg-purple-200 rounded-full overflow-hidden">
              <div className="h-full bg-gradient-to-r from-purple-500 to-fuchsia-500 rounded-full animate-pulse"></div>
            </div>
          </div>
        </div>
      );
    }

    if (isRecording) {
      // Recording state: show ellipsis with pulse animation
      return (
        <div className="flex flex-col items-center gap-2">
          <Button
            className="w-24 h-24 animate-pulse shadow-inner transition-colors rounded-full bg-fuchsia-200 hover:bg-fuchsia-300"
            variant="secondary"
            onClick={onStopRecording}
          >
            <Ellipsis className="size-10 text-purple-700" />
          </Button>
          <div className="text-sm font-medium text-fuchsia-700">Recording...</div>
        </div>
      );
    }

    // Idle state: show microphone icon
    return (
      <Button
        className="w-24 h-24 shadow-inner transition-all duration-300 rounded-full hover:bg-fuchsia-200 hover:scale-105 hover:shadow-lg"
        variant="secondary"
        onClick={onStartRecording}
      >
        <Mic className="size-10 text-purple-700" />
      </Button>
    );
  };

  return (
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
  );
};
