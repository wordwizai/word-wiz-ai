import { useRef, useState, useEffect, useCallback } from "react";
import hark from "hark";

// Stop on our own if the reader never pauses (or the room never goes quiet
// enough for hark to notice). Longer than any practice sentence takes.
const MAX_RECORDING_MS = 30_000;
// Anything shorter is an accidental double tap, not a reading attempt.
const MIN_RECORDING_SECONDS = 0.6;
// Peak sample level below which we treat the clip as silence (about -40 dBFS).
const SILENCE_PEAK = 0.01;
const SILENCE_DELAY_MS = 2000;

/** Explain a getUserMedia failure in words a parent can act on. */
function describeMicError(error: unknown): string {
  const name = error instanceof DOMException ? error.name : "";
  switch (name) {
    case "NotAllowedError":
    case "SecurityError":
      return "Word Wiz needs your microphone to hear you read. Click the lock or microphone icon in your browser's address bar, allow the microphone, then tap the mic again.";
    case "NotFoundError":
    case "OverconstrainedError":
      return "We couldn't find a microphone. Plug one in or check that it's turned on, then tap the mic again.";
    case "NotReadableError":
    case "AbortError":
      return "Your microphone is busy in another app (like a video call). Close that app, then tap the mic again.";
    default:
      return "We couldn't start the microphone. Please tap the mic to try again.";
  }
}

function encodeWAV(samples: Float32Array, sampleRate: number) {
  const buffer = new ArrayBuffer(44 + samples.length * 2);
  const view = new DataView(buffer);

  function writeString(view: DataView, offset: number, str: string) {
    for (let i = 0; i < str.length; i++) {
      view.setUint8(offset + i, str.charCodeAt(i));
    }
  }

  writeString(view, 0, "RIFF");
  view.setUint32(4, 36 + samples.length * 2, true);
  writeString(view, 8, "WAVE");
  writeString(view, 12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  writeString(view, 36, "data");
  view.setUint32(40, samples.length * 2, true);

  let offset = 44;
  for (let i = 0; i < samples.length; i++, offset += 2) {
    const s = Math.max(-1, Math.min(1, samples[i]));
    view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7fff, true);
  }

  return new Blob([view], { type: "audio/wav" });
}

export function useAudioRecorder(onFinish: (audioFile: File) => void) {
  const [isRecording, setIsRecording] = useState(false);
  // A problem to show next to the record button, or null.
  const [recorderError, setRecorderError] = useState<string | null>(null);
  const stopHandlerRef = useRef<(() => Promise<void>) | null>(null);
  // Releases the mic, audio graph, hark and timers without sending anything.
  const teardownRef = useRef<(() => void) | null>(null);
  // Guards the async gap in getUserMedia so a double tap can't open two mics.
  const busyRef = useRef(false);

  useEffect(() => {
    return () => {
      // Leaving the page mid-recording: release the mic, don't analyze.
      teardownRef.current?.();
    };
  }, []);

  const stopRecording = useCallback(() => {
    stopHandlerRef.current?.();
  }, []);

  const startRecording = useCallback(async () => {
    if (busyRef.current) return;
    busyRef.current = true;
    setRecorderError(null);

    if (!navigator.mediaDevices?.getUserMedia) {
      // Old browser, or the page isn't on https.
      setRecorderError(
        "This browser can't record audio. Please try the latest Chrome, Edge, or Safari.",
      );
      busyRef.current = false;
      return;
    }

    let stream: MediaStream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (error) {
      console.error("Error starting audio recording:", error);
      setRecorderError(describeMicError(error));
      busyRef.current = false;
      return;
    }

    const audioContext = new AudioContext();
    const source = audioContext.createMediaStreamSource(stream);

    const bufferSize = 4096;
    const processor = audioContext.createScriptProcessor(bufferSize, 1, 1);

    const audioChunks: Float32Array[] = [];

    processor.onaudioprocess = (event) => {
      const inputData = event.inputBuffer.getChannelData(0);
      audioChunks.push(new Float32Array(inputData));
    };

    source.connect(processor);
    processor.connect(audioContext.destination);

    setIsRecording(true);

    let silenceTimer: ReturnType<typeof setTimeout> | null = null;
    let heardSpeech = false;
    const speechEvents = hark(stream, {
      threshold: -50,
      interval: 50,
    });
    speechEvents.on("speaking", () => {
      heardSpeech = true;
      if (silenceTimer) clearTimeout(silenceTimer);
    });
    speechEvents.on("stopped_speaking", () => {
      silenceTimer = setTimeout(() => stopHandlerRef.current?.(), SILENCE_DELAY_MS);
    });
    const maxTimer = setTimeout(() => stopHandlerRef.current?.(), MAX_RECORDING_MS);

    let isStopping = false;

    const teardown = () => {
      if (silenceTimer) clearTimeout(silenceTimer);
      clearTimeout(maxTimer);
      speechEvents.stop();
      processor.disconnect();
      source.disconnect();
      stream.getTracks().forEach((track) => track.stop());
      audioContext.close();
      stopHandlerRef.current = null;
      teardownRef.current = null;
      busyRef.current = false;
    };

    const stopHandler = async () => {
      if (isStopping) return;
      isStopping = true;
      const originalSampleRate = audioContext.sampleRate;
      teardown();
      setIsRecording(false);

      const length = audioChunks.reduce((acc, cur) => acc + cur.length, 0);
      const mergedBuffer = new Float32Array(length);
      let offset = 0;
      let peak = 0;
      for (const chunk of audioChunks) {
        mergedBuffer.set(chunk, offset);
        offset += chunk.length;
        for (let i = 0; i < chunk.length; i++) {
          const v = Math.abs(chunk[i]);
          if (v > peak) peak = v;
        }
      }

      // Catch empty attempts here rather than spending a full (billed)
      // analysis on them and getting a confusing result back.
      if (length / originalSampleRate < MIN_RECORDING_SECONDS) {
        setRecorderError(
          "That was too short. Tap the mic, read the whole sentence out loud, then wait a moment.",
        );
        return;
      }
      if (!heardSpeech && peak < SILENCE_PEAK) {
        setRecorderError(
          "We didn't hear anything. Check that your microphone is on and not muted, then tap the mic and read the sentence out loud.",
        );
        return;
      }

      const offlineContext = new OfflineAudioContext(
        1,
        Math.floor((mergedBuffer.length * 16000) / originalSampleRate),
        16000,
      );

      const audioBuffer = offlineContext.createBuffer(
        1,
        mergedBuffer.length,
        originalSampleRate,
      );
      audioBuffer.getChannelData(0).set(mergedBuffer);

      const bufferSource = offlineContext.createBufferSource();
      bufferSource.buffer = audioBuffer;
      bufferSource.connect(offlineContext.destination);
      bufferSource.start(0);

      const renderedBuffer = await offlineContext.startRendering();

      const wavBlob = encodeWAV(renderedBuffer.getChannelData(0), 16000);
      const file = new File([wavBlob], "recording.wav", {
        type: "audio/wav",
      });
      onFinish(file);
    };

    stopHandlerRef.current = stopHandler;
    teardownRef.current = teardown;
  }, [onFinish]);

  return { isRecording, startRecording, stopRecording, recorderError };
}
