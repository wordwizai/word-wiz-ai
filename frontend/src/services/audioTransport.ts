/**
 * Transport Abstraction Layer for Audio Analysis
 *
 * Provides a unified interface for sending audio analysis requests
 * via either WebSocket (persistent connection) or SSE (per-request connection).
 */

import { API_URL, WS_URL } from "@/api";

export interface AudioAnalysisEvent {
  type:
    | "processing_started"
    | "analysis"
    | "gpt_response"
    | "audio_feedback_file"
    | "error"
    | "pong";
  data: any;
  filename?: string;
  mimetype?: string;
}

export interface TransportOptions {
  token: string;
  sessionId: number;
  onEvent: (event: AudioAnalysisEvent) => void;
  onError: (error: string) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
}

export interface AudioTransport {
  connect(options: TransportOptions): Promise<void>;
  sendAudio(
    file: File,
    sentence: string,
    clientPhonemes?: string[][] | null,
    clientWords?: string[] | null
  ): Promise<void>;
  disconnect(): void;
  isConnected(): boolean;
}

/**
 * WebSocket-based transport with persistent connection
 */
export class WebSocketTransport implements AudioTransport {
  private ws: WebSocket | null = null;
  private options: TransportOptions | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private pingInterval: NodeJS.Timeout | null = null;
  private isManualDisconnect = false;

  async connect(options: TransportOptions): Promise<void> {
    this.options = options;
    this.isManualDisconnect = false;

    return new Promise((resolve, reject) => {
      try {
        // Construct WebSocket URL with token as query param
        // Use WS_URL (direct connection) to bypass nginx buffering
        const wsProtocol =
          window.location.protocol === "https:" ? "wss:" : "ws:";
        const wsUrl = WS_URL.replace(/^https?:/, wsProtocol);
        const url = `${wsUrl}/ai/ws/audio-analysis?token=${encodeURIComponent(
          options.token
        )}`;

        console.log("🔌 Connecting to WebSocket:", url);
        this.ws = new WebSocket(url);

        this.ws.onopen = () => {
          console.log("✅ WebSocket connected");
          this.reconnectAttempts = 0;
          this.startPingInterval();
          options.onConnect?.();
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data) as AudioAnalysisEvent;

            // Handle pong (heartbeat response)
            if (message.type === "pong") {
              return;
            }

            // Emit event to handler
            options.onEvent(message);
          } catch (err) {
            console.error("Failed to parse WebSocket message:", err);
            options.onError("Failed to parse server message");
          }
        };

        this.ws.onerror = (error) => {
          console.error("❌ WebSocket error:", error);
          reject(new Error("WebSocket connection failed"));
        };

        this.ws.onclose = (event) => {
          console.log("🔌 WebSocket closed:", event.code, event.reason);
          this.stopPingInterval();
          options.onDisconnect?.();

          // Auto-reconnect if not manually disconnected
          if (
            !this.isManualDisconnect &&
            this.reconnectAttempts < this.maxReconnectAttempts
          ) {
            this.scheduleReconnect();
          }
        };
      } catch (err) {
        reject(err);
      }
    });
  }

  async sendAudio(
    file: File,
    sentence: string,
    clientPhonemes?: string[][] | null,
    clientWords?: string[] | null
  ): Promise<void> {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error("WebSocket not connected");
    }

    // Convert File to base64
    const base64Audio = await this.fileToBase64(file);

    // Send message
    const message = {
      type: "analyze_audio",
      audio_base64: base64Audio,
      attempted_sentence: sentence,
      session_id: this.options?.sessionId,
      filename: file.name,
      content_type: file.type,
      client_phonemes: clientPhonemes,
      client_words: clientWords,
    };

    console.log("📤 Sending audio via WebSocket:", {
      filename: file.name,
      size: file.size,
      hasClientPhonemes: !!clientPhonemes,
      hasClientWords: !!clientWords,
    });

    this.ws.send(JSON.stringify(message));
  }

  disconnect(): void {
    this.isManualDisconnect = true;
    this.stopPingInterval();

    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    this.options = null;
  }

  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }

  private async fileToBase64(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        const base64 = (reader.result as string).split(",")[1];
        resolve(base64);
      };
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  }

  private startPingInterval(): void {
    // Send ping every 30 seconds to keep connection alive
    this.pingInterval = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: "ping" }));
      }
    }, 30000);
  }

  private stopPingInterval(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  private scheduleReconnect(): void {
    // Exponential backoff: 1s, 2s, 4s, 8s, 16s
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 16000);
    this.reconnectAttempts++;

    console.log(
      `🔄 Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`
    );

    this.reconnectTimeout = setTimeout(() => {
      if (this.options && !this.isManualDisconnect) {
        this.connect(this.options).catch((err) => {
          console.error("Reconnection failed:", err);
          this.options?.onError("Connection lost. Please refresh the page.");
        });
      }
    }, delay);
  }
}

