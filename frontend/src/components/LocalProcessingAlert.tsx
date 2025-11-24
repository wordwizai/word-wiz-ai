import { useState, useEffect } from "react";
import { X, Zap, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { checkDeviceCapabilities } from "@/utils/deviceCapabilities";
import { useSettings } from "@/contexts/SettingsContext";

const LOCAL_PROCESSING_ALERT_DISMISSED_KEY = "local_processing_alert_dismissed";

export const LocalProcessingAlert = () => {
  const [isVisible, setIsVisible] = useState(false);
  const [isEnabling, setIsEnabling] = useState(false);
  const { settings, updateSettings } = useSettings();

  useEffect(() => {
    // Check if alert was already dismissed
    const dismissed = localStorage.getItem(LOCAL_PROCESSING_ALERT_DISMISSED_KEY);
    if (dismissed === "true") {
      return;
    }

    // Check if user already has local processing enabled
    if (settings?.use_client_phoneme_extraction === true) {
      return;
    }

    // Check if device is capable
    const capabilities = checkDeviceCapabilities();
    if (capabilities.canRunModel && !capabilities.shouldRecommendDisabling) {
      setIsVisible(true);
    }
  }, [settings]);

  const handleDismiss = () => {
    localStorage.setItem(LOCAL_PROCESSING_ALERT_DISMISSED_KEY, "true");
    setIsVisible(false);
  };

  const handleEnableLocalProcessing = async () => {
    setIsEnabling(true);
    try {
      await updateSettings({ use_client_phoneme_extraction: true });
      // Reload the page to apply the setting
      window.location.reload();
    } catch (error) {
      console.error("Failed to enable local processing:", error);
      setIsEnabling(false);
    }
  };

  if (!isVisible) {
    return null;
  }

  return (
    <div className="fixed top-4 right-4 z-50 w-96 max-w-[calc(100vw-2rem)] animate-in slide-in-from-top-5 duration-300">
      <div className="rounded-2xl bg-gradient-to-br from-green-50 to-emerald-50/50 dark:from-green-950/50 dark:to-emerald-950/30 border-2 border-green-200/50 dark:border-green-800/50 shadow-xl backdrop-blur-sm p-4">
        <div className="flex items-start gap-3">
          <div className="p-2 bg-gradient-to-r from-green-400 to-emerald-500 rounded-xl shrink-0">
            <Zap className="w-5 h-5 text-white" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2 mb-1">
              <h3 className="text-sm font-semibold text-foreground">
                Try Local Processing (Beta)
              </h3>
              <button
                onClick={handleDismiss}
                className="p-1 hover:bg-green-100/50 dark:hover:bg-green-900/50 rounded-lg transition-colors shrink-0"
                aria-label="Dismiss alert"
              >
                <X className="w-4 h-4 text-muted-foreground" />
              </button>
            </div>
            <p className="text-xs text-muted-foreground mb-3 leading-relaxed">
              Your device has good specs! Enable local processing for much quicker results.
            </p>
            <Button
              onClick={handleEnableLocalProcessing}
              disabled={isEnabling}
              className="w-full bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white font-semibold py-2 px-4 rounded-xl transition-all duration-200 hover:scale-[1.02] hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
              size="sm"
            >
              {isEnabling ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Enabling...
                </>
              ) : (
                <>
                  <Zap className="w-4 h-4 mr-2" />
                  Enable & Reload
                </>
              )}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};
