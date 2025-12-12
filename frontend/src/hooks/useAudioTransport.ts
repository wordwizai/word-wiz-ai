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
import { showErrorToast, showNetworkError } from "@/utils/errorHandling";

export interface UseAudioTransportOptions {
  onAnalysis?: (data: any) => void;
  onGptResponse?: (data: any) => void;
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

      case "gpt_response":
        opts.onGptResponse?.(event.data);
        break;

      case "audio_feedback_file":
        if (event.data && event.filename && event.mimetype) {
          const blob = b64toBlob(event.data, event.mimetype);
          const audioUrl = URL.createObjectURL(blob);
          opts.onAudioFeedback?.(audioUrl);
        }
        break;

      case "error":
        setIsProcessing(false);
        opts.onProcessingEnd?.();
        showErrorToast(event.data);
        opts.onError?.(event.data);
        break;

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
        console.error("Failed to initialize transport:", err);
        showNetworkError(err);
        optionsRef.current.onError?.("Failed to connect. Please try again.");
      });

    transportRef.current = transport;

    return () => {
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

      if (!transport || !transport.isConnected()) {
        throw new Error("Transport not connected");
      }

      setIsProcessing(true);

      try {
        await transport.sendAudio(file, sentence, clientPhonemes, clientWords);
      } catch (err: any) {
        setIsProcessing(false);
        console.error("Failed to send audio:", err);
        throw err;
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
