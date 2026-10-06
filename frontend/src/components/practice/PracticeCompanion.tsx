import { AnimatePresence, motion } from "framer-motion";
import { Volume2 } from "lucide-react";
import Mascot, { type MascotMood } from "@/components/mascot/Mascot";
import { FeedbackAnimatedText } from "@/components/FeedbackAnimatedText";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

// The mascot's spot under the sentence. It stays put the whole time so the
// child gets used to it. It listens while they read, and the speech bubble
// fills in beside it when the feedback arrives.
interface PracticeCompanionProps {
  mood: MascotMood;
  // Null while there's nothing to say. Then only the mascot shows.
  feedback: string | null;
  onReplay: (() => void) | null;
  onCelebrateEnd: () => void;
}

const PracticeCompanion = ({
  mood,
  feedback,
  onReplay,
  onCelebrateEnd,
}: PracticeCompanionProps) => (
  <div
    className={cn(
      "flex w-full max-w-2xl items-start gap-3 rounded-2xl p-3 transition-colors duration-300 sm:p-4",
      feedback ? "bg-muted/70" : "bg-transparent",
    )}
  >
    <span className="flex size-12 shrink-0 items-center justify-center rounded-xl bg-card shadow-xs">
      <Mascot mood={mood} onCelebrateEnd={onCelebrateEnd} className="size-9" />
    </span>
    <AnimatePresence mode="wait">
      {feedback && (
        <motion.div
          key={feedback}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0 }}
          className="flex min-h-12 flex-1 items-start gap-3"
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
    </AnimatePresence>
  </div>
);

export default PracticeCompanion;
