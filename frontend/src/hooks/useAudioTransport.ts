/**
 * Hook for managing audio transport (WebSocket or SSE)
 *
 * Provides a unified interface for audio analysis that abstracts
 * the underlying transport mechanism.
 */

import { useCallback, useContext, useEffect, useRef, useState } from "react";
import { AuthContext } from "@/contexts/AuthContext";
import {
  WebSocketTransport,
  SSETransport,
  b64toBlob,
} from "@/services/audioTransport";
import type {
  AudioTransport,
  AudioAnalysisEvent,
} from "@/services/audioTransport";
import {
  showErrorToast,
  showNetworkError,
  showPracticeErrorToast,
} from "@/utils/errorHandling";

export interface UseAudioTransportOptions {
  onAnalysis?: (data: any) => void;
  /** Called immediately with locally-generated feedback text (before TTS is ready). */
  onFeedback?: (data: { text: string; ssml?: string }) => void;
  /** Called when GPT returns the next practice sentence (arrives in parallel with audio). */
  onNextSentence?: (data: { sentence: any }) => void;
  onAudioFeedback?: (audioUrl: string) => void;
  onError?: (error: string) => void;
  onProcessingStart?: () => void;
  onProcessingEnd?: () => void;
  sessionId: number;
  useWebSocket?: boolean; // If true, use WebSocket; otherwise SSE
}

export function useAudioTransport(options: UseAudioTransportOptions) {
  const { token } = useContext(AuthContext);
  const transportRef = useRef<AudioTransport | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  // Use refs for callbacks to avoid recreating transport on every render
  const optionsRef = useRef(options);
  useEffect(() => {
    optionsRef.current = options;
  }, [options]);

  const handleEvent = useCallback((event: AudioAnalysisEvent) => {
    const opts = optionsRef.current;
    console.log("📨 Transport event:", event.type);

    switch (event.type) {
      case "processing_started":
        setIsProcessing(true);
        opts.onProcessingStart?.();
        break;

      case "analysis":
        setIsProcessing(false);
        opts.onProcessingEnd?.();
        opts.onAnalysis?.(event.data);
        break;

      case "feedback":
        opts.onFeedback?.(event.data);
        break;

      case "next_sentence":
        opts.onNextSentence?.(event.data);
        break;

      case "audio_feedback_file":
        if (event.data && event.filename && event.mimetype) {
          const blob = b64toBlob(event.data, event.mimetype);
          const audioUrl = URL.createObjectURL(blob);
          opts.onAudioFeedback?.(audioUrl);
        }
        break;

      case "error": {
        setIsProcessing(false);
        opts.onProcessingEnd?.();
        const errorMsg =
          typeof event.data === "string"
            ? event.data
            : event.data?.message || event.data?.error || "An error occurred";
        // The backend writes these for parents and kids, so show them as-is.
        showPracticeErrorToast(errorMsg);
        opts.onError?.(errorMsg);
        break;
      }

      case "pong":
        // Heartbeat response, ignore
        break;

      default:
        console.warn("Unknown event type:", event);
    }
  }, []); // Stable callback

  // Initialize transport
  useEffect(() => {
    if (!token) return;

    const transport = options.useWebSocket
      ? new WebSocketTransport()
      : new SSETransport();
    let cancelled = false;

    transport
      .connect({
        token,
        sessionId: options.sessionId,
        onEvent: handleEvent,
        onError: (error) => {
          console.error("Transport error:", error);
          showErrorToast(error);
          optionsRef.current.onError?.(error);
        },
        onConnect: () => {
          console.log("✅ Transport connected");
          setIsConnected(true);
        },
        onDisconnect: () => {
          console.log("🔌 Transport disconnected");
          setIsConnected(false);
        },
      })
      .catch((err) => {
        // Cleanup below closes a socket that may still be connecting (React
        // StrictMode's double mount in dev, or a session/setting change).
        // That rejection is expected and must not surface as a network error.
        if (cancelled) return;
        console.error("Failed to initialize transport:", err);
        showNetworkError(err);
        optionsRef.current.onError?.("Failed to connect. Please try again.");
      });

    transportRef.current = transport;

    return () => {
      cancelled = true;
      transport.disconnect();
      transportRef.current = null;
    };
  }, [token, options.sessionId, options.useWebSocket, handleEvent]);

  const sendAudio = useCallback(
    async (
      file: File,
      sentence: string,
      clientPhonemes?: string[][] | null,
      clientWords?: string[] | null
    ) => {
      const transport = transportRef.current;

      // Nothing upstream catches a throw here (the recorder fires and
      // forgets), so a dropped connection used to discard the recording
      // silently. Tell the reader instead; the socket reconnects on its own.
      const lostConnection = () => {
        const message =
          "We lost the connection for a moment. Please tap the mic and read the sentence again.";
        showPracticeErrorToast(message);
        optionsRef.current.onError?.(message);
      };

      if (!transport || !transport.isConnected()) {
        lostConnection();
        return;
      }

      setIsProcessing(true);

      try {
        await transport.sendAudio(file, sentence, clientPhonemes, clientWords);
      } catch (err: any) {
        setIsProcessing(false);
        console.error("Failed to send audio:", err);
        lostConnection();
      }
    },
    []
  );

  const disconnect = useCallback(() => {
    transportRef.current?.disconnect();
    transportRef.current = null;
    setIsConnected(false);
    setIsProcessing(false);
  }, []);

  return {
    sendAudio,
    disconnect,
    isConnected,
    isProcessing,
  };
}
