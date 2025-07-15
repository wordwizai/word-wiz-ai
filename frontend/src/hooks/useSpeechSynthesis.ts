import { useCallback, useRef } from "react";

export interface SpeakOptions {
  lang?: string;
  rate?: number;
  pitch?: number;
  volume?: number;
  voiceName?: string;
}

export function useSpeechSynthesis(defaultOptions?: SpeakOptions) {
  const synthRef = useRef(window.speechSynthesis);

  const speak = useCallback(
    (text: string, options?: SpeakOptions) => {
      const synth = synthRef.current;
      const utter = new window.SpeechSynthesisUtterance(text);

      const voices = synth.getVoices();
      let voice = voices[0];
      if (options?.voiceName) {
        const found = voices.find((v) => v.name === options.voiceName);
        if (found) voice = found;
      }
      utter.voice = voice;
      utter.lang = options?.lang || defaultOptions?.lang || "en-US";
      utter.rate = options?.rate ?? defaultOptions?.rate ?? 1;
      utter.pitch = options?.pitch ?? defaultOptions?.pitch ?? 1;
      utter.volume = options?.volume ?? defaultOptions?.volume ?? 1;

      synth.cancel();
      synth.speak(utter);
    },
    [defaultOptions],
  );

  return { speak, voices: synthRef.current.getVoices() };
}
