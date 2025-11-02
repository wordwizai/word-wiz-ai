import { useSettings } from "@/contexts/SettingsContext";
import { usePhonemeModel } from "./usePhonemeModel";
import { useAudioAnalysisStream } from "./useAudioAnalysisStream";
import type { UseAudioAnalysisStreamOptions } from "./useAudioAnalysisStream";

interface UseHybridAudioAnalysisOptions extends UseAudioAnalysisStreamOptions {
  // Additional options can be added here if needed
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
   * Process audio using hybrid approach:
   * - Try client-side phoneme extraction if enabled and ready
   * - Fallback to full server processing if needed
   */
  const processAudio = async (audioFile: File, sentence: string) => {
    let clientPhonemes: string[][] | null = null;

    // Attempt client-side extraction if enabled and model is ready
    const shouldUseClientExtraction =
      settings?.use_client_phoneme_extraction &&
      phonemeModel.isReady &&
      !phonemeModel.shouldFallbackToServer;

    if (shouldUseClientExtraction) {
      try {
        console.log("Attempting client-side phoneme extraction...");
        const startTime = performance.now();

        clientPhonemes = await phonemeModel.extractPhonemes(audioFile);

        const extractionTime = performance.now() - startTime;
        console.log(
          `Client phoneme extraction completed in ${extractionTime.toFixed(
            2
          )}ms`
        );

        if (clientPhonemes) {
          console.log(
            "Successfully extracted phonemes on client:",
            clientPhonemes
          );
        }
      } catch (error) {
        console.warn(
          "Client extraction failed, falling back to server:",
          error
        );
        clientPhonemes = null;
      }
    } else {
      const reason = !settings?.use_client_phoneme_extraction
        ? "disabled in settings"
        : !phonemeModel.isReady
        ? "model not ready"
        : "fallback flag set";
      console.log(`Skipping client extraction: ${reason}`);
    }

    // Send to backend with or without client phonemes
    audioAnalysisStream.start(audioFile, sentence, clientPhonemes);
  };

  /**
   * Load the phoneme model if client extraction is enabled
   */
  const initializeModel = async () => {
    if (settings?.use_client_phoneme_extraction && !phonemeModel.isReady) {
      try {
        console.log("Initializing client-side phoneme model...");
        await phonemeModel.loadModel();
        console.log("Model initialized successfully");
      } catch (error) {
        console.warn("Failed to initialize model:", error);
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
