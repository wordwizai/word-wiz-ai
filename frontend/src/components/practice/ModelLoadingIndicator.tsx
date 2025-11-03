import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2, Download, AlertCircle } from "lucide-react";

interface ModelLoadingIndicatorProps {
  isLoading: boolean;
  progress: number;
  error?: string | null;
}

/**
 * Component to display model loading progress with user-friendly messages.
 */
export const ModelLoadingIndicator = ({
  isLoading,
  progress,
  error,
}: ModelLoadingIndicatorProps) => {
  if (!isLoading && !error) {
    return null;
  }

  if (error) {
    return (
      <Alert variant="destructive" className="mb-4">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          <strong>Model Load Failed:</strong> {error}
          <br />
          <span className="text-sm mt-1 block">
            Falling back to server processing. You can continue using the app
            normally.
          </span>
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <Alert className="mb-4">
      <Download className="h-4 w-4 animate-pulse" />
      <AlertDescription>
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="font-medium">
              {progress < 10 && "Initializing AI model..."}
              {progress >= 10 &&
                progress < 50 &&
                "Downloading model (~250MB)..."}
              {progress >= 50 && progress < 90 && "Loading model..."}
              {progress >= 90 && "Almost ready..."}
            </span>
            <span className="text-sm text-muted-foreground">
              {progress.toFixed(0)}%
            </span>
          </div>
          <Progress value={progress} className="h-2" />
          <p className="text-xs text-muted-foreground">
            This is a one-time download. The model will be cached for future
            sessions.
          </p>
        </div>
      </AlertDescription>
    </Alert>
  );
};

interface ProcessingIndicatorProps {
  isProcessing: boolean;
  isUsingClientExtraction?: boolean;
}

/**
 * Component to show processing status during audio analysis.
 */
export const ProcessingIndicator = ({
  isProcessing,
  isUsingClientExtraction = false,
}: ProcessingIndicatorProps) => {
  if (!isProcessing) {
    return null;
  }

  return (
    <div className="flex items-center gap-2 text-sm text-muted-foreground">
      <Loader2 className="h-4 w-4 animate-spin" />
      <span>
        {isUsingClientExtraction
          ? "Processing locally..."
          : "Processing on server..."}
      </span>
    </div>
  );
};

interface ModelStatusBannerProps {
  shouldRecommendDisabling: boolean;
  warningMessage?: string;
  onDisable?: () => void;
}

/**
 * Banner to suggest disabling client processing on slow devices.
 */
export const ModelStatusBanner = ({
  shouldRecommendDisabling,
  warningMessage,
  onDisable,
}: ModelStatusBannerProps) => {
  if (!shouldRecommendDisabling) {
    return null;
  }

  return (
    <Alert
      variant="default"
      className="mb-4 border-yellow-500/50 bg-yellow-50 dark:bg-yellow-950/20"
    >
      <AlertCircle className="h-4 w-4 text-yellow-600 dark:text-yellow-500" />
      <AlertDescription>
        <div className="space-y-2">
          <p className="text-sm">
            {warningMessage ||
              "Your device may experience slower performance with client-side processing."}
          </p>
          {onDisable && (
            <button
              onClick={onDisable}
              className="text-sm font-medium text-yellow-700 dark:text-yellow-400 hover:underline"
            >
              Switch to server processing →
            </button>
          )}
        </div>
      </AlertDescription>
    </Alert>
  );
};
