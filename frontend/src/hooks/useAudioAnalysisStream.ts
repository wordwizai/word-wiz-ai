import { useContext, useRef } from "react";
import { AuthContext } from "@/contexts/AuthContext"; // adjust to your project path
import { API_URL } from "@/api";

interface AudioAnalysisEvents {
  type: "analysis" | "gpt_response" | "audio_feedback_file";
  data: any;
  filename?: string;
  mimetype?: string;
}

interface UseAudioAnalysisStreamOptions {
  onAnalysis?: (data: any) => void;
  onGptResponse?: (data: any) => void;
  onAudioFeedback?: (
    objectUrl: string,
    meta: { filename: string; mimetype: string },
  ) => void;
  onError?: (err: string) => void;
  sessionId?: number;
}

export const useAudioAnalysisStream = (
  options?: UseAudioAnalysisStreamOptions,
) => {
  const { token } = useContext(AuthContext);
  const eventSourceRef = useRef<EventSource | null>(null);

  const start = (file: File, sentence: string) => {
    if (!token) {
      options?.onError?.("Not authenticated");
      return;
    }

    const formData = new FormData();
    formData.append("audio_file", file);
    formData.append("attempted_sentence", sentence);
    formData.append("session_id", options?.sessionId?.toString() || "");

    const url = `${API_URL}/ai/analyze-audio`;

    // Create a manual fetch POST to initialize the SSE
    fetch(url, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body: formData,
    })
      .then(async (response) => {
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
                const parsed: AudioAnalysisEvents = JSON.parse(
                  rawEvent.slice(6),
                );
                if (parsed.type === "analysis") {
                  options?.onAnalysis?.(parsed.data);
                } else if (parsed.type === "gpt_response") {
                  options?.onGptResponse?.(parsed.data);
                } else if (parsed.type === "audio_feedback_file") {
                  console.log(
                    "Received base64 audio length:",
                    parsed.data.length,
                  );
                  console.log("First 100 chars:", parsed.data.slice(0, 100));
                  const audioBlob = b64toBlob(
                    parsed.data,
                    parsed.mimetype || "audio/wav",
                  );
                  const objectUrl = URL.createObjectURL(audioBlob);
                  options?.onAudioFeedback?.(objectUrl, {
                    filename: parsed.filename || "feedback.wav",
                    mimetype: parsed.mimetype || "audio/wav",
                  });
                } else if (parsed.type === "error") {
                  console.error("SSE Error:", parsed.data);
                }
              } catch (err) {
                options?.onError?.("Failed to parse SSE message");
              }
            }

            boundary = buffer.indexOf("\n\n");
          }
        }
      })
      .catch((err) => {
        options?.onError?.(err.message);
      });
  };

  const stop = () => {
    eventSourceRef.current?.close?.();
    eventSourceRef.current = null;
  };

  return { start, stop };
};

// Helper to decode base64 to blob
function b64toBlob(b64Data: string, contentType = "", sliceSize = 512): Blob {
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
