import { useState, useCallback, useEffect, useRef } from "react";
import wordExtractor from "@/services/wordExtractor";

export interface UseWordModelReturn {
  isSupported: boolean;
  isLoading: boolean;
  isReady: boolean;
  loadProgress: number;
  error: string | null;
  shouldFallbackToServer: boolean;
  loadModel: () => Promise<void>;
  extractWords: (audio: Blob) => Promise<string[] | null>;
  unloadModel: () => void;
}

/**
 * React hook for managing the client-side word extraction model.
 * Handles model loading, extraction, and error states.
 * Runs in parallel with phoneme model for complete client-side processing.
 */
export function useWordModel(): UseWordModelReturn {
  const [isSupported, setIsSupported] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [isReady, setIsReady] = useState(false);
  const [loadProgress, setLoadProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [shouldFallbackToServer, setShouldFallbackToServer] = useState(false);

  // Track if component is mounted to prevent state updates after unmount
  const isMountedRef = useRef(true);

  useEffect(() => {
    // Check browser support on mount
    const checkSupport = async () => {
      const capabilities = wordExtractor.getDeviceCapabilities();

      if (isMountedRef.current) {
        setIsSupported(capabilities.canRunModel);

        if (!capabilities.canRunModel) {
          setError(
            capabilities.warningMessage ||
              "Device cannot run word extraction model"
          );
          setShouldFallbackToServer(true);
        }

        // Check if model is already loaded
        if (wordExtractor.isModelLoaded()) {
          setIsReady(true);
          setLoadProgress(100);
        }
      }
    };

    checkSupport();

    // Cleanup on unmount
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  /**
   * Load the word extraction model.
   */
  const loadModel = useCallback(async () => {
    if (!isSupported) {
      setError("Device not supported for word extraction");
      setShouldFallbackToServer(true);
      return;
    }

    if (isReady || isLoading) {
      console.log("Word model already loaded or loading");
      return;
    }

    console.log("🚀 Starting word model load...");
    setIsLoading(true);
    setError(null);
    setLoadProgress(0);

    try {
      await wordExtractor.loadModel((progress) => {
        if (isMountedRef.current) {
          setLoadProgress(progress);
        }
      });

      console.log("✅ Word model load completed, updating state...");

      if (isMountedRef.current) {
        setIsReady(true);
        setIsLoading(false);
        setLoadProgress(100);
        setShouldFallbackToServer(false);
        console.log("✅ Word model ready: isReady=true");
      }
    } catch (err) {
      console.error("Failed to load word model:", err);

      if (isMountedRef.current) {
        const errorMessage =
          err instanceof Error ? err.message : "Failed to load word model";
        setError(errorMessage);
        setIsLoading(false);
        setIsReady(false);
        setShouldFallbackToServer(true);
      }
    }
  }, [isSupported, isReady, isLoading]);

  /**
   * Extract words from audio blob.
   * Returns null if extraction fails (caller should fallback to server).
   */
  const extractWords = useCallback(
    async (audio: Blob): Promise<string[] | null> => {
      // Check if model is actually loaded (not relying on React state to avoid timing issues)
      if (!wordExtractor.isModelLoaded()) {
        console.warn("Word model not loaded, cannot extract words");
        setShouldFallbackToServer(true);
        return null;
      }

      try {
        const words = await wordExtractor.extractWords(audio);

        // Reset fallback flag on successful extraction
        if (isMountedRef.current) {
          setShouldFallbackToServer(false);
        }

        return words;
      } catch (err) {
        console.error("Word extraction failed:", err);

        if (isMountedRef.current) {
          const errorMessage =
            err instanceof Error ? err.message : "Word extraction failed";
          setError(errorMessage);
          setShouldFallbackToServer(true);
        }

        return null;
      }
    },
    [isReady]
  );

  /**
   * Unload the model and free memory.
   */
  const unloadModel = useCallback(() => {
    wordExtractor.unloadModel();

    if (isMountedRef.current) {
      setIsReady(false);
      setLoadProgress(0);
      setError(null);
    }
  }, []);

  return {
    isSupported,
    isLoading,
    isReady,
    loadProgress,
    error,
    shouldFallbackToServer,
    loadModel,
    extractWords,
    unloadModel,
  };
}
