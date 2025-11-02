import {
  pipeline,
  AutomaticSpeechRecognitionPipeline,
} from "@xenova/transformers";

/**
 * Singleton client-side phoneme extractor.
 * Manages model lifecycle, caching, and extraction.
 *
 * Model Options:
 * - "Xenova/wav2vec2-lv-60-espeak-cv-ft" - eSpeak phonemes (default, ~250MB)
 * - "Xenova/wav2vec2-large-xlsr-53-english" - English ASR (~1.2GB, can extract phonemes)
 *
 * To use TIMIT-IPA model (speech31/wav2vec2-large-TIMIT-IPA):
 * The model must be converted to ONNX format first. Options:
 * 1. Check if "Xenova/wav2vec2-large-TIMIT-IPA" exists (community conversion)
 * 2. Convert yourself: https://huggingface.co/docs/transformers.js/custom_usage
 * 3. Use the backend's TIMIT model and only run simpler models client-side
 */
class ClientPhonemeExtractor {
  private static instance: ClientPhonemeExtractor | null = null;
  private model: AutomaticSpeechRecognitionPipeline | null = null;

  // Model configuration - can be changed before loading
  private modelName = "Xenova/wav2vec2-lv-60-espeak-cv-ft"; // ONNX-compatible phoneme model

  private isLoading = false;
  private loadProgress = 0;
  private progressCallback: ((progress: number) => void) | null = null;

  private constructor() {}

  /**
   * Get the singleton instance.
   */
  static getInstance(): ClientPhonemeExtractor {
    if (!ClientPhonemeExtractor.instance) {
      ClientPhonemeExtractor.instance = new ClientPhonemeExtractor();
    }
    return ClientPhonemeExtractor.instance;
  }

  /**
   * Check if the browser supports WebAssembly and required features.
   */
  checkBrowserSupport(): boolean {
    try {
      // Check WebAssembly support
      if (typeof WebAssembly === "undefined") {
        console.warn("WebAssembly not supported");
        return false;
      }

      // Check if we can create audio context
      if (
        typeof AudioContext === "undefined" &&
        typeof (window as any).webkitAudioContext === "undefined"
      ) {
        console.warn("AudioContext not supported");
        return false;
      }

      return true;
    } catch (error) {
      console.error("Browser support check failed:", error);
      return false;
    }
  }

  /**
   * Check if device has enough resources to run the model.
   * Estimates based on available RAM and device type.
   */
  async checkDeviceResources(): Promise<boolean> {
    try {
      // Check device memory (if available)
      const deviceMemory = (navigator as any).deviceMemory;
      if (deviceMemory && deviceMemory < 4) {
        console.warn(`Low device memory: ${deviceMemory}GB`);
        return false;
      }

      // Check if mobile device (may struggle with model)
      const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
      if (isMobile && deviceMemory && deviceMemory < 6) {
        console.warn("Mobile device with limited resources");
        return false;
      }

      return true;
    } catch (error) {
      console.error("Resource check failed:", error);
      // If we can't check, assume it's okay
      return true;
    }
  }

  /**
   * Load the phoneme extraction model.
   * @param onProgress - Callback for loading progress (0-100)
   */
  async loadModel(onProgress?: (progress: number) => void): Promise<void> {
    if (this.model) {
      console.log("Model already loaded");
      return;
    }

    if (this.isLoading) {
      console.log("Model is already loading");
      return;
    }

    this.isLoading = true;
    this.progressCallback = onProgress || null;
    this.loadProgress = 0;

    try {
      console.log("Loading phoneme extraction model...");

      // Update progress callback
      const updateProgress = (progress: number) => {
        this.loadProgress = progress;
        if (this.progressCallback) {
          this.progressCallback(progress);
        }
      };

      updateProgress(10);

      // Load the ASR pipeline with progress tracking
      this.model = await pipeline(
        "automatic-speech-recognition",
        this.modelName,
        {
          progress_callback: (progressData: any) => {
            // TransformersJS progress format: { progress, loaded, total, status }
            if (progressData.progress !== undefined) {
              const modelProgress = Math.min(
                90,
                Math.floor(10 + progressData.progress * 0.8)
              );
              updateProgress(modelProgress);
            }
          },
        }
      );

      updateProgress(100);
      console.log("Phoneme extraction model loaded successfully");
    } catch (error) {
      console.error("Failed to load model:", error);
      this.model = null;
      throw error;
    } finally {
      this.isLoading = false;
      this.progressCallback = null;
    }
  }

