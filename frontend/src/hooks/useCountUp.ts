import { useEffect, useState } from "react";

/**
 * Custom hook for animating number counting up from 0 to target value
 * @param target - The target number to count up to
 * @param duration - Duration of the animation in milliseconds (default: 1000ms)
 * @returns The current animated value
 */
export const useCountUp = (target: number, duration: number = 1000): number => {
  const [count, setCount] = useState(0);

  useEffect(() => {
    // Reset to 0 when target changes
    setCount(0);

    if (target === 0) {
      return;
    }

    const startTime = Date.now();

    const timer = setInterval(() => {
      const now = Date.now();
      const progress = Math.min((now - startTime) / duration, 1);

      // Easing function for smooth animation (easeOutCubic)
      const easedProgress = 1 - Math.pow(1 - progress, 3);

      const currentCount = Math.floor(easedProgress * target);
      setCount(currentCount);

      if (progress >= 1) {
        setCount(target);
        clearInterval(timer);
      }
    }, 16); // ~60fps

    return () => clearInterval(timer);
  }, [target, duration]);

  return count;
};
