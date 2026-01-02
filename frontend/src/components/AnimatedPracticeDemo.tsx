import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import { WordBadge } from "./WordBadge";
import { Mic, Volume2 } from "lucide-react";
import { useEffect, useState } from "react";

// Simulated practice session showing how the app works
const AnimatedPracticeDemo = () => {
  const prefersReducedMotion = useReducedMotion();
  const demoSentences = [
    {
      words: ["The", "cat", "sat"],
      perScores: [0.0, 0.1, 0.0], // Perfect, nearly perfect, perfect
    },
    {
      words: ["I", "see", "the", "blue", "sky"],
      perScores: [0.0, 0.3, 0.0, 0.2, 0.0],
    },
    {
      words: ["Fish", "swim", "in", "the", "pond"],
      perScores: [0.0, 0.0, 0.0, 0.15, 0.0],
    },
  ];

  const [currentSentence, setCurrentSentence] = useState(0);
  const [animationPhase, setAnimationPhase] = useState<
    "waiting" | "recording" | "analyzing" | "showing"
  >("waiting");
  const [showHighlighting, setShowHighlighting] = useState(false);

  useEffect(() => {
    // Skip animations if user prefers reduced motion
    if (prefersReducedMotion) {
      setAnimationPhase("showing");
      setShowHighlighting(true);
      return;
    }

    const timeline = [
      { phase: "waiting" as const, duration: 1500 },
      { phase: "recording" as const, duration: 2000 },
      { phase: "analyzing" as const, duration: 1000 },
      { phase: "showing" as const, duration: 3000 },
    ];

    let currentStep = 0;
    let timeoutId: NodeJS.Timeout;

    const runTimeline = () => {
      if (currentStep >= timeline.length) {
        // Move to next sentence
        setCurrentSentence((prev) => (prev + 1) % demoSentences.length);
        setShowHighlighting(false);
        currentStep = 0;
      }

      const step = timeline[currentStep];
      setAnimationPhase(step.phase);

      if (step.phase === "showing") {
        setShowHighlighting(true);
      } else {
        setShowHighlighting(false);
      }

      timeoutId = setTimeout(() => {
        currentStep++;
        runTimeline();
      }, step.duration);
    };

    runTimeline();

    return () => clearTimeout(timeoutId);
  }, [currentSentence, prefersReducedMotion]);

  const sentence = demoSentences[currentSentence];

  return (
    <div className="relative w-full h-full flex items-center justify-center p-4 md:p-8">
      {/* Background glow effect */}
      <div className="absolute inset-0 bg-gradient-to-br from-purple-100/50 via-pink-50/30 to-blue-50/30 rounded-3xl blur-xl" />

      {/* Main demo container */}
      <div className="relative w-full max-w-4xl bg-white/80 dark:bg-zinc-900/80 backdrop-blur-sm rounded-3xl shadow-2xl border-2 border-purple-200/50 p-6 md:p-8 lg:p-12">
        {/* Status indicator */}
        <motion.div
          className="flex items-center justify-center gap-3 mb-8"
          animate={{
            scale: animationPhase === "recording" ? [1, 1.05, 1] : 1,
          }}
          transition={{
            repeat: animationPhase === "recording" ? Infinity : 0,
            duration: 1.5,
          }}
        >
          <AnimatePresence mode="wait">
            {animationPhase === "recording" && (
              <motion.div
                key="recording"
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                className="flex items-center gap-2 px-4 py-2 bg-red-100 text-red-600 rounded-full"
              >
                <Mic className="w-5 h-5 animate-pulse" />
                <span className="font-medium">Recording...</span>
              </motion.div>
            )}
            {animationPhase === "analyzing" && (
              <motion.div
                key="analyzing"
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                className="flex items-center gap-2 px-4 py-2 bg-blue-100 text-blue-600 rounded-full"
              >
                <div className="w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
                <span className="font-medium">Analyzing...</span>
              </motion.div>
            )}
            {animationPhase === "showing" && (
              <motion.div
                key="showing"
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                className="flex items-center gap-2 px-4 py-2 bg-green-100 text-green-600 rounded-full"
              >
                <Volume2 className="w-5 h-5" />
                <span className="font-medium">Great job!</span>
              </motion.div>
            )}
            {animationPhase === "waiting" && (
              <motion.div
                key="waiting"
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                className="flex items-center gap-2 px-4 py-2 bg-purple-100 text-purple-600 rounded-full"
              >
                <span className="font-medium">Read the sentence aloud</span>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>

        {/* Words display */}
        <div className="flex flex-wrap items-center justify-center gap-3 md:gap-4 min-h-[120px]">
          <AnimatePresence mode="wait">
            {sentence.words.map((word, idx) => (
              <WordBadge
                key={`${currentSentence}-${idx}-${word}`}
                word={word}
                idx={idx}
                showHighlighted={showHighlighting}
                analysisPer={
                  showHighlighting ? sentence.perScores[idx] : undefined
                }
              />
            ))}
          </AnimatePresence>
        </div>

        {/* Instruction text */}
        <motion.p
          className="text-center text-sm md:text-base text-muted-foreground mt-8"
          animate={{ opacity: [0.5, 1, 0.5] }}
          transition={{ duration: 2, repeat: Infinity }}
        >
          Watch how Word Wiz AI analyzes pronunciation in real-time
        </motion.p>
      </div>
    </div>
  );
};

export default AnimatedPracticeDemo;
