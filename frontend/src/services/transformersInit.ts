// Transformers.js and the ONNX runtime it bundles are most of the practice
// page's JavaScript. They used to be imported up front, so every practice
// page waited on them even when the in-browser model wasn't used. Now they
// download the first time a model is loaded, and are configured once then.

type Transformers = typeof import("@huggingface/transformers");

let loading: Promise<Transformers> | null = null;

function configure(env: Transformers["env"]) {
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
}

/** Transformers.js, downloaded and configured on first use. */
export function loadTransformers(): Promise<Transformers> {
  if (!loading) {
    loading = import("@huggingface/transformers")
      .then((transformers) => {
        configure(transformers.env);
        return transformers;
      })
      .catch((error) => {
        // Let the next model load try the download again.
        loading = null;
        throw error;
      });
  }
  return loading;
}
