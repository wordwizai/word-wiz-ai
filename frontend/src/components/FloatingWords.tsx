import { motion, useReducedMotion } from "framer-motion";
import { useEffect, useState } from "react";

interface FloatingWord {
  id: string;
  word: string;
  x: number;
  y: number;
  duration: number;
  delay: number;
  size: number;
  color: string;
}

const WORDS = [
  "cat",
  "dog",
  "run",
  "jump",
  "play",
  "read",
  "fun",
  "book",
  "learn",
  "grow",
];

const COLORS = [
  "text-purple-300/20",
  "text-pink-300/20",
  "text-blue-300/20",
  "text-green-300/20",
  "text-yellow-300/20",
];

const FloatingWords = () => {
  const prefersReducedMotion = useReducedMotion();
  const [floatingWords, setFloatingWords] = useState<FloatingWord[]>([]);

  useEffect(() => {
    const generateWords = (): FloatingWord[] => {
      return Array.from({ length: 12 }, (_, i) => ({
        id: `word-${i}`,
        word: WORDS[Math.floor(Math.random() * WORDS.length)],
        x: Math.random() * 100,
        y: Math.random() * 100,
        duration: 15 + Math.random() * 10,
        delay: Math.random() * 2,
        size: 1.5 + Math.random() * 2,
        color: COLORS[Math.floor(Math.random() * COLORS.length)],
      }));
    };

    setFloatingWords(generateWords());
  }, []); // Empty array is intentional - we only want to generate words once on mount

  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {!prefersReducedMotion && floatingWords.map((fw) => (
        <motion.div
          key={fw.id}
          className={`absolute font-bold ${fw.color}`}
          style={{
            left: `${fw.x}%`,
            top: `${fw.y}%`,
            fontSize: `${fw.size}rem`,
          }}
          animate={{
            y: [0, -30, 0],
            x: [0, 15, 0],
            rotate: [0, 5, 0, -5, 0],
            opacity: [0.3, 0.6, 0.3],
          }}
          transition={{
            duration: fw.duration,
            delay: fw.delay,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        >
          {fw.word}
        </motion.div>
      ))}
    </div>
  );
};

export default FloatingWords;
