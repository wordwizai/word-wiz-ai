import { useRef, useCallback } from "react";

/**
 * Hook for iOS-compatible audio playback that handles Safari's autoplay restrictions
 * Must be initialized during a user gesture (like recording) to work on iOS
 */
export const useIOSCompatibleAudio = () => {
  const audioContextRef = useRef<AudioContext | null>(null);
  const isInitializedRef = useRef(false);

  /**
   * Initialize the audio context during a user gesture (e.g., when recording starts)
   * This is required for iOS to allow programmatic audio playback later
   */
  const initializeAudioContext = useCallback(() => {
    try {
      if (!audioContextRef.current || audioContextRef.current.state === 'closed') {
        audioContextRef.current = new (window.AudioContext || (window as typeof window & { webkitAudioContext?: typeof AudioContext }).webkitAudioContext)();
      }
      
      // Resume context if it's suspended (required for iOS)
      if (audioContextRef.current.state === 'suspended') {
        audioContextRef.current.resume();
      }
      
      isInitializedRef.current = true;
    } catch (error) {
      console.error('Failed to initialize audio context:', error);
    }
  }, []);

  /**
   * Play audio using iOS-compatible approach
   * Falls back to standard HTML5 Audio if AudioContext fails
   */
  const playAudio = useCallback(async (audioUrl: string) => {
    try {
      // Try AudioContext approach first (better for iOS)
      if (audioContextRef.current && isInitializedRef.current) {
        try {
          const response = await fetch(audioUrl);
          const arrayBuffer = await response.arrayBuffer();
          const audioBuffer = await audioContextRef.current.decodeAudioData(arrayBuffer);
          
          const source = audioContextRef.current.createBufferSource();
          source.buffer = audioBuffer;
          source.connect(audioContextRef.current.destination);
          source.start(0);
          
          return; // Success, exit early
        } catch (contextError) {
          console.warn('AudioContext playback failed, falling back to HTML5 Audio:', contextError);
        }
      }

      // Fallback to HTML5 Audio API
      const audio = new Audio(audioUrl);
      
      // Set properties that help with iOS compatibility
      audio.preload = 'auto';
      audio.volume = 1.0;
      
      // Handle play promise for browsers that return one
      const playPromise = audio.play();
      if (playPromise !== undefined) {
        await playPromise;
      }
    } catch (error) {
      console.error('Audio playback failed:', error);
      
      // Show user a message that they can tap to play audio manually
      console.warn('Audio autoplay blocked. User will need to tap to hear feedback.');
    }
  }, []);

  /**
   * Check if audio context is properly initialized
   */
  const isAudioReady = useCallback(() => {
    return isInitializedRef.current && 
           audioContextRef.current && 
           audioContextRef.current.state !== 'closed';
  }, []);

  return {
    initializeAudioContext,
    playAudio,
    isAudioReady,
  };
};