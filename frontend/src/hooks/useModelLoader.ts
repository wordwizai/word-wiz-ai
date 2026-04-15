import { useState, useCallback, useEffect, useRef } from "react";

export interface ModelExtractor {
  loadModel: (onProgress: (progress: number) => void) => Promise<void>;
  unloadModel: () => void;
  isModelLoaded: () => boolean;
}

export interface UseModelLoaderReturn {
  isLoading: boolean;
  isReady: boolean;
  loadProgress: number;
  error: string | null;
  shouldFallbackToServer: boolean;
  isMountedRef: React.MutableRefObject<boolean>;
  setError: React.Dispatch<React.SetStateAction<string | null>>;
  setShouldFallbackToServer: React.Dispatch<React.SetStateAction<boolean>>;
  loadModel: () => Promise<void>;
  unloadModel: () => void;
}

/**
 * Shared hook for managing client-side ML model loading state.
 * Handles the load/unload lifecycle, progress tracking, and error state.
 * Used by usePhonemeModel and useWordModel.
 */
export function useModelLoader(
  extractor: ModelExtractor,
  isSupported: boolean,
  unsupportedErrorMessage: string
): UseModelLoaderReturn {
  const [isLoading, setIsLoading] = useState(false);
  const [isReady, setIsReady] = useState(false);
  const [loadProgress, setLoadProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [shouldFallbackToServer, setShouldFallbackToServer] = useState(false);

  const isMountedRef = useRef(true);

  useEffect(() => {
    if (extractor.isModelLoaded()) {
      setIsReady(true);
      setLoadProgress(100);
    }

    return () => {
      isMountedRef.current = false;
    };
  }, []);

  const loadModel = useCallback(async () => {
    if (!isSupported) {
      setError(unsupportedErrorMessage);
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
      await extractor.loadModel((progress) => {
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
  }, [extractor, isSupported, unsupportedErrorMessage, isReady, isLoading]);

  const unloadModel = useCallback(() => {
    extractor.unloadModel();

    if (isMountedRef.current) {
      setIsReady(false);
      setLoadProgress(0);
      setError(null);
    }
  }, [extractor]);

  return {
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
  };
}
