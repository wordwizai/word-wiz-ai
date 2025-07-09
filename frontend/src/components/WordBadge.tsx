import { motion } from "framer-motion";
import { Badge } from "@/components/ui/badge";

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
  let initialBg = "rgb(255,255,255)";
  let targetBg = "rgb(255,255,255)";
  let textClass = "rounded-xl px-4 py-2 text-4xl font-medium";
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
    textClass += p > 0.5 ? " text-white" : " text-black";
  }
  return (
    <motion.div
      initial={{
        opacity: 0,
        scale: 0.8,
        backgroundColor: initialBg,
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
          : { opacity: 1, scale: 1, backgroundColor: initialBg }
      }
      exit={{ opacity: 0, scale: 0.8 }}
      style={{ borderRadius: "0.75rem" }}
      className="inline-block"
    >
      <Badge
        variant="outline"
        className={textClass}
        style={{ background: "transparent" }}
      >
        {word}
      </Badge>
    </motion.div>
  );
};
