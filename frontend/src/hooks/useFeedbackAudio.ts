import { useCallback, useEffect, useRef, useState } from "react";
import { showAudioPlaybackError } from "@/utils/errorHandling";

// Plays the tutor's spoken feedback and keeps it around so a child who
// can't read the feedback text yet can hear it again.
export function useFeedbackAudio() {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [hasAudio, setHasAudio] = useState(false);

  const start = (audio: HTMLAudioElement) =>
    audio.play().catch((error) => {
      console.error("[AudioFeedback] Failed to play audio:", error);
      showAudioPlaybackError(error);
    });

  const play = useCallback((url: string) => {
    audioRef.current?.pause();
    const audio = new Audio(url);
    audio.addEventListener("error", () =>
      console.error("[AudioFeedback] Playback error:", audio.error?.message)
    );
    audioRef.current = audio;
    setHasAudio(true);
    start(audio);
  }, []);

  const replay = useCallback(() => {
    const audio = audioRef.current;
    if (!audio) return;
    audio.currentTime = 0;
    start(audio);
  }, []);

  const reset = useCallback(() => {
    audioRef.current?.pause();
    audioRef.current = null;
    setHasAudio(false);
  }, []);

  useEffect(() => () => audioRef.current?.pause(), []);

  return { play, replay: hasAudio ? replay : null, reset };
}