/**
 * SSE-based transport (creates new connection per request)
 */
export class SSETransport implements AudioTransport {
  private options: TransportOptions | null = null;
  private abortController: AbortController | null = null;

  async connect(options: TransportOptions): Promise<void> {
    this.options = options;
    // SSE doesn't need upfront connection, just store options
    options.onConnect?.();
  }

  async sendAudio(
    file: File,
    sentence: string,
    clientPhonemes?: string[][] | null,
    clientWords?: string[] | null
  ): Promise<void> {
    if (!this.options) {
      throw new Error("Transport not initialized");
    }

    // Create new abort controller for this request
    this.abortController = new AbortController();

    const formData = new FormData();
    formData.append("audio_file", file);
    formData.append("attempted_sentence", sentence);
    formData.append("session_id", this.options.sessionId.toString());

    // Determine endpoint based on client phonemes
    const url = clientPhonemes
      ? `${API_URL}/ai/analyze-audio-with-phonemes`
      : `${API_URL}/ai/analyze-audio`;

    // Add client data if available
    if (clientPhonemes) {
      formData.append("client_phonemes", JSON.stringify(clientPhonemes));
    }
    if (clientWords) {
      formData.append("client_words", JSON.stringify(clientWords));
    }

    console.log("📤 Sending audio via SSE:", {
      filename: file.name,
      size: file.size,
      endpoint: url,
      hasClientPhonemes: !!clientPhonemes,
      hasClientWords: !!clientWords,
    });

    try {
      const response = await fetch(url, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${this.options.token}`,
        },
        body: formData,
        signal: this.abortController.signal,
      });

      if (!response.ok) {
        throw new Error(await response.text());
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (reader) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        let boundary = buffer.indexOf("\n\n");
        while (boundary !== -1) {
          const rawEvent = buffer.slice(0, boundary).trim();
          buffer = buffer.slice(boundary + 2);

          if (rawEvent.startsWith("data: ")) {
            try {
              const event = JSON.parse(rawEvent.slice(6)) as AudioAnalysisEvent;
              this.options.onEvent(event);
            } catch (err) {
              console.error("Failed to parse SSE message:", err);
            }
          }

          boundary = buffer.indexOf("\n\n");
        }
      }
    } catch (err: any) {
      if (err.name === "AbortError") {
        console.log("SSE request aborted");
        return;
      }
      this.options.onError(err.message);
      throw err;
    }
  }

  disconnect(): void {
    if (this.abortController) {
      this.abortController.abort();
      this.abortController = null;
    }
    this.options?.onDisconnect?.();
    this.options = null;
  }

  isConnected(): boolean {
    // SSE is always "connected" if options are set (creates connection per request)
    return this.options !== null;
  }
}

/**
 * Helper to decode base64 to blob (for audio feedback)
 */
export function b64toBlob(
  b64Data: string,
  contentType = "",
  sliceSize = 512
): Blob {
  const byteCharacters = atob(b64Data);
  const byteArrays = [];

  for (let offset = 0; offset < byteCharacters.length; offset += sliceSize) {
    const slice = byteCharacters.slice(offset, offset + sliceSize);
    const byteNumbers = new Array(slice.length)
      .fill(0)
      .map((_, i) => slice.charCodeAt(i));
    byteArrays.push(new Uint8Array(byteNumbers));
  }

  return new Blob(byteArrays, { type: contentType });
}
