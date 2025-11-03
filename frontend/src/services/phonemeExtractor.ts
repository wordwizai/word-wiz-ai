import {
  pipeline,
  AutomaticSpeechRecognitionPipeline,
  env,
} from "@huggingface/transformers";
import {
  checkDeviceCapabilities,
  type DeviceCapabilities,
} from "../utils/deviceCapabilities";

// Configure HuggingFace authentication token globally
const hfToken = import.meta.env.VITE_HUGGINGFACE_TOKEN;
if (hfToken) {
  // Set custom headers for authentication
  (env as any).customHeaders = {
    Authorization: `Bearer ${hfToken}`,
  };
  console.log("🔑 HuggingFace token configured");
} else {
  console.warn("⚠️ No HuggingFace token found - may encounter 401 errors");
}

// Performance optimizations for Transformers.js
// Enable multi-threading for faster inference (requires crossOriginIsolated headers)
if (env.backends?.onnx?.wasm) {
  const numThreads = navigator.hardwareConcurrency || 4;
  env.backends.onnx.wasm.numThreads = numThreads;
  console.log(
    `🚀 WASM configured for ${numThreads} threads (will fall back to single-thread if crossOriginIsolated not enabled)`
  );
}

// Try to use WebGPU for even faster inference if available
// WebGPU is 10-100x faster than WASM but only available in Chrome/Edge
if ("gpu" in navigator) {
  console.log("🎮 WebGPU detected - will attempt to use GPU acceleration");
} else {
  console.log("💻 WebGPU not available, using CPU (WASM)");
}

