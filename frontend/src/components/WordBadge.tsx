import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { useMemo, type CSSProperties } from "react";
import { useSpeechSynthesis } from "@/hooks/useSpeechSynthesis";
import { cn } from "@/lib/utils";

const PHONICS_CHUNKS = [
  // Vowel teams & diphthongs
  "ai", "ay", "au", "aw", "ea", "ee", "ei", "ey", "ie", "oa", "oe", "oo",
  "ou", "ow", "ue", "ui", "ew", "oy", "oi", "igh",
  // R-controlled vowels (Bossy R)
  "ar", "er", "ir", "or", "ur",
  // Consonant digraphs
  "ch", "ck", "gh", "gn", "kn", "ph", "sh", "th", "wh", "wr", "qu", "ng",
  // Common consonant blends (initial and final)
  "bl", "br", "cl", "cr", "dr", "fl", "fr", "gl", "gr", "pl", "pr", "sc",
  "scr", "sk", "sl", "sm", "sn", "sp", "spl", "spr", "st", "str", "sw", "tr",
  "tw",
  // Word endings / suffixes
  "ing", "ed", "es", "ly", "est", "y", "en", "ness", "ful", "less", "ment",
  "tion", "sion", "ous", "able", "ible",
  // Common word families (rimes)
  "ack", "all", "ank", "ash", "ate", "eep", "ell", "ick", "ink", "ock", "op",
  "uck", "ump",
  // Silent letter patterns
  "mb",
];

// Greedy longest-match split into phonics chunks ("sh" + "i" + "p").
function chunkPhonics(word: string): string[] {
  const lower = word.toLowerCase().replace(/[^a-z]/g, "");
  const chunks: string[] = [];
  let i = 0;
  while (i < lower.length) {
    let len = 3;
    while (len > 1 && !PHONICS_CHUNKS.includes(lower.slice(i, i + len))) len--;
    chunks.push(lower.slice(i, i + len));
    i += len;
  }
  return chunks;
}

// Three clear bands instead of a continuous neon gradient. Each band also
// changes the outline (none / dashed / solid) so it never relies on red
// versus green alone.
type Score = "good" | "close" | "practice";

const scoreFor = (per: number): Score =>
  per < 0.15 ? "good" : per < 0.5 ? "close" : "practice";

const SCORE_STYLE: Record<Score, CSSProperties & { label: string }> = {
  good: {
    label: "read well",
    backgroundColor: "var(--pastel-mint)",
    color: "var(--pastel-mint-foreground)",
    borderColor: "transparent",
  },
  close: {
    label: "almost",
    backgroundColor: "var(--pastel-yellow)",
    color: "var(--pastel-yellow-foreground)",
    borderColor: "var(--pastel-yellow-foreground)",
    borderStyle: "dashed",
  },
  practice: {
    label: "practice this one",
    backgroundColor: "var(--pastel-pink)",
    color: "var(--pastel-pink-foreground)",
    borderColor: "var(--pastel-pink-foreground)",
  },
};

interface WordBadgeProps {
  word: string;
  idx: number;
  showHighlighted: boolean;
  analysisPer?: number;
  isInsertion?: boolean;
  isDeletion?: boolean;
  // Show the word as phonics chunks ("sound it out"); taps then read slowly.
  splitIntoSounds?: boolean;
}

export const WordBadge = ({
  word,
  idx,
  showHighlighted,
  analysisPer,
  isInsertion = false,
  isDeletion = false,
  splitIntoSounds = false,
}: WordBadgeProps) => {
  const { speak } = useSpeechSynthesis();
  const reduceMotion = useReducedMotion();
  const chunks = useMemo(() => chunkPhonics(word), [word]);

  const score =
    showHighlighted && typeof analysisPer === "number"
      ? scoreFor(Math.max(0, Math.min(1, analysisPer)))
      : null;
  const { label: scoreLabel, ...scoreStyle } = score
    ? SCORE_STYLE[score]
    : { label: "" };

  const status = isDeletion
    ? "skipped"
    : isInsertion
      ? "extra word"
      : scoreLabel;

  return (
    <motion.button
      type="button"
      layout={!reduceMotion}
      initial={reduceMotion ? false : { opacity: 0, scale: 0.85 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.85 }}
      transition={{ duration: 0.2 }}
      onClick={() => speak(word, { rate: splitIntoSounds ? 0.3 : 1 })}
      aria-label={`Hear "${word}"${status ? `, ${status}` : ""}`}
      className={cn(
        "relative inline-flex items-center rounded-2xl border-2 px-3 py-1.5 md:px-4 md:py-2",
        "text-2xl leading-tight font-medium md:text-4xl",
        "outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50",
        "transition-[background-color,color,border-color,translate] duration-300",
        "hover:-translate-y-0.5 active:translate-y-0",
        !score && !isDeletion && !isInsertion &&
          "border-border bg-card text-foreground shadow-xs",
        isDeletion &&
          "border-dashed border-pastel-pink-foreground/60 bg-transparent text-pastel-pink-foreground/70 line-through",
        isInsertion &&
          "border-dashed border-border bg-transparent text-muted-foreground italic"
      )}
      style={{
        ...scoreStyle,
        // Feedback sweeps left to right, 80ms per word (design system).
        transitionDelay: score ? `${idx * 80}ms` : undefined,
      }}
    >
      {splitIntoSounds ? (
        <span className="flex items-center gap-1">
          <AnimatePresence initial={!reduceMotion}>
            {chunks.map((chunk, i) => (
              <motion.span
                key={`${chunk}-${i}`}
                initial={{ opacity: 0, scale: 0.5, y: 6 }}
                animate={{
                  opacity: 1,
                  scale: 1,
                  y: 0,
                  transition: {
                    delay: i * 0.08,
                    type: "spring",
                    stiffness: 120,
                    damping: 9,
                  },
                }}
                className={cn(
                  "rounded-lg px-1.5 md:px-2",
                  score ? "bg-white/60 dark:bg-black/20" : "bg-secondary"
                )}
              >
                {chunk}
              </motion.span>
            ))}
          </AnimatePresence>
        </span>
      ) : (
        word
      )}
    </motion.button>
  );
};
