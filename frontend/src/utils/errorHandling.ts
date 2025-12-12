import { toast } from "sonner";

export enum ErrorCategory {
  NETWORK = "network",
  AUTHENTICATION = "authentication",
  AUDIO_PROCESSING = "audio_processing",
  MODEL_LOADING = "model_loading",
  AUDIO_PLAYBACK = "audio_playback",
  STREAM_PARSING = "stream_parsing",
  UNKNOWN = "unknown",
}

interface ErrorMessage {
  title: string;
  description: string;
  action?: string;
}

const ERROR_MESSAGES: Record<ErrorCategory, ErrorMessage> = {
  [ErrorCategory.NETWORK]: {
    title: "Connection Error",
    description: "Unable to connect to the server. Please check your internet connection.",
    action: "Try again in a moment",
  },
  [ErrorCategory.AUTHENTICATION]: {
    title: "Authentication Required",
    description: "You need to be logged in to use this feature.",
    action: "Please sign in again",
  },
  [ErrorCategory.AUDIO_PROCESSING]: {
    title: "Audio Processing Failed",
    description: "We couldn't analyze your recording. Please try recording again.",
    action: "Check your microphone and try again",
  },
  [ErrorCategory.MODEL_LOADING]: {
    title: "Loading Failed",
    description: "Failed to load speech recognition models.",
    action: "Refresh the page to try again",
  },
  [ErrorCategory.AUDIO_PLAYBACK]: {
    title: "Playback Error",
    description: "Unable to play audio feedback.",
    action: "Check your device volume and try again",
  },
  [ErrorCategory.STREAM_PARSING]: {
    title: "Processing Error",
    description: "An error occurred while processing your request.",
    action: "Please try again",
  },
  [ErrorCategory.UNKNOWN]: {
    title: "Something Went Wrong",
    description: "An unexpected error occurred.",
    action: "Please try again",
  },
};

/**
 * Categorize error based on error message or type
 */
export function categorizeError(error: string | Error): ErrorCategory {
  const message = typeof error === "string" ? error : error.message;
  const lowerMessage = message.toLowerCase();

  if (lowerMessage.includes("not authenticated") || lowerMessage.includes("authentication")) {
    return ErrorCategory.AUTHENTICATION;
  }
  if (lowerMessage.includes("network") || lowerMessage.includes("connect") || lowerMessage.includes("timeout")) {
    return ErrorCategory.NETWORK;
  }
  // Check for playback errors before general audio errors (more specific first)
  if (lowerMessage.includes("play") && lowerMessage.includes("audio")) {
    return ErrorCategory.AUDIO_PLAYBACK;
  }
  // Check for model/loading errors before general audio errors
  if (lowerMessage.includes("model") || lowerMessage.includes("load")) {
    return ErrorCategory.MODEL_LOADING;
  }
  if (lowerMessage.includes("parse") || lowerMessage.includes("sse")) {
    return ErrorCategory.STREAM_PARSING;
  }
  // General audio errors checked last
  if (lowerMessage.includes("audio") || lowerMessage.includes("recording")) {
    return ErrorCategory.AUDIO_PROCESSING;
  }

  return ErrorCategory.UNKNOWN;
}

/**
 * Display error toast with user-friendly message
 */
export function showErrorToast(error: string | Error, category?: ErrorCategory) {
  const errorCategory = category || categorizeError(error);
  const errorMessage = ERROR_MESSAGES[errorCategory];

  // Build description with action on separate line if present
  const descriptionParts = [errorMessage.description];
  if (errorMessage.action) {
    descriptionParts.push(errorMessage.action);
  }

  toast.error(errorMessage.title, {
    description: descriptionParts.join("\n\n"),
  });

  // Log detailed error for debugging
  console.error(`[${errorCategory}]`, error);
}

/**
 * Specialized toast helpers
 */
export function showNetworkError(error?: string | Error) {
  showErrorToast(error || "Network error", ErrorCategory.NETWORK);
}

export function showAudioError(error?: string | Error) {
  showErrorToast(error || "Audio processing error", ErrorCategory.AUDIO_PROCESSING);
}

export function showAuthError(error?: string | Error) {
  showErrorToast(error || "Authentication error", ErrorCategory.AUTHENTICATION);
}

export function showModelError(error?: string | Error) {
  showErrorToast(error || "Model loading error", ErrorCategory.MODEL_LOADING);
}

export function showAudioPlaybackError(error?: string | Error) {
  showErrorToast(error || "Audio playback error", ErrorCategory.AUDIO_PLAYBACK);
}

/**
 * Show info toast (for non-error notifications)
 */
export function showInfoToast(title: string, description?: string) {
  toast.info(title, { description });
}

/**
 * Show success toast
 */
export function showSuccessToast(title: string, description?: string) {
  toast.success(title, { description });
}
