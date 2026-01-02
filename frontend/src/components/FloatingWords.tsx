import { motion } from "framer-motion";
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

const FloatingWords = () => {
  const words = [
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

  const colors = [
    "text-purple-300/20",
    "text-pink-300/20",
    "text-blue-300/20",
    "text-green-300/20",
    "text-yellow-300/20",
  ];

  const [floatingWords, setFloatingWords] = useState<FloatingWord[]>([]);

  useEffect(() => {
    const generateWords = () => {
      return Array.from({ length: 12 }, (_, i) => ({
        id: `word-${i}`,
        word: words[Math.floor(Math.random() * words.length)],
        x: Math.random() * 100,
        y: Math.random() * 100,
        duration: 15 + Math.random() * 10,
        delay: Math.random() * 2,
        size: 1.5 + Math.random() * 2,
        color: colors[Math.floor(Math.random() * colors.length)],
      }));
    };

    setFloatingWords(generateWords());
  }, []);

  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {floatingWords.map((fw) => (
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
