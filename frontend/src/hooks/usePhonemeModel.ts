import { useState, useCallback, useEffect } from "react";
import phonemeExtractor from "@/services/phonemeExtractor";
import { useModelLoader } from "./useModelLoader";

export interface UsePhonemeModelReturn {
  isSupported: boolean;
  isLoading: boolean;
  isReady: boolean;
  loadProgress: number;
  error: string | null;
  shouldFallbackToServer: boolean;
  loadModel: () => Promise<void>;
  extractPhonemes: (audio: Blob) => Promise<string[][] | null>;
  extractPhonemesAndWords: (
    audio: Blob
  ) => Promise<{ phonemes: string[][]; words: string[] } | null>;
  unloadModel: () => void;
}

export function usePhonemeModel(): UsePhonemeModelReturn {
  const [isSupported, setIsSupported] = useState(true);

  const {
    isLoading,
    isReady,
    loadProgress,
    error,
    shouldFallbackToServer,
    isMountedRef,
    setError,
    setShouldFallbackToServer,
    loadModel,
    unloadModel,
  } = useModelLoader(phonemeExtractor, isSupported, "Browser or device not supported");

  useEffect(() => {
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
      }
    };

    checkSupport();
  }, []);

  const extractPhonemes = useCallback(
    async (audio: Blob): Promise<string[][] | null> => {
      if (!phonemeExtractor.isModelLoaded()) {
        console.warn("Model not loaded, cannot extract phonemes");
        setShouldFallbackToServer(true);
        return null;
      }

      try {
        const phonemes = await phonemeExtractor.extractPhonemes(audio);

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

  const extractPhonemesAndWords = useCallback(
    async (
      audio: Blob
    ): Promise<{ phonemes: string[][]; words: string[] } | null> => {
      if (!phonemeExtractor.isModelLoaded()) {
        console.warn("Model not loaded, cannot extract phonemes and words");
        setShouldFallbackToServer(true);
        return null;
      }

      try {
        const result = await phonemeExtractor.extractPhonemesAndWords(audio);

        if (isMountedRef.current) {
          setShouldFallbackToServer(false);
        }

        return result;
      } catch (err) {
        console.error("Phoneme and word extraction failed:", err);

        if (isMountedRef.current) {
          const errorMessage =
            err instanceof Error
              ? err.message
              : "Phoneme and word extraction failed";
          setError(errorMessage);
          setShouldFallbackToServer(true);
        }

        return null;
      }
    },
    [isReady]
  );

  return {
    isSupported,
    isLoading,
    isReady,
    loadProgress,
    error,
    shouldFallbackToServer,
    loadModel,
    extractPhonemes,
    extractPhonemesAndWords,
    unloadModel,
  };
}
