import { useCallback, useEffect, useRef, useState } from "react";
import { showAudioPlaybackError } from "@/utils/errorHandling";

// Plays the tutor's spoken feedback and keeps it around so a child who
// can't read the feedback text yet can hear it again.
export function useFeedbackAudio() {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [hasAudio, setHasAudio] = useState(false);
  // True while the feedback is coming out of the speakers, so the mascot
  // can talk along with it.
  const [isPlaying, setIsPlaying] = useState(false);

  const start = (audio: HTMLAudioElement) =>
    audio.play().catch((error) => {
      console.error("[AudioFeedback] Failed to play audio:", error);
      showAudioPlaybackError(error);
    });

  const play = useCallback((url: string) => {
    audioRef.current?.pause();
    const audio = new Audio(url);
    // Only the current clip may change isPlaying. A replaced clip's late
    // pause event would otherwise cut the new clip's talking short.
    const track = (playing: boolean) => () => {
      if (audioRef.current === audio) setIsPlaying(playing);
    };
    audio.addEventListener("playing", track(true));
    audio.addEventListener("pause", track(false));
    audio.addEventListener("ended", track(false));
    audio.addEventListener("error", () => {
      console.error("[AudioFeedback] Playback error:", audio.error?.message);
      track(false)();
    });
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
    // The pause above is ignored by `track` once the ref is cleared.
    setIsPlaying(false);
  }, []);

  useEffect(() => () => audioRef.current?.pause(), []);

  return { play, replay: hasAudio ? replay : null, reset, isPlaying };
}
