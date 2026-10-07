import { useRef, useState, useEffect, useCallback } from "react";
import hark from "hark";
import { toast } from "sonner";
import { WarmMic } from "@/lib/warmMic";

// Stop on our own if the reader never pauses (or the room never goes quiet
// enough for hark to notice). Longer than any practice sentence takes.
const MAX_RECORDING_MS = 30_000;
// Anything shorter is an accidental double tap, not a reading attempt.
const MIN_RECORDING_SECONDS = 0.6;
// Peak sample level below which we treat the clip as silence (about -40 dBFS).
const SILENCE_PEAK = 0.01;
const SILENCE_DELAY_MS = 2000;
// A grown-up usually has to act on these, so give them time to read it.
const HELP_TOAST_MS = 10_000;
// An open mic keeps the browser's recording indicator on, so let it go once
// nobody has tapped for a while. The next tap then opens it from cold.
const IDLE_RELEASE_MS = 2 * 60_000;

/** Explain a getUserMedia failure in words a parent can act on. */
function describeMicError(error: unknown): { title: string; description: string } {
  const name = error instanceof DOMException ? error.name : "";
  switch (name) {
    case "NotAllowedError":
    case "SecurityError":
      return {
        title: "Microphone is off",
        description:
          "Click the lock or microphone icon in the browser's address bar, allow the microphone for this site, then tap the microphone again.",
      };
    case "NotFoundError":
    case "OverconstrainedError":
      return {
        title: "No microphone found",
        description: "Plug in a microphone or check that it's turned on, then tap the microphone again.",
      };
    case "NotReadableError":
    case "AbortError":
      return {
        title: "Microphone is busy",
        description: "Another app (like a video call) is using the microphone. Close it, then tap the microphone again.",
      };
    default:
      return {
        title: "Microphone didn't start",
        description: "Please tap the microphone to try again.",
      };
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

// One open microphone and the audio graph reading it, kept open between
// recordings (see WarmMic). `onChunk` is set only while a recording is
// collecting samples; the rest of the time they're dropped.
type Mic = {
  stream: MediaStream;
  audioContext: AudioContext;
  source: MediaStreamAudioSourceNode;
  processor: ScriptProcessorNode;
  onChunk: ((samples: Float32Array) => void) | null;
};

async function openMic(onLost: () => void): Promise<Mic> {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  stream.getAudioTracks()[0]?.addEventListener("ended", onLost);
  const audioContext = new AudioContext();
  const source = audioContext.createMediaStreamSource(stream);
  const processor = audioContext.createScriptProcessor(4096, 1, 1);
  const mic: Mic = { stream, audioContext, source, processor, onChunk: null };
  processor.onaudioprocess = (event) =>
    mic.onChunk?.(event.inputBuffer.getChannelData(0));
  source.connect(processor);
  processor.connect(audioContext.destination);
  return mic;
}

function closeMic(mic: Mic) {
  mic.processor.disconnect();
  mic.source.disconnect();
  mic.stream.getTracks().forEach((track) => track.stop());
  mic.audioContext.close();
}

async function micAlreadyAllowed() {
  try {
    const status = await navigator.permissions.query({ name: "microphone" });
    return status.state === "granted";
  } catch {
    // Older Safari and Firefox can't be asked. Wait for the tap.
    return false;
  }
}

export function useAudioRecorder(onFinish: (audioFile: File) => void) {
  const [isRecording, setIsRecording] = useState(false);
  const stopHandlerRef = useRef<(() => Promise<void>) | null>(null);
  // Ends the recording in progress (hark, timers, sample collection)
  // without sending anything. The mic itself stays open.
  const teardownRef = useRef<(() => void) | null>(null);
  // Guards the async gap in getUserMedia so a double tap can't start two
  // recordings.
  const busyRef = useRef(false);
  // Live input loudness (RMS, roughly 0-0.3 for speech). A ref rather than
  // state: it changes ~12 times a second and only the level meter reads it.
  const levelRef = useRef(0);
  const [mic] = useState(() => new WarmMic(openMic, closeMic, IDLE_RELEASE_MS));

  useEffect(() => {
    let active = true;
    // If the mic is already allowed, open it now so the first tap is
    // instant too.
    const warmIfAllowed = () =>
      micAlreadyAllowed().then((allowed) => {
        if (allowed && active && document.visibilityState === "visible") {
          void mic.warm();
        }
      });
    // Don't hold the mic for a background tab.
    const onVisibilityChange = () => {
      if (document.visibilityState === "hidden") mic.closeWhenIdle();
      else void warmIfAllowed();
    };
    // The open mic stays on the device it started with, so follow a
    // headset plugged in mid-practice.
    const onDeviceChange = () => {
      if (mic.current && !busyRef.current) {
        mic.close();
        void mic.warm();
      }
    };
    void warmIfAllowed();
    document.addEventListener("visibilitychange", onVisibilityChange);
    navigator.mediaDevices?.addEventListener("devicechange", onDeviceChange);
    return () => {
      active = false;
      document.removeEventListener("visibilitychange", onVisibilityChange);
      navigator.mediaDevices?.removeEventListener("devicechange", onDeviceChange);
      // Leaving the page mid-recording: release the mic, don't analyze.
      teardownRef.current?.();
      mic.close();
    };
  }, [mic]);

  const startRecording = useCallback(async () => {
    if (busyRef.current) return;
    busyRef.current = true;

    if (!navigator.mediaDevices?.getUserMedia) {
      // Old browser, or the page isn't served over https.
      toast.error("Can't record here", {
        description: "This browser can't record audio. Please try the latest Chrome, Edge, or Safari.",
        duration: HELP_TOAST_MS,
      });
      busyRef.current = false;
      return;
    }

    // Resume while still inside the tap. A mic opened on page load, before
    // any tap, can have a suspended context, which delivers no samples.
    void mic.current?.audioContext.resume().catch(() => {});

    let opened: Mic | null;
    try {
      opened = await mic.startUsing();
    } catch (error) {
      console.error("Error starting audio recording:", error);
      // Usually a blocked or missing microphone. Without this the button
      // just did nothing, which a child can't diagnose.
      const { title, description } = describeMicError(error);
      toast.error(title, { description, duration: HELP_TOAST_MS });
      busyRef.current = false;
      return;
    }
    if (!opened) {
      // Closed while it was opening: the page was left or hidden.
      busyRef.current = false;
      return;
    }
    const recordingMic = opened;
    const { stream, audioContext } = recordingMic;
    // A context first made by this tap was created after an await, so some
    // browsers (Safari especially) start it suspended; a suspended context
    // delivers no samples and the recording comes out empty.
    if (audioContext.state !== "running") {
      await audioContext.resume().catch(() => {});
    }

    const audioChunks: Float32Array[] = [];

    recordingMic.onChunk = (inputData) => {
      audioChunks.push(new Float32Array(inputData));
      let sum = 0;
      for (let i = 0; i < inputData.length; i++) sum += inputData[i] ** 2;
      levelRef.current = Math.sqrt(sum / inputData.length);
    };

    setIsRecording(true);

    let silenceTimer: ReturnType<typeof setTimeout> | null = null;
    let heardSpeech = false;
    const speechEvents = hark(stream, {
      threshold: -50,
      interval: 50,
      // Otherwise hark makes its own context, which nothing resumes in
      // Safari.
      audioContext,
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
      // hark polls on an interval until stopped; it used to keep running
      // after every recording. Stop it before clearing silenceTimer, because
      // stop() fires one last stopped_speaking, and the timer that sets
      // would otherwise end the next recording 2 s in.
      speechEvents.stop();
      if (silenceTimer) clearTimeout(silenceTimer);
      clearTimeout(maxTimer);
      levelRef.current = 0;
      recordingMic.onChunk = null;
      mic.stopUsing();
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
        toast("That was too short", {
          description: "Tap the microphone, read the whole sentence out loud, then wait a moment.",
        });
        return;
      }
      if (!heardSpeech && peak < SILENCE_PEAK) {
        toast.error("We didn't hear anything", {
          description: "Check that the microphone is on and not muted, then tap it and read the sentence out loud.",
          duration: HELP_TOAST_MS,
        });
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
  }, [onFinish, mic]);

  const stopRecording = useCallback(() => {
    stopHandlerRef.current?.();
  }, []);

  return { isRecording, startRecording, stopRecording, levelRef };
}
