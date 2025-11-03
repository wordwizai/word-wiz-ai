import { useState, useCallback, useEffect, useRef } from "react";
import phonemeExtractor from "@/services/phonemeExtractor";

export interface UsePhonemeModelReturn {
  isSupported: boolean;
  isLoading: boolean;
  isReady: boolean;
  loadProgress: number;
  error: string | null;
  shouldFallbackToServer: boolean;
  loadModel: () => Promise<void>;
  extractPhonemes: (audio: Blob) => Promise<string[][] | null>;
  unloadModel: () => void;
}

/**
 * React hook for managing the client-side phoneme extraction model.
 * Handles model loading, extraction, and error states.
 */
export function usePhonemeModel(): UsePhonemeModelReturn {
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
      const browserSupported = phonemeExtractor.checkBrowserSupport();
      const resourcesOk = await phonemeExtractor.checkDeviceResources();

      if (isMountedRef.current) {
        setIsSupported(browserSupported && resourcesOk);

        if (!browserSupported) {
          setError("Your browser doesn't support client-side processing");
          setShouldFallbackToServer(true);
        } else if (!resourcesOk) {
          setError(
            "Device resources may be insufficient for client processing"
          );
          setShouldFallbackToServer(true);
        }

        // Check if model is already loaded
        if (phonemeExtractor.isModelLoaded()) {
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
   * Load the phoneme extraction model.
   */
  const loadModel = useCallback(async () => {
    if (!isSupported) {
      setError("Browser or device not supported");
      setShouldFallbackToServer(true);
      return;
    }

    if (isReady || isLoading) {
      console.log("Model already loaded or loading");
      return;
    }

    console.log("🚀 Starting model load...");
    setIsLoading(true);
    setError(null);
    setLoadProgress(0);

    try {
      await phonemeExtractor.loadModel((progress) => {
        if (isMountedRef.current) {
          setLoadProgress(progress);
        }
      });

      console.log("✅ Model load completed, updating state...");

      if (isMountedRef.current) {
        setIsReady(true);
        setIsLoading(false);
        setLoadProgress(100);
        setShouldFallbackToServer(false);
        console.log("✅ State updated: isReady=true");
      }
    } catch (err) {
      console.error("Failed to load model:", err);

      if (isMountedRef.current) {
        const errorMessage =
          err instanceof Error ? err.message : "Failed to load model";
        setError(errorMessage);
        setIsLoading(false);
        setIsReady(false);
        setShouldFallbackToServer(true);
      }
    }
  }, [isSupported, isReady, isLoading]);

  /**
   * Extract phonemes from audio blob.
   * Returns null if extraction fails (caller should fallback to server).
   */
  const extractPhonemes = useCallback(
    async (audio: Blob): Promise<string[][] | null> => {
      // Check if model is actually loaded (not relying on React state to avoid timing issues)
      if (!phonemeExtractor.isModelLoaded()) {
        console.warn("Model not loaded, cannot extract phonemes");
        setShouldFallbackToServer(true);
        return null;
      }

      try {
        const phonemes = await phonemeExtractor.extractPhonemes(audio);

        // Reset fallback flag on successful extraction
        if (isMountedRef.current) {
          setShouldFallbackToServer(false);
        }

        return phonemes;
      } catch (err) {
        console.error("Phoneme extraction failed:", err);

        if (isMountedRef.current) {
          const errorMessage =
            err instanceof Error ? err.message : "Phoneme extraction failed";
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
    phonemeExtractor.unloadModel();

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
    extractPhonemes,
    unloadModel,
  };
}
