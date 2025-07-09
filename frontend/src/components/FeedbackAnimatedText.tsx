import { AnimatePresence, motion } from "framer-motion";

interface FeedbackAnimatedTextProps {
  feedback: string | null;
}

export const FeedbackAnimatedText = ({
  feedback,
}: FeedbackAnimatedTextProps) => (
  <div className="flex min-h-12 items-end justify-center relative flex-wrap w-full mt-auto">
    <AnimatePresence>
      {typeof feedback === "string" &&
        feedback.split(" ").map((word, idx) => (
          <motion.span
            key={word + idx}
            className="inline-block mx-1 text-lg font-medium text-gray-500"
            initial={{ opacity: 0, y: 12 }}
            animate={{
              opacity: 1,
              y: 0,
              transition: {
                delay: idx * 0.05,
                duration: 0.6,
                type: "spring",
                stiffness: 80,
              },
            }}
            exit={{ opacity: 0, y: -12 }}
          >
            {word}
          </motion.span>
        ))}
    </AnimatePresence>
  </div>
);
