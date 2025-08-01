import { AnimatePresence, motion } from "framer-motion";
import { Badge } from "@/components/ui/badge";
import { useSpeechSynthesis } from "@/hooks/useSpeechSynthesis";
import { useEffect, useState } from "react";
import { Columns, Split, SplitSquareVertical, Text } from "lucide-react";
import { useTheme } from "@/contexts/ThemeContext";

interface WordBadgeProps {
  word: string;
  idx: number;
  showHighlighted: boolean;
  analysisPer?: number;
}

export const WordBadge = ({
  word,
  idx,
  showHighlighted,
  analysisPer,
}: WordBadgeProps) => {
  const PHONICS_CHUNKS = [
    // Vowel teams & diphthongs
    "ai",
    "ay",
    "au",
    "aw",
    "ea",
    "ee",
    "ei",
    "ey",
    "ie",
    "oa",
    "oe",
    "oo",
    "ou",
    "ow",
    "ue",
    "ui",
    "ew",
    "oy",
    "oi",
    "igh",

    // R-controlled vowels (Bossy R)
    "ar",
    "er",
    "ir",
    "or",
    "ur",

    // Consonant digraphs
    "ch",
    "ck",
    "gh",
    "gn",
    "kn",
    "ph",
    "sh",
    "th",
    "wh",
    "wr",
    "qu",
    "ng",

    // Common consonant blends (initial and final)
    "bl",
    "br",
    "cl",
    "cr",
    "dr",
    "fl",
    "fr",
    "gl",
    "gr",
    "pl",
    "pr",
    "sc",
    "scr",
    "sk",
    "sl",
    "sm",
    "sn",
    "sp",
    "spl",
    "spr",
    "st",
    "str",
    "sw",
    "tr",
    "tw",

    // Word endings / suffixes
    "ing",
    "ed",
    "es",
    "ly",
    "er",
    "est",
    "y",
    "en",
    "ness",
    "ful",
    "less",
    "ment",
    "tion",
    "sion",
    "ous",
    "able",
    "ible",

    // Common word families (rimes) – optional but useful
    "ack",
    "all",
    "ank",
    "ash",
    "ate",
    "eep",
    "ell",
    "est",
    "ick",
    "ing",
    "ink",
    "ock",
    "op",
    "uck",
    "ump",

    // Silent letter patterns
    "mb",
    "gn",
    "kn",
    "wr",
  ];

  const formatWord = (w: string) => {
    // make everything lowercase and remove any non-alphabetic characters
    return w.toLowerCase().replace(/[^a-z]/g, "");
  };

  function chunkPhonics(word: string): string[] {
    const chunks: string[] = [];
    let i = 0;

    const lower = word.toLowerCase();

    while (i < lower.length) {
      let found = false;

      // Try to match longest possible chunk (up to 3 letters)
      for (let len = 3; len > 0; len--) {
        const piece = lower.slice(i, i + len);
        if (PHONICS_CHUNKS.includes(piece)) {
          chunks.push(piece);
          i += len;
          found = true;
          break;
        }
      }

      if (!found) {
        // Default to single letter
        chunks.push(lower[i]);
        i += 1;
      }
    }

    return chunks;
  }
  const [phonicsChunks, setPhonicsChunks] = useState<string[]>([]);

  useEffect(() => {
    if (word) {
      const chunks = chunkPhonics(formatWord(word));
      setPhonicsChunks(chunks);
    }
  }, [word]);

  let initialBg = "rgb(255,255,255)";
  let targetBg = "rgb(255,255,255)";
  const baseBgClass = "bg-white dark:bg-zinc-900";
  const baseTextClass = "text-black dark:text-white";
  let textClass = `rounded-xl px-2 md:px-4 py-1 md:py-2 text-4xl font-medium ${baseTextClass}`;
  if (typeof analysisPer === "number" && showHighlighted) {
    const p = Math.max(0, Math.min(1, analysisPer));
    let r, g;
    const b = 100;
    if (p < 0.5) {
      r = Math.round(2 * 255 * p);
      g = 255;
    } else {
      r = 255;
      g = Math.round(255 * (1 - 2 * (p - 0.5)));
    }
    targetBg = `rgb(${r},${g},${b})`;
    textClass +=
      p > 0.5 ? " text-white dark:text-white" : " text-black dark:text-black";
  }

  const { speak } = useSpeechSynthesis();
  const [isGraphemes, setIsGraphemes] = useState(false);

  return (
    <motion.div
      initial={{
        opacity: 0,
        scale: 0.8,
      }}
      animate={
        showHighlighted && typeof analysisPer === "number"
          ? {
              opacity: 1,
              scale: 1,
              backgroundColor: targetBg,
              transition: {
                backgroundColor: { delay: idx * 0.08, duration: 0.3 },
                opacity: { delay: idx * 0.08, duration: 0.3 },
                scale: { delay: idx * 0.08, duration: 0.3 },
              },
            }
          : { opacity: 1, scale: 1 }
      }
      exit={{ opacity: 0, scale: 0.8 }}
      style={{ borderRadius: "0.75rem", position: "relative" }}
      className="inline-block group bg-white dark:bg-zinc-900"
    >
      {/* Toggle Grapheme Button */}
      <button
        type="button"
        aria-label="Toggle grapheme mode"
        onClick={(e) => {
          e.stopPropagation();
          setIsGraphemes((s) => !s);
        }}
        className="absolute top-[-8px] right-[-8px] z-10 p-1.5 rounded-full bg-white/80 hover:bg-muted shadow transition-opacity opacity-0 group-hover:opacity-100"
        tabIndex={0}
      >
        {isGraphemes ? (
          <Text className="h-5 w-5" />
        ) : (
          <Columns className="h-5 w-5" />
        )}
      </button>
      <Badge
        variant="outline"
        className={`${textClass} ${baseBgClass} cursor-pointer transition-colors hover:bg-muted relative`}
        style={{ background: "transparent" }}
        onClick={() => {
          if (!isGraphemes) {
            speak(word, { rate: 1 });
          } else {
            speak(phonicsChunks.join(" "), { rate: 0.6 });
          }
        }}
      >
        {isGraphemes ? (
          <span>
            <AnimatePresence>
              {phonicsChunks.map((g, i) => (
                <motion.span
                  key={i}
                  initial={{
                    opacity: 0,
                    scale: 0.5,
                    x: 0,
                    y: 0,
                    rotate: Math.random() * 20 - 10, // random slight rotation
                  }}
                  animate={{
                    opacity: 1,
                    scale: 1,
                    x: (i - phonicsChunks.length / 2 + 0.5) * 12, // spread horizontally
                    y: 0,
                    rotate: 0,
                    transition: {
                      delay: i * 0.08,
                      duration: 0.5,
                      type: "spring",
                      stiffness: 120,
                      damping: 9,
                    },
                  }}
                  exit={{
                    opacity: 0,
                    scale: 0.5,
                    x: 0,
                    y: 0,
                    transition: {
                      duration: 0.3,
                      type: "spring",
                    },
                  }}
                >
                  <Badge
                    key={i}
                    variant="secondary"
                    className="mx-0.5 text-2xl md:text-4xl font-medium px-3"
                  >
                    {g}
                  </Badge>
                </motion.span>
              ))}
            </AnimatePresence>
          </span>
        ) : (
          <motion.span
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            key="whole-word"
            className="text-2xl md:text-4xl font-medium px-1 md:px-3"
          >
            {word}
          </motion.span>
        )}
      </Badge>
    </motion.div>
  );
};
