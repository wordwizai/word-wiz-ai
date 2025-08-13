import { useState } from "react";
import { RecordAndNextButtons } from "@/components/RecordAndNextButtons";
import { Button } from "@/components/ui/button";

export const SpeakerButtonDemo = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [showNextButton, setShowNextButton] = useState(false);

  const handleStartRecording = () => {
    setIsRecording(true);
  };

  const handleStopRecording = () => {
    setIsRecording(false);
    setIsProcessing(true);
  };

  const handleNext = () => {
    setShowNextButton(false);
    setIsProcessing(false);
    setIsRecording(false);
  };

  const resetDemo = () => {
    setIsRecording(false);
    setIsProcessing(false);
    setShowNextButton(false);
  };

  const triggerProcessing = () => {
    setIsRecording(false);
    setIsProcessing(true);
  };

  const triggerComplete = () => {
    setIsProcessing(false);
    setShowNextButton(true);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-accent/5 flex flex-col items-center justify-center gap-8 p-8">
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-primary via-purple-600 to-pink-600 bg-clip-text text-transparent">
          Speaker Button Demo
        </h1>
        <p className="text-lg text-muted-foreground max-w-2xl">
          This demo showcases the enhanced speaker button with three states:
          idle (microphone), recording (ellipsis with pulse), and processing (spinner with progress bar).
        </p>
      </div>

      <div className="rounded-3xl bg-gradient-to-br from-white to-purple-50/50 border-2 border-purple-100/50 shadow-xl p-8 w-full max-w-2xl">
        <div className="text-center space-y-6">
          <h2 className="text-2xl font-semibold text-foreground">
            Practice Reading: "The quick brown fox jumps over the lazy dog"
          </h2>

          <div className="py-8">
            <RecordAndNextButtons
              isRecording={isRecording}
              isProcessing={isProcessing}
              onStartRecording={handleStartRecording}
              onStopRecording={handleStopRecording}
              showNextButton={showNextButton}
              onNext={handleNext}
            />
          </div>

          <div className="space-y-4">
            <div className="text-sm text-muted-foreground">
              Current State: 
              {isRecording && <span className="text-fuchsia-700 font-medium"> Recording...</span>}
              {isProcessing && <span className="text-purple-700 font-medium"> Processing...</span>}
              {!isRecording && !isProcessing && <span className="text-gray-700 font-medium"> Idle</span>}
            </div>
            
            <div className="flex gap-2 flex-wrap justify-center">
              <Button
                onClick={() => setIsRecording(true)}
                variant="outline"
                size="sm"
                disabled={isRecording}
              >
                Start Recording
              </Button>
              <Button
                onClick={triggerProcessing}
                variant="outline"
                size="sm"
                disabled={!isRecording}
              >
                Trigger Processing
              </Button>
              <Button
                onClick={triggerComplete}
                variant="outline"
                size="sm"
                disabled={!isProcessing}
              >
                Complete Processing
              </Button>
              <Button
                onClick={resetDemo}
                variant="outline"
                size="sm"
              >
                Reset Demo
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="text-center space-y-2 text-sm text-muted-foreground max-w-lg">
        <p>
          <strong>Instructions:</strong> Use the manual control buttons above to demonstrate each state 
          of the speaker button, or click the microphone directly to start recording.
        </p>
      </div>
    </div>
  );
};