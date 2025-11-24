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
  console.log("🔑 HuggingFace token configured for word model");
} else {
  console.warn(
    "⚠️ No HuggingFace token found for word model - may encounter 401 errors"
  );
}

/**
 * Singleton client-side word extractor.
 * Uses a separate ASR model (Whisper) to extract words from audio.
 * Runs in parallel with phoneme extractor.
 *
 * Model: Xenova/whisper-tiny.en (~75MB ONNX)
 * - Fast inference even on CPU
 * - Excellent accuracy for English word transcription
 * - Browser-cached after first download
 */
class ClientWordExtractor {
  private static instance: ClientWordExtractor | null = null;
  private model: AutomaticSpeechRecognitionPipeline | null = null;

  // Model configuration - Whisper tiny for fast word transcription
  private modelName = "Xenova/whisper-tiny.en"; // ~75MB ONNX model

  // Use quantized model for faster inference
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
        "Device cannot run word extraction model:",
        this.deviceCapabilities.warningMessage
      );
    }
  }

  /**
   * Get the singleton instance.
   */
  static getInstance(): ClientWordExtractor {
    if (!ClientWordExtractor.instance) {
      ClientWordExtractor.instance = new ClientWordExtractor();
    }
    return ClientWordExtractor.instance;
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
   * Load the word extraction model (Whisper).
   * @param onProgress - Callback for loading progress (0-100)
   * @throws Error if device cannot run model
   */
  async loadModel(onProgress?: (progress: number) => void): Promise<void> {
    if (this.model) {
      console.log("Word model already loaded");
      return;
    }

    if (this.isLoading) {
      console.log("Word model is already loading");
      return;
    }

    const capabilities = this.getDeviceCapabilities();
    if (!capabilities.canRunModel) {
      throw new Error(
        capabilities.warningMessage ||
          "Device does not meet minimum requirements for word model"
      );
    }

    this.isLoading = true;
    this.progressCallback = onProgress || null;
    this.loadProgress = 0;

    try {
      console.log("Loading word extraction model (Whisper)...");
      console.log(
        `Device: ${capabilities.isMobile ? "Mobile" : "Desktop"}, RAM: ${
          capabilities.estimatedRAM
        }GB`
      );

      const updateProgress = (progress: number) => {
        this.loadProgress = progress;
        if (this.progressCallback) {
          this.progressCallback(progress);
        }
      };

      updateProgress(10);

      const hfToken = import.meta.env.VITE_HUGGINGFACE_TOKEN;

      const baseConfig: any = {
        token: hfToken,
        quantized: this.useQuantized,
        progress_callback: (progressData: any) => {
          if (progressData.progress !== undefined) {
            const modelProgress = Math.min(
              90,
              Math.floor(10 + progressData.progress * 0.8)
            );
            updateProgress(modelProgress);
          }
        },
      };

      // Try WebGPU first, fallback to WASM
      let loadSuccess = false;

      // Attempt 1: Try WebGPU (10-100x faster)
      if ("gpu" in navigator) {
        try {
          console.log("🎮 Attempting WebGPU for word model...");
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
            console.log("✅ Word model using WebGPU acceleration!");
            loadSuccess = true;
          } else {
            console.log(
              "⚠️ WebGPU adapter not available for word model, falling back to CPU"
            );
          }
        } catch (webgpuError) {
          console.warn(
            "⚠️ WebGPU failed for word model, falling back to CPU:",
            webgpuError
          );
        }
      } else {
        console.log("💻 WebGPU not supported for word model, using CPU (WASM)");
      }

      // Attempt 2: Fallback to WASM (CPU)
      if (!loadSuccess) {
        console.log("💻 Loading word model on CPU (WASM)...");
        const wasmConfig = { ...baseConfig, device: "wasm" };
        this.model = await pipeline(
          "automatic-speech-recognition",
          this.modelName,
          wasmConfig as any
        );
        console.log("✅ Word model using CPU (WASM) backend");
      }

      updateProgress(100);
      console.log(
        `Word extraction model loaded successfully (quantized: ${this.useQuantized})`
      );

      return;
    } catch (error) {
      console.error("Failed to load word model:", error);
      this.model = null;
      throw error;
    } finally {
      this.isLoading = false;
      this.progressCallback = null;
    }
  }

  /**
   * Extract words from audio blob.
   * @param audioBlob - Audio file as Blob
   * @returns Array of words (strings)
   */
  async extractWords(audioBlob: Blob): Promise<string[]> {
    if (!this.model) {
      throw new Error("Word model not loaded. Call loadModel() first.");
    }

    try {
      console.log("Extracting words from audio using Whisper...");

      // Convert blob to array buffer
      const arrayBuffer = await audioBlob.arrayBuffer();

      // Create audio context to decode the audio
      const audioContext = new (window.AudioContext ||
        (window as any).webkitAudioContext)();
      const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);

      // Get audio data as Float32Array (mono, 16kHz)
      let audioData: Float32Array = audioBuffer.getChannelData(0);

      // Resample to 16kHz if needed (Whisper expects 16kHz)
      if (audioBuffer.sampleRate !== 16000) {
        console.log(
          `Resampling from ${audioBuffer.sampleRate}Hz to 16000Hz for Whisper`
        );
        const resampled = this.resampleAudio(
          audioData,
          audioBuffer.sampleRate,
          16000
        );
        audioData = resampled as Float32Array;
      }

      // Run Whisper inference
      console.log(
        `Running Whisper on ${audioData.length} audio samples (${(
          audioData.length / 16000
        ).toFixed(2)}s)`
      );

      // Note: Don't specify language/task for English-only models like whisper-tiny.en
      const result = await this.model(audioData, {
        chunk_length_s: 30, // Increased for better accuracy
        stride_length_s: 5, // Increased overlap for better boundary handling
        return_timestamps: false,
        // Use beam search for better accuracy
        num_beams: 5, // Increased from 1 for more accurate transcription
        // Repetition penalty to discourage repeated words/phrases
        repetition_penalty: 1.5,
        // No-repeat n-gram size to prevent exact repetitions
        no_repeat_ngram_size: 3,
        // Temperature for more conservative predictions
        temperature: 0.4, // Lower = less hallucination (Whisper works well at low temps)
      });

      console.log("Raw Whisper output:", result);

      const text = Array.isArray(result)
        ? result[0]?.text || ""
        : (result as any).text || "";

      console.log("Whisper transcribed text:", text);

      // Parse words from transcription
      const words = this.parseWords(text);

      console.log("Extracted words:", words);
      return words;
    } catch (error) {
      console.error("Word extraction failed:", error);
      throw error;
    }
  }

  /**
   * Parse words from Whisper transcription.
   * Removes punctuation and splits into word array.
   */
  private parseWords(text: string): string[] {
    if (!text || text.trim() === "") {
      console.warn("Whisper returned empty transcription");
      return [];
    }

    // Remove punctuation (keep only letters, numbers, spaces, hyphens, apostrophes)
    let cleaned = text.replace(/[^\w\s'-]/g, "");

    // Convert to lowercase for consistency
    cleaned = cleaned.toLowerCase();

    // Split by whitespace
    const words = cleaned
      .trim()
      .split(/\s+/)
      .filter((word) => word.length > 0);

    console.log(`Parsed ${words.length} words from transcription`);
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
      console.log("Unloading word extraction model...");
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
export default ClientWordExtractor.getInstance();
