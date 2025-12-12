import { Button } from "@/components/ui/button";
import {
  showErrorToast,
  showNetworkError,
  showAudioError,
  showAuthError,
  showModelError,
  showAudioPlaybackError,
  showInfoToast,
  showSuccessToast,
  ErrorCategory,
} from "@/utils/errorHandling";

export default function ToastTestPage() {
  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-2xl mx-auto space-y-6">
        <h1 className="text-3xl font-bold text-foreground mb-8">
          Toast Notification Test Page
        </h1>

        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-foreground">
            Error Toasts
          </h2>
          
          <div className="grid grid-cols-2 gap-4">
            <Button
              variant="destructive"
              onClick={() => showNetworkError("Connection timeout")}
            >
              Test Network Error
            </Button>

            <Button
              variant="destructive"
              onClick={() => showAuthError("Token expired")}
            >
              Test Auth Error
            </Button>

            <Button
              variant="destructive"
              onClick={() => showAudioError("Failed to process recording")}
            >
              Test Audio Error
            </Button>

            <Button
              variant="destructive"
              onClick={() => showModelError("Model failed to load")}
            >
              Test Model Error
            </Button>

            <Button
              variant="destructive"
              onClick={() =>
                showAudioPlaybackError("Unable to play audio file")
              }
            >
              Test Playback Error
            </Button>

            <Button
              variant="destructive"
              onClick={() =>
                showErrorToast("Unknown error occurred", ErrorCategory.UNKNOWN)
              }
            >
              Test Unknown Error
            </Button>
          </div>
        </div>

        <div className="space-y-4 pt-6">
          <h2 className="text-xl font-semibold text-foreground">
            Other Toasts
          </h2>
          
          <div className="grid grid-cols-2 gap-4">
            <Button
              variant="default"
              onClick={() =>
                showSuccessToast(
                  "Success!",
                  "Your action completed successfully"
                )
              }
            >
              Test Success Toast
            </Button>

            <Button
              variant="outline"
              onClick={() =>
                showInfoToast("Information", "Here's some helpful information")
              }
            >
              Test Info Toast
            </Button>
          </div>
        </div>

        <div className="mt-8 p-4 bg-muted rounded-lg">
          <h3 className="font-semibold mb-2">Instructions:</h3>
          <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
            <li>Click any button to trigger a toast notification</li>
            <li>Toasts should appear at the top-center of the screen</li>
            <li>They should auto-dismiss after 5 seconds</li>
            <li>You can manually close them by clicking the X</li>
            <li>Multiple toasts should stack properly</li>
            <li>Check browser console for debug logs</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
