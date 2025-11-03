import { useSettings } from "@/contexts/SettingsContext";
import { usePhonemeModel } from "./usePhonemeModel";
import { useAudioAnalysisStream } from "./useAudioAnalysisStream";
import type { UseAudioAnalysisStreamOptions } from "./useAudioAnalysisStream";
import { performanceTracker } from "@/services/performanceTracker";
import phonemeExtractor from "@/services/phonemeExtractor";

interface UseHybridAudioAnalysisOptions extends UseAudioAnalysisStreamOptions {
  /** Maximum number of retries for client extraction (default: 2) */
  maxRetries?: number;
  /** Enable exponential backoff for retries (default: true) */
  enableBackoff?: boolean;
}

/**
 * Retry extraction with exponential backoff.
 * @param fn - Function to retry
 * @param maxRetries - Maximum number of retries
 * @param enableBackoff - Whether to use exponential backoff
 */
async function retryWithBackoff<T>(
  fn: () => Promise<T>,
  maxRetries: number = 2,
  enableBackoff: boolean = true
): Promise<T> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      // If this was the last attempt, throw the error
      if (attempt === maxRetries) {
        throw error;
      }

      // Calculate backoff delay: 1s, 2s, 4s, etc.
      const backoffMs = enableBackoff ? Math.pow(2, attempt) * 1000 : 500;

      console.warn(
        `Extraction attempt ${
          attempt + 1
        } failed, retrying in ${backoffMs}ms...`,
        error
      );

      // Wait before retrying
      await new Promise((resolve) => setTimeout(resolve, backoffMs));
    }
  }

  // TypeScript requires this, but we'll never reach here
  throw new Error("Retry logic failed unexpectedly");
}

/**
 * Hook that orchestrates hybrid audio analysis by combining client-side
 * phoneme extraction with server-side processing.
 *
 * Flow:
 * 1. Check if client-side extraction is enabled in settings
 * 2. Check if the phoneme model is ready
 * 3. If both true: extract phonemes locally, send to backend
 * 4. If either false: send audio directly to backend for full processing
 * 5. Automatic fallback to server if client extraction fails
 */
export const useHybridAudioAnalysis = (
  options?: UseHybridAudioAnalysisOptions
) => {
  const { settings } = useSettings();
  const audioAnalysisStream = useAudioAnalysisStream(options);
  const phonemeModel = usePhonemeModel();

  /**
   * Process audio using hybrid approach with retry logic:
   * - Try client-side phoneme extraction if enabled and ready
   * - Retry with exponential backoff on failure
   * - Fallback to full server processing if all retries fail
   */
  const processAudio = async (audioFile: File, sentence: string) => {
    let clientPhonemes: string[][] | null = null;

    // Attempt client-side extraction if enabled and model is actually loaded
    // Check phonemeExtractor.isModelLoaded() directly instead of relying on React state
    // to avoid race conditions with state updates
    const shouldUseClientExtraction =
      settings?.use_client_phoneme_extraction &&
      phonemeExtractor.isModelLoaded() &&
      !phonemeModel.shouldFallbackToServer;

    if (shouldUseClientExtraction) {
      const maxRetries = options?.maxRetries ?? 2;
      const enableBackoff = options?.enableBackoff ?? true;

      try {
        console.log("Attempting client-side phoneme extraction with retry...");
        const startTime = performance.now();

        // Wrap extraction in retry logic
        clientPhonemes = await retryWithBackoff(
          () => phonemeModel.extractPhonemes(audioFile),
          maxRetries,
          enableBackoff
        );

        const extractionTime = performance.now() - startTime;
        console.log(
          `✅ Client phoneme extraction completed in ${extractionTime.toFixed(
            2
          )}ms`
        );

        // Track successful extraction
        performanceTracker.recordClientExtraction(
          extractionTime,
          true,
          undefined // Audio duration not available here
        );

        if (clientPhonemes) {
          console.log(
            "Successfully extracted phonemes on client:",
            clientPhonemes.length,
            "words"
          );
        }
      } catch (error) {
        console.warn(
          "❌ Client extraction failed after retries, falling back to server:",
          error
        );

        // Track failed extraction
        performanceTracker.recordClientExtraction(
          0,
          false,
          undefined,
          error instanceof Error ? error.message : String(error)
        );

        clientPhonemes = null;
      }
    } else {
      const reason = !settings?.use_client_phoneme_extraction
        ? "disabled in settings"
        : !phonemeModel.isReady
        ? "model not ready"
        : "fallback flag set";
      console.log(`ℹ️ Skipping client extraction: ${reason}`);
    }

    // Send to backend with or without client phonemes
    audioAnalysisStream.start(audioFile, sentence, clientPhonemes);
  };

  /**
   * Load the phoneme model if client extraction is enabled.
   * Tracks model load time for performance monitoring.
   */
  const initializeModel = async () => {
    if (settings?.use_client_phoneme_extraction && !phonemeModel.isReady) {
      try {
        console.log("🔄 Initializing client-side phoneme model...");
        const startTime = performance.now();

        await phonemeModel.loadModel();

        const loadTime = performance.now() - startTime;
        performanceTracker.recordModelLoad(loadTime);

        console.log(
          `✅ Model initialized successfully in ${(loadTime / 1000).toFixed(
            2
          )}s`
        );
      } catch (error) {
        console.warn("❌ Failed to initialize model:", error);
      }
    }
  };

  return {
    // Audio processing
    processAudio,
    stop: audioAnalysisStream.stop,

    // Model management
    initializeModel,
    loadModel: phonemeModel.loadModel,
    unloadModel: phonemeModel.unloadModel,

    // Model state
    isModelSupported: phonemeModel.isSupported,
    isModelLoading: phonemeModel.isLoading,
    isModelReady: phonemeModel.isReady,
    modelLoadProgress: phonemeModel.loadProgress,
    modelError: phonemeModel.error,
    shouldFallbackToServer: phonemeModel.shouldFallbackToServer,

    // Settings state
    isClientExtractionEnabled: settings?.use_client_phoneme_extraction ?? false,
  };
};
