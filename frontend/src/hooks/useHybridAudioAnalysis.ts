import { useSettings } from "@/contexts/SettingsContext";
import { usePhonemeModel } from "./usePhonemeModel";
import { useWordModel } from "./useWordModel";
import { useAudioTransport } from "./useAudioTransport";
import type { UseAudioTransportOptions } from "./useAudioTransport";
import { performanceTracker } from "@/services/performanceTracker";
import phonemeExtractor from "@/services/phonemeExtractor";
import wordExtractor from "@/services/wordExtractor";
import type { ExtractionType } from "@/services/performanceTracker";
import { showModelError, showAudioError } from "@/utils/errorHandling";

interface UseHybridAudioAnalysisOptions
  extends Omit<UseAudioTransportOptions, "useWebSocket" | "sessionId"> {
  /** Session ID for this audio analysis session */
  sessionId: number;
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
  options: UseHybridAudioAnalysisOptions
) => {
  const { settings } = useSettings();

  // Determine whether to use WebSocket based on settings (default: false for gradual rollout)
  const useWebSocket = settings?.use_websocket ?? false;

  // Initialize transport with WebSocket or SSE based on settings
  const audioTransport = useAudioTransport({
    ...options,
    useWebSocket,
  });

  const phonemeModel = usePhonemeModel();
  const wordModel = useWordModel();

  /**
   * Initialize both models in parallel if client extraction is enabled
   */
  const initializeModels = async () => {
    // Always enable client extraction if supported
    const shouldUseClientExtraction =
      settings?.use_client_phoneme_extraction ?? false;

    if (!shouldUseClientExtraction) {
      console.log(
        "[HybridAudioAnalysis] Client extraction disabled or not supported"
      );
      return;
    }

    try {
      console.log("[HybridAudioAnalysis] Loading both models in parallel...");
      const startTime = performance.now();

      // Load both models in parallel
      const [phonemeResult, wordResult] = await Promise.allSettled([
        phonemeModel.loadModel(),
        wordModel.loadModel(),
      ]);

      const loadTime = performance.now() - startTime;

      // Check results
      const phonemeSuccess = phonemeResult.status === "fulfilled";
      const wordSuccess = wordResult.status === "fulfilled";

      if (phonemeSuccess && wordSuccess) {
        console.log(
          `[HybridAudioAnalysis] ✅ Both models loaded successfully in ${loadTime.toFixed(
            0
          )}ms`
        );
      } else if (phonemeSuccess || wordSuccess) {
        console.warn(
          `[HybridAudioAnalysis] ⚠️ Partial model loading - Phonemes: ${phonemeSuccess}, Words: ${wordSuccess}`
        );
        if (phonemeResult.status === "rejected") {
          console.error(
            "[HybridAudioAnalysis] Phoneme model error:",
            phonemeResult.reason
          );
        }
        if (wordResult.status === "rejected") {
          console.error(
            "[HybridAudioAnalysis] Word model error:",
            wordResult.reason
          );
        }
      } else {
        console.error("[HybridAudioAnalysis] ❌ Both models failed to load");
        showModelError(new Error("Failed to load both models"));
        throw new Error("Failed to load both models");
      }
    } catch (error) {
      console.error("[HybridAudioAnalysis] Error loading models:", error);
      throw error;
    }
  };

  /**
   * Process audio using hybrid approach with retry logic:
   * - Try client-side phoneme and word extraction in parallel if enabled
   * - Retry with exponential backoff on failure
   * - Fallback to full server processing if all retries fail
   * - Support partial success (e.g., phonemes work but words fail)
   */
  const processAudio = async (audioFile: File, sentence: string) => {
    let clientPhonemes: string[][] | null = null;
    let clientWords: string[] | null = null;

    // Check if both models are loaded (always enabled if models are ready)
    const shouldUseClientExtraction =
      settings?.use_client_phoneme_extraction &&
      phonemeExtractor.isModelLoaded() &&
      wordExtractor.isModelLoaded() &&
      !phonemeModel.shouldFallbackToServer &&
      !wordModel.shouldFallbackToServer;

    if (shouldUseClientExtraction) {
      const maxRetries = options?.maxRetries ?? 2;
      const enableBackoff = options?.enableBackoff ?? true;

      try {
        console.log(
          "[HybridAudioAnalysis] Attempting client-side extraction (phonemes + words) with retry..."
        );
        const startTime = performance.now();

        // Extract both phonemes and words in parallel with retry logic
        const [phonemeResult, wordResult] = await Promise.allSettled([
          retryWithBackoff(
            () => phonemeModel.extractPhonemes(audioFile),
            maxRetries,
            enableBackoff
          ),
          retryWithBackoff(
            () => wordModel.extractWords(audioFile),
            maxRetries,
            enableBackoff
          ),
        ]);

        const extractionTime = performance.now() - startTime;

        // Handle results
        const phonemeSuccess = phonemeResult.status === "fulfilled";
        const wordSuccess = wordResult.status === "fulfilled";

        if (phonemeSuccess) {
          clientPhonemes = phonemeResult.value;
        }
        if (wordSuccess) {
          clientWords = wordResult.value;
        }

        // Determine extraction type based on what succeeded
        // No validation needed - backend will handle alignment
        if (clientPhonemes && clientWords) {
          const wordCount = clientWords.length;
          console.log(
            `[HybridAudioAnalysis] ✅ Full extraction completed in ${extractionTime.toFixed(
              2
            )}ms (${wordCount} words, ${clientPhonemes.length} phoneme words)`
          );
          performanceTracker.recordClientExtraction(
            extractionTime,
            true,
            wordCount,
            undefined,
            "full" as ExtractionType
          );
        } else if (clientPhonemes || clientWords) {
          // Partial success - backend will handle alignment
          console.warn(
            `[HybridAudioAnalysis] ⚠️ Partial extraction success - Phonemes: ${!!clientPhonemes}, Words: ${!!clientWords} (${extractionTime.toFixed(
              2
            )}ms)`
          );
          performanceTracker.recordClientExtraction(
            extractionTime,
            true,
            undefined,
            undefined,
            "partial" as ExtractionType
          );
        } else {
          // Both failed
          console.error(
            `[HybridAudioAnalysis] ❌ Both extractions failed after retries`
          );
          if (phonemeResult.status === "rejected") {
            console.error("Phoneme error:", phonemeResult.reason);
          }
          if (wordResult.status === "rejected") {
            console.error("Word error:", wordResult.reason);
          }
          const errorMsg =
            phonemeResult.status === "rejected"
              ? String(phonemeResult.reason)
              : wordResult.status === "rejected"
              ? String(wordResult.reason)
              : "Unknown error";
          performanceTracker.recordClientExtraction(
            extractionTime,
            false,
            undefined,
            errorMsg,
            "failed" as ExtractionType
          );
        }
      } catch (error) {
        console.error(
          "[HybridAudioAnalysis] Unexpected error during extraction:",
          error
        );
        showAudioError(error as Error);
        performanceTracker.recordClientExtraction(0, false);
      }
    }

    // If both phonemes and words were extracted on client, send empty audio to save bandwidth
    const audioToSend =
      clientPhonemes && clientWords
        ? new File([], "empty.wav", { type: "audio/wav" })
        : audioFile;

    if (clientPhonemes && clientWords) {
      console.log(
        "[HybridAudioAnalysis] 🚀 Full client extraction - sending empty audio to save bandwidth"
      );
    }

    // Send to backend (with or without client-extracted data)
    await audioTransport.sendAudio(
      audioToSend,
      sentence,
      clientPhonemes,
      clientWords
    );
  };

  return {
    // Audio processing
    processAudio,
    stop: audioTransport.disconnect,

    // Transport state
    isConnected: audioTransport.isConnected,
    isProcessing: audioTransport.isProcessing,

    // Model management
    initializeModels,
    loadModel: async () => {
      await Promise.all([phonemeModel.loadModel(), wordModel.loadModel()]);
    },
    unloadModel: async () => {
      await Promise.all([phonemeModel.unloadModel(), wordModel.unloadModel()]);
    },

    // Model state - combined status
    isModelSupported: phonemeModel.isSupported && wordModel.isSupported,
    isModelLoading: phonemeModel.isLoading || wordModel.isLoading,
    isModelReady: phonemeModel.isReady && wordModel.isReady,
    modelLoadProgress: Math.round(
      (phonemeModel.loadProgress + wordModel.loadProgress) / 2
    ),
    phonemeModelProgress: phonemeModel.loadProgress,
    wordModelProgress: wordModel.loadProgress,
    modelError: phonemeModel.error || wordModel.error,
    shouldFallbackToServer:
      phonemeModel.shouldFallbackToServer || wordModel.shouldFallbackToServer,

    // Settings state
    isClientExtractionEnabled: settings?.use_client_phoneme_extraction ?? false,
  };
};
