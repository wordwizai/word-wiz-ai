import { env } from "@huggingface/transformers";

// Configure HuggingFace authentication token globally
const hfToken = import.meta.env.VITE_HUGGINGFACE_TOKEN;
if (hfToken) {
  (env as any).customHeaders = {
    Authorization: `Bearer ${hfToken}`,
  };
  console.log("🔑 HuggingFace token configured");
} else {
  console.warn("⚠️ No HuggingFace token found - may encounter 401 errors");
}

// Enable multi-threading for faster inference (requires crossOriginIsolated headers)
if (env.backends?.onnx?.wasm) {
  const numThreads = navigator.hardwareConcurrency || 4;
  env.backends.onnx.wasm.numThreads = numThreads;
  console.log(
    `🚀 WASM configured for ${numThreads} threads (will fall back to single-thread if crossOriginIsolated not enabled)`
  );
}

// Log WebGPU availability for inference acceleration
if ("gpu" in navigator) {
  console.log("🎮 WebGPU detected - will attempt to use GPU acceleration");
} else {
  console.log("💻 WebGPU not available, using CPU (WASM)");
}