  /**
   * Extract phonemes from audio blob.
   * @param audioBlob - Audio file as Blob
   * @returns Array of words, each containing array of phonemes
   */
  async extractPhonemes(audioBlob: Blob): Promise<string[][]> {
    if (!this.model) {
      throw new Error("Model not loaded. Call loadModel() first.");
    }

    try {
      console.log("Extracting phonemes from audio...");

      // Convert blob to array buffer
      const arrayBuffer = await audioBlob.arrayBuffer();

      // Create audio context to decode the audio
      const audioContext = new (window.AudioContext ||
        (window as any).webkitAudioContext)();
      const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);

      // Get audio data as Float32Array (mono, 16kHz)
      let audioData = audioBuffer.getChannelData(0);

      // Resample to 16kHz if needed
      if (audioBuffer.sampleRate !== 16000) {
        console.log(`Resampling from ${audioBuffer.sampleRate}Hz to 16000Hz`);
        audioData = this.resampleAudio(
          audioData,
          audioBuffer.sampleRate,
          16000
        ) as Float32Array;
      }

      // Run model inference
      const result = await this.model(audioData, {
        return_timestamps: false,
        chunk_length_s: 30,
        stride_length_s: 5,
      });

      console.log("Raw model output:", result);

      // Parse the phoneme output
      const phonemes = this.parsePhonemeOutput(result.text);

      console.log("Extracted phonemes:", phonemes);
      return phonemes;
    } catch (error) {
      console.error("Phoneme extraction failed:", error);
      throw error;
    }
  }

  /**
   * Parse phoneme output from model into word->phonemes format.
   * Model outputs IPA phonemes separated by spaces, words separated by spaces.
   */
  private parsePhonemeOutput(text: string): string[][] {
    if (!text || text.trim() === "") {
      return [];
    }

    // The model outputs phonemes like: "h ɛ l oʊ w ɜr l d"
    // We need to group them by words
    // For now, split by spaces and group based on typical phoneme patterns

    const phonemes = text
      .trim()
      .split(/\s+/)
      .filter((p) => p.length > 0);

    // Simple heuristic: group phonemes into words
    // This is a basic implementation - you may need to adjust based on actual model output
    const words: string[][] = [];
    let currentWord: string[] = [];

    for (const phoneme of phonemes) {
      currentWord.push(phoneme);

      // Simple heuristic: vowels often end words
      // This is approximate and may need refinement
      const isVowel = /[aeiouəɛɪɔʊʌæ]/i.test(phoneme);
      if (isVowel && currentWord.length >= 2) {
        words.push([...currentWord]);
        currentWord = [];
      }
    }

    // Add remaining phonemes
    if (currentWord.length > 0) {
      words.push(currentWord);
    }

    return words.length > 0 ? words : [phonemes]; // Fallback: treat all as one word
  }

  /**
   * Simple audio resampling using linear interpolation.
   */
  private resampleAudio(
    audioData: Float32Array,
    fromSampleRate: number,
    toSampleRate: number
  ): Float32Array {
    const ratio = fromSampleRate / toSampleRate;
    const newLength = Math.floor(audioData.length / ratio);
    const resampled = new Float32Array(newLength);

    for (let i = 0; i < newLength; i++) {
      const srcIndex = i * ratio;
      const srcIndexFloor = Math.floor(srcIndex);
      const srcIndexCeil = Math.min(srcIndexFloor + 1, audioData.length - 1);
      const t = srcIndex - srcIndexFloor;

      // Linear interpolation
      resampled[i] =
        audioData[srcIndexFloor] * (1 - t) + audioData[srcIndexCeil] * t;
    }

    return resampled;
  }

  /**
   * Unload the model and free memory.
   */
  unloadModel(): void {
    if (this.model) {
      console.log("Unloading phoneme extraction model...");
      this.model = null;
      // Force garbage collection if available
      if ((window as any).gc) {
        (window as any).gc();
      }
    }
  }

  /**
   * Check if model is currently loaded.
   */
  isModelLoaded(): boolean {
    return this.model !== null;
  }

  /**
   * Check if model is currently loading.
   */
  isModelLoading(): boolean {
    return this.isLoading;
  }

  /**
   * Get current loading progress (0-100).
   */
  getLoadProgress(): number {
    return this.loadProgress;
  }
}

// Export singleton instance
export default ClientPhonemeExtractor.getInstance();
