import { AnimatePresence, motion } from "framer-motion";
import { Badge } from "@/components/ui/badge";
import { useSpeechSynthesis } from "@/hooks/useSpeechSynthesis";
import { useEffect, useState } from "react";
import { Columns, Text, Target } from "lucide-react";

interface GraphemeError {
  type: "missed" | "substituted" | "added";
  phoneme?: string;
  expected_phoneme?: string;
  detected_phoneme?: string;
  grapheme?: string | null;
}

interface WordBadgeProps {
  word: string;
  idx: number;
  showHighlighted: boolean;
  analysisPer?: number;
  isInsertion?: boolean;
  isDeletion?: boolean;
  graphemes?: string[];
  graphemeErrors?: Record<number, GraphemeError>;
}

export const WordBadge = ({
  word,
  idx,
  showHighlighted,
  analysisPer,
  isInsertion = false,
  isDeletion = false,
  graphemes,
  graphemeErrors,
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

  const [textClass, setTextClass] = useState("");
  const [targetBg, setTargetBg] = useState("rgb(255,255,255)");

  const baseBgClass = "bg-white dark:bg-zinc-900";

  useEffect(() => {
    const baseTextClass = "text-black dark:text-white";
    let tempTextClass = `rounded-xl px-2 md:px-4 py-1 md:py-2 text-4xl font-medium ${baseTextClass}`;
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
      setTargetBg(`rgb(${r},${g},${b})`);
      tempTextClass +=
        p > 0.5 ? " text-white dark:text-white" : " text-black dark:text-black";
    }
    setTextClass(tempTextClass);
  }, [analysisPer, showHighlighted]);

  const { speak } = useSpeechSynthesis();
  const [isGraphemes, setIsGraphemes] = useState(false);
  const [showLetterLevel, setShowLetterLevel] = useState(false);

  /**
   * Render letter-level highlights for phoneme errors
   */
  const renderLetterHighlights = () => {
    if (!graphemes || !graphemeErrors || Object.keys(graphemeErrors).length === 0) {
      return renderWholeWord();
    }

    return (
      <span className="inline-flex gap-0">
        {graphemes.map((grapheme, g_idx) => {
          const error = graphemeErrors[g_idx];

          let bgColor = "transparent";
          let tooltip = "";

          if (error) {
            if (error.type === "missed") {
              bgColor = "rgba(248, 113, 113, 0.3)"; // light red
              tooltip = `You missed the "${grapheme}" sound (/${error.phoneme}/)`;
            } else if (error.type === "substituted") {
              bgColor = "rgba(251, 146, 60, 0.3)"; // light orange
              tooltip = `You said /${error.detected_phoneme}/ instead of /${error.expected_phoneme}/`;
            }
          }

          return (
            <motion.span
              key={g_idx}
              initial={{ scale: 1 }}
              animate={
                showHighlighted && error
                  ? {
                      scale: [1, 1.2, 1],
                      backgroundColor: ["transparent", bgColor, bgColor],
                      transition: {
                        delay: g_idx * 0.1,
                        duration: 0.6,
                      },
                    }
                  : {}
              }
              style={{
                backgroundColor: showHighlighted && error ? bgColor : "transparent",
                padding: "2px 1px",
                borderRadius: "4px",
              }}
              title={tooltip}
              className="cursor-pointer hover:scale-110 transition-transform"
              onClick={(e) => {
                e.stopPropagation();
                speak(grapheme, { rate: 0.5 });
              }}
            >
              {grapheme}
            </motion.span>
          );
        })}

        {/* Render added phonemes as phantom letters */}
        {Object.entries(graphemeErrors).map(([key, error]) => {
          const keyNum = parseInt(key);
          if (keyNum < 0 && error.type === "added") {
            return (
              <motion.span
                key={`added-${key}`}
                initial={{ opacity: 0, scale: 0.5 }}
                animate={{ opacity: 0.5, scale: 1 }}
                style={{
                  color: "rgb(134, 239, 172)",
                  border: "2px dashed rgb(134, 239, 172)",
                  padding: "2px 4px",
                  borderRadius: "4px",
                  fontStyle: "italic",
                  marginLeft: "2px",
                }}
                title={`You added the /${error.phoneme}/ sound`}
              >
                ?
              </motion.span>
            );
          }
          return null;
        })}
      </span>
    );
  };

  const renderWholeWord = () => {
    return (
      <motion.span
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        key="whole-word"
        className="text-2xl md:text-4xl font-medium px-1 md:px-3"
      >
        {word}
      </motion.span>
    );
  };

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
          : { opacity: isInsertion ? 0.4 : 1, scale: 1 }
      }
      exit={{ opacity: 0, scale: 0.8 }}
      style={{
        position: "relative",
        ...(isInsertion && {
          border: "2px dashed rgb(134, 239, 172)", // pastel mint green dashed border for ghosts
          backgroundColor: "rgba(134, 239, 172, 0.1)", // subtle mint green background
        }),
        ...(isDeletion && {
          backgroundColor: "rgba(248, 113, 113, 0.15)", // light red background for deletions
        }),
      }}
      className="inline-block group bg-white dark:bg-zinc-900 rounded-xl"
    >
      {/* Toggle Letter-Level Button */}
      {graphemes && graphemeErrors && Object.keys(graphemeErrors).length > 0 && (
        <button
          type="button"
          aria-label="Toggle letter-level error view"
          onClick={(e) => {
            e.stopPropagation();
            setShowLetterLevel((s) => !s);
            if (!showLetterLevel) setIsGraphemes(false); // Turn off graphemes when showing letters
          }}
          className="absolute top-[-8px] left-[-8px] z-10 p-1.5 rounded-full bg-white/80 hover:bg-muted shadow transition-opacity opacity-0 group-hover:opacity-100"
          tabIndex={0}
        >
          {showLetterLevel ? (
            <Text className="h-5 w-5 text-red-500" />
          ) : (
            <Target className="h-5 w-5" />
          )}
        </button>
      )}
      {/* Toggle Grapheme Button */}
      <button
        type="button"
        aria-label="Toggle grapheme mode"
        onClick={(e) => {
          e.stopPropagation();
          setIsGraphemes((s) => !s);
          if (!isGraphemes) setShowLetterLevel(false); // Turn off letter view when showing graphemes
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
        className={`${textClass} ${baseBgClass} cursor-pointer transition-colors hover:bg-muted relative rounded-xl ${
          isInsertion ? "italic text-green-600 dark:text-green-400" : ""
        } ${
          isDeletion
            ? "line-through text-red-400 dark:text-red-400 opacity-60"
            : ""
        }`}
        style={{ background: "transparent" }}
        onClick={() => {
          if (showLetterLevel) {
            // Don't speak on click in letter mode, let individual letters handle it
            return;
          }
          if (!isGraphemes) {
            speak(word, { rate: 1 });
          } else {
            speak(word, { rate: 0.3 });
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
                    className="mx-0.5 text-2xl md:text-4xl font-medium px-3 rounded-xl"
                  >
                    {g}
                  </Badge>
                </motion.span>
              ))}
            </AnimatePresence>
          </span>
        ) : showLetterLevel ? (
          // NEW: Letter-level error view
          renderLetterHighlights()
        ) : (
          // Whole word view
          renderWholeWord()
        )}
      </Badge>
    </motion.div>
  );
};
