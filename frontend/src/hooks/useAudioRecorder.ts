import { useRef, useState, useEffect, useCallback } from "react";
import hark from "hark";

export function useAudioRecorder(onFinish: (audioFile: File) => void) {
  const [isRecording, setIsRecording] = useState(false);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const stopHandlerRef = useRef<(() => Promise<void>) | null>(null);

  useEffect(() => {
    return () => {
      // Cleanup on unmount
      mediaStreamRef.current?.getTracks().forEach((track) => track.stop());
    };
  }, []);

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStreamRef.current = stream;

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
      const SILENCE_DELAY = 2000;
      const speechEvents = hark(stream, {
        threshold: -50,
        interval: 50,
      });
      speechEvents.on("speaking", () => {
        if (silenceTimer) clearTimeout(silenceTimer);
      });
      speechEvents.on("stopped_speaking", () => {
        silenceTimer = setTimeout(stopRecording, SILENCE_DELAY);
      });

      const stopHandler = async () => {
        processor.disconnect();
        source.disconnect();
        stream.getTracks().forEach((track) => track.stop());
        audioContext.close();

        const length = audioChunks.reduce((acc, cur) => acc + cur.length, 0);
        const mergedBuffer = new Float32Array(length);
        let offset = 0;
        for (const chunk of audioChunks) {
          mergedBuffer.set(chunk, offset);
          offset += chunk.length;
        }

        const originalSampleRate = audioContext.sampleRate;
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

        const wavBlob = encodeWAV(renderedBuffer.getChannelData(0), 16000);
        const file = new File([wavBlob], "recording.wav", {
          type: "audio/wav",
        });
        setIsRecording(false);
        onFinish(file);
      };

      stopHandlerRef.current = stopHandler;
    } catch (error) {
      setIsRecording(false);
      console.error("Error starting audio recording:", error);
    }
  }, [onFinish]);

  const stopRecording = useCallback(() => {
    stopHandlerRef.current?.();
  }, []);

  return { isRecording, startRecording, stopRecording };
}
