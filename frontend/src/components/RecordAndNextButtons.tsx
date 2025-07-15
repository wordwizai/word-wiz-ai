import { Button } from "@/components/ui/button";
import { Mic, Ellipsis, SkipForward } from "lucide-react";

interface RecordAndNextButtonsProps {
  isRecording: boolean;
  onStartRecording: () => void;
  onStopRecording: () => void;
  showNextButton?: boolean;
  onNext?: () => void;
}

export const RecordAndNextButtons = ({
  isRecording,
  onStartRecording,
  onStopRecording,
  showNextButton = false,
  onNext = () => {
    console.warn("Next button clicked, but no handler provided");
  },
}: RecordAndNextButtonsProps) => (
  <div className="flex justify-center items-center gap-4">
    {isRecording ? (
      <Button
        className="w-24 h-24 not-hover:animate-pulse shadow-inner transition-colors rounded-full bg-fuchsia-200 hover:bg-fuchsia-300"
        variant="secondary"
        onClick={onStopRecording}
      >
        <Ellipsis className="size-10 text-purple-700" />
      </Button>
    ) : (
      <Button
        className="w-24 h-24 not-hover:animate-pulse shadow-inner transition-colors rounded-full hover:bg-fuchsia-200"
        variant="secondary"
        onClick={onStartRecording}
      >
        <Mic className="size-10 text-purple-700" />
      </Button>
    )}
    {showNextButton && (
      <Button
        variant="outline"
        onClick={onNext}
        className="w-24 h-24 shadow-inner rounded-full"
      >
        <SkipForward className="size-10" />
      </Button>
    )}
  </div>
);
