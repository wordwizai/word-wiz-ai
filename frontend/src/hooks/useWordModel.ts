import { useState, useCallback, useEffect } from "react";
import wordExtractor from "@/services/wordExtractor";
import { useModelLoader } from "./useModelLoader";

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

export function useWordModel(): UseWordModelReturn {
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
  } = useModelLoader(wordExtractor, isSupported, "Device not supported for word extraction");

  useEffect(() => {
    const checkSupport = () => {
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
      }
    };

    checkSupport();
  }, []);

  const extractWords = useCallback(
    async (audio: Blob): Promise<string[] | null> => {
      if (!wordExtractor.isModelLoaded()) {
        console.warn("Word model not loaded, cannot extract words");
        setShouldFallbackToServer(true);
        return null;
      }

      try {
        const words = await wordExtractor.extractWords(audio);

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