/**
 * Singleton client-side phoneme extractor.
 * Manages model lifecycle, caching, and extraction with resource detection.
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
  // Using our custom ONNX-converted TIMIT-IPA model for IPA phoneme extraction
  private modelName = "Bobcat9/wav2vec2-timit-ipa-onnx"; // ONNX-compatible IPA phoneme model

  // Use quantized model for faster inference (4-5x speedup)
  private useQuantized = true;

  private isLoading = false;
  private loadProgress = 0;
  private progressCallback: ((progress: number) => void) | null = null;

  // Device capabilities cache
  private deviceCapabilities: DeviceCapabilities | null = null;

  private constructor() {
    // Check device capabilities on initialization
    this.deviceCapabilities = checkDeviceCapabilities();

    if (!this.deviceCapabilities.canRunModel) {
      console.warn(
        "Device cannot run AI model:",
        this.deviceCapabilities.warningMessage
      );
    }
  }

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
   * Get device capabilities assessment.
   */
  getDeviceCapabilities(): DeviceCapabilities {
    if (!this.deviceCapabilities) {
      this.deviceCapabilities = checkDeviceCapabilities();
    }
    return this.deviceCapabilities;
  }

  /**
   * Check if the browser supports WebAssembly and required features.
   * @deprecated Use getDeviceCapabilities() instead for more comprehensive checks
   */
  checkBrowserSupport(): boolean {
    const capabilities = this.getDeviceCapabilities();
    return capabilities.hasWebAssembly;
  }

  /**
   * Check if device has enough resources to run the model.
   * @deprecated Use getDeviceCapabilities() instead for more comprehensive checks
   */
  async checkDeviceResources(): Promise<boolean> {
    const capabilities = this.getDeviceCapabilities();
    return capabilities.canRunModel;
  }

  /**
   * Load the phoneme extraction model.
   * @param onProgress - Callback for loading progress (0-100)
   * @throws Error if device cannot run model
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

    // Check device capabilities before attempting to load
    const capabilities = this.getDeviceCapabilities();
    if (!capabilities.canRunModel) {
      const error = new Error(
        capabilities.warningMessage ||
          "Device does not meet minimum requirements for running AI model"
      );
      console.error("Cannot load model:", error.message);
      throw error;
    }

    this.isLoading = true;
    this.progressCallback = onProgress || null;
    this.loadProgress = 0;

    try {
      console.log("Loading phoneme extraction model...");
      console.log(
        `Device: ${capabilities.isMobile ? "Mobile" : "Desktop"}, RAM: ${
          capabilities.estimatedRAM
        }GB`
      );

      // Update progress callback
      const updateProgress = (progress: number) => {
        this.loadProgress = progress;
        if (this.progressCallback) {
          this.progressCallback(progress);
        }
      };

      updateProgress(10);

      // Load the ASR pipeline with progress tracking and authentication
      const hfToken = import.meta.env.VITE_HUGGINGFACE_TOKEN;

      // Configure base settings
      const baseConfig: any = {
        // Pass HuggingFace token for model download authentication
        token: hfToken,
        // Use quantized model for 4-5x faster inference
        quantized: this.useQuantized,
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
      };

      // Try WebGPU first, fallback to WASM if it fails
      let loadSuccess = false;

      // Attempt 1: Try WebGPU (10-100x faster)
      // WebGPU is available in Chrome/Edge 113+, Safari 18+
      // In production (HTTPS), it should work automatically
      // In development, users may need to enable chrome://flags/#enable-unsafe-webgpu
      if ("gpu" in navigator) {
        try {
          console.log("🎮 Attempting WebGPU acceleration...");
          const adapter = await (navigator as any).gpu?.requestAdapter();
          if (adapter) {
            const webgpuConfig = {
              ...baseConfig,
              device: "webgpu",
              dtype: "fp32",
            };
            this.model = await pipeline(
              "automatic-speech-recognition",
              this.modelName,
              webgpuConfig as any
            );
            console.log("✅ Using WebGPU acceleration! (10-100x faster)");
            loadSuccess = true;
          } else {
            console.log("⚠️ WebGPU adapter not available, falling back to CPU");
          }
        } catch (webgpuError) {
          console.warn("⚠️ WebGPU failed, falling back to CPU:", webgpuError);
          if (import.meta.env.DEV) {
            console.log(
              "💡 Tip: Enable chrome://flags/#enable-unsafe-webgpu for faster inference in development"
            );
          }
        }
      } else {
        console.log("💻 WebGPU not supported in this browser, using CPU");
      }

      // Attempt 2: Fallback to WASM (CPU)
      if (!loadSuccess) {
        console.log("💻 Loading model on CPU (WASM)...");
        const wasmConfig = { ...baseConfig, device: "wasm" };
        this.model = await pipeline(
          "automatic-speech-recognition",
          this.modelName,
          wasmConfig as any
        );
        console.log("✅ Using CPU (WASM) backend");
      }

      updateProgress(100);
      console.log(
        `Phoneme extraction model loaded successfully (quantized: ${this.useQuantized})`
      );

      // Explicitly return to ensure promise resolves
      return;
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
      let audioData: Float32Array = audioBuffer.getChannelData(0);

      // Resample to 16kHz if needed
      if (audioBuffer.sampleRate !== 16000) {
        console.log(`Resampling from ${audioBuffer.sampleRate}Hz to 16000Hz`);
        const resampled = this.resampleAudio(
          audioData,
          audioBuffer.sampleRate,
          16000
        );
        audioData = resampled as Float32Array;
      }

      // Run model inference with CTC decoding
      // Calculate min/max without spread operator to avoid stack overflow
      let min = audioData[0];
      let max = audioData[0];
      for (let i = 1; i < audioData.length; i++) {
        if (audioData[i] < min) min = audioData[i];
        if (audioData[i] > max) max = audioData[i];
      }
      console.log(
        `Audio data: ${audioData.length} samples, min: ${min}, max: ${max}`
      );

      const result = await this.model(audioData, {
        return_timestamps: false,
        // Optimized chunk settings for faster processing
        chunk_length_s: 20, // Reduced from 30s for faster processing
        stride_length_s: 3, // Reduced from 5s for less overlap
        // Force greedy decoding (faster than beam search)
        num_beams: 1,
      });

      console.log("Raw model output:", result);

      const text = Array.isArray(result)
        ? result[0]?.text || ""
        : (result as any).text || "";
      console.log("Decoded text:", text);

      const phonemes = this.parsePhonemeOutput(text);

      console.log("Extracted phonemes:", phonemes);
      return phonemes;
    } catch (error) {
      console.error("Phoneme extraction failed:", error);
      throw error;
    }
  }

  /**
   * Parse phoneme output from model into word->phonemes format.
   * Model outputs IPA phonemes with [PAD] tokens and "|" as word delimiters.
   * Example: "[PAD]ðə k[PAD]w[PAD]ɪ[PAD]k [PAD]br[PAD]aʊ[PAD]n[PAD]"
   */
  private parsePhonemeOutput(text: string): string[][] {
    if (!text || text.trim() === "") {
      return [];
    }

    console.log("Parsing phoneme output:", text);

    // Step 1: Remove all [PAD] tokens
    let cleaned = text.replace(/\[PAD\]/g, "");
    console.log("After removing [PAD]:", cleaned);

    // Step 2: Replace "|" with space (word delimiter)
    cleaned = cleaned.replace(/\|/g, " ");

    // Step 3: Split by spaces to get individual phonemes
    const phonemes = cleaned
      .trim()
      .split(/\s+/)
      .filter((p) => p.length > 0);

    console.log("Individual phoneme words:", phonemes);

    // Step 4: Split each word into individual phoneme characters
    // Each word like "ðə" needs to become ["ð", "ə"]
    const words: string[][] = phonemes.map((word) => {
      // Split the word into individual characters (phonemes)
      return word.split("");
    });

    console.log("Parsed into words:", words);
    return words;
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
