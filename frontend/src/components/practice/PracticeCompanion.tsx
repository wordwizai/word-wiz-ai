import { motion, useReducedMotion } from "framer-motion";
import { Volume2 } from "lucide-react";
import Mascot, { type MascotMood } from "@/components/mascot/Mascot";
import { FeedbackAnimatedText } from "@/components/FeedbackAnimatedText";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

// The feedback row under the sentence. The mascot only shows beside its own
// words, since on its own it was a stray tile under the sentence. The row
// keeps its height while hidden so the sentence above doesn't move.
interface PracticeCompanionProps {
  mood: MascotMood;
  // Null while there's nothing to say. Then the row is empty.
  feedback: string | null;
  // True while the child reads. The old feedback stays in place, unseen.
  quiet?: boolean;
  onReplay: (() => void) | null;
  onCelebrateEnd: () => void;
}

const PracticeCompanion = ({
  mood,
  feedback,
  quiet = false,
  onReplay,
  onCelebrateEnd,
}: PracticeCompanionProps) => {
  const reduceMotion = useReducedMotion();
  const speaking = !!feedback && !quiet;
  return (
    <div
      className={cn(
        "flex w-full max-w-2xl items-start gap-3 rounded-2xl p-3 transition-colors duration-300 sm:p-4",
        speaking ? "bg-muted/70" : "bg-transparent",
      )}
    >
      <span
        className={cn(
          "flex size-12 shrink-0 items-center justify-center rounded-xl bg-card shadow-xs transition-opacity duration-300 motion-reduce:transition-none",
          !speaking && "opacity-0",
        )}
      >
        <Mascot mood={mood} onCelebrateEnd={onCelebrateEnd} className="size-9" />
      </span>
      {/* No exit animation. Old feedback usually leaves while it's already
          invisible (after the child stops reading). AnimatePresence's wait
          mode would hold the next feedback back until a fade-out finished,
          and its default mode briefly shows two bubbles. */}
      {feedback && (
        <motion.div
          key={feedback}
          initial={reduceMotion ? false : { opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className={cn(
            "flex min-h-12 flex-1 items-start gap-3",
            quiet && "invisible",
          )}
        >
          <FeedbackAnimatedText
            feedback={feedback}
            className="flex-1 self-center text-base text-foreground sm:text-lg"
          />
          {onReplay && (
            <Button
              variant="ghost"
              size="icon"
              onClick={onReplay}
              aria-label="Hear this again"
              className="shrink-0 rounded-xl text-primary hover:bg-card"
            >
              <Volume2 className="size-5" />
            </Button>
          )}
        </motion.div>
      )}
    </div>
  );
};

export default PracticeCompanion;
