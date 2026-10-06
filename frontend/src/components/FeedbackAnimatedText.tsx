import { motion, useReducedMotion } from "framer-motion";
import { cn } from "@/lib/utils";

interface FeedbackAnimatedTextProps {
  feedback: string | null;
  className?: string;
}

// Words arrive one after another, roughly at the pace the spoken feedback
// is read out, so a child following along sees and hears them together.
export const FeedbackAnimatedText = ({
  feedback,
  className,
}: FeedbackAnimatedTextProps) => {
  const reduceMotion = useReducedMotion();
  if (typeof feedback !== "string") return null;

  return (
    <p className={cn("leading-relaxed", className)}>
      {feedback.split(" ").map((word, idx) => (
        <motion.span
          key={word + idx}
          className="inline-block"
          initial={reduceMotion ? false : { opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: idx * 0.05, duration: 0.3 }}
        >
          {word}
          {" "}
        </motion.span>
      ))}
    </p>
  );
};
