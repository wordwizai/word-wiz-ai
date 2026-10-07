import { Fragment, type ReactNode } from "react";
import { motion, useReducedMotion, type Variants } from "framer-motion";
import { cn } from "@/lib/utils";
import { PEN_PATHS } from "./penPaths";

/*
 * The teacher's-pen layer on the home page: hand-drawn marks and handwritten
 * notes in pen ink over the real product UI. The rules for using it live in
 * STYLE_GUIDELINES.md under "Handwriting (Teacher's Pen)".
 *
 * A PenGroup starts everything inside it once it scrolls into view; each
 * stroke or note waits for its own `delay` (seconds) after that.
 */

const PEN_EASE = [0.65, 0, 0.35, 1] as const;
const WRITE_EASE = [0.3, 0, 0.6, 1] as const;
// Roughly handwriting pace for the write-on effect.
const SECONDS_PER_LETTER = 0.045;


export function PenGroup({
  className,
  children,
  amount = 0.4,
}: {
  className?: string;
  children: ReactNode;
  amount?: number;
}) {
  const reduce = useReducedMotion();
  if (reduce) return <div className={className}>{children}</div>;
  return (
    <motion.div
      className={className}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, amount }}
    >
      {children}
    </motion.div>
  );
}

/** An inline SVG in pen ink. Its viewBox stretches to the box it's given. */
export function PenMark({
  viewBox,
  className,
  strokeWidth = 3,
  children,
}: {
  viewBox: string;
  className?: string;
  strokeWidth?: number;
  children: ReactNode;
}) {
  return (
    <svg
      viewBox={viewBox}
      preserveAspectRatio="none"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      className={cn("pointer-events-none overflow-visible text-pen-ink", className)}
    >
      {children}
    </svg>
  );
}

/** One stroke of a PenMark, drawn along its length. */
export function PenStroke({
  d,
  delay = 0,
  duration = 0.5,
}: {
  d: string;
  delay?: number;
  duration?: number;
}) {
  const reduce = useReducedMotion();
  if (reduce) return <path d={d} />;
  const variants: Variants = {
    hidden: { pathLength: 0, opacity: 0 },
    visible: {
      pathLength: 1,
      opacity: 1,
      transition: {
        pathLength: { delay, duration, ease: PEN_EASE },
        opacity: { delay, duration: 0.01 },
      },
    },
  };
  return <motion.path d={d} variants={variants} />;
}

/**
 * Handwritten text that writes itself in word by word, each word revealed
 * left to right at about handwriting pace.
 */
export function PenWords({
  text,
  delay = 0,
  className,
  as: Tag = "p",
}: {
  text: string;
  delay?: number;
  className?: string;
  as?: "p" | "span";
}) {
  const reduce = useReducedMotion();
  if (reduce) return <Tag className={className}>{text}</Tag>;

  let start = delay;
  const words = text.split(" ").map((word) => {
    const duration = Math.max(0.12, word.length * SECONDS_PER_LETTER);
    const timing = { word, start, duration };
    start += duration + 0.05;
    return timing;
  });

  return (
    <Tag className={className}>
      {words.map(({ word, start, duration }, i) => (
        <Fragment key={i}>
          {i > 0 && " "}
          <motion.span
            className="inline-block"
            variants={{
              hidden: { clipPath: "inset(-25% 100% -25% 0%)", opacity: 0 },
              visible: {
                clipPath: "inset(-25% -8% -25% -8%)",
                opacity: 1,
                transition: {
                  delay: start,
                  duration,
                  ease: WRITE_EASE,
                  opacity: { delay: start, duration: 0.05 },
                },
              },
            }}
          >
            {word}
          </motion.span>
        </Fragment>
      ))}
    </Tag>
  );
}

// Hand-drawn digits in a 40 x 60 box. Nanum Pen Script's own "1" is a bare
// stroke that reads as a bar, so step numbers are drawn instead of typed.
const DIGITS: Record<string, string[]> = {
  "1": ["M9 16 C 14 12, 18 8, 21 3", "M21 3 C 21 20, 20 38, 21 55"],
  "2": ["M7 17 C 9 7, 29 1, 31 14 C 33 26, 17 39, 6 54 C 16 52, 28 53, 35 52"],
  "3": [
    "M7 11 C 15 2, 31 4, 30 15 C 29 23, 20 27, 15 28 C 26 28, 34 36, 32 46 C 30 57, 12 58, 5 49",
  ],
};

/** A handwritten step number, drawn stroke by stroke. Size it 2:3. */
export function PenNumeral({
  digit,
  delay = 0,
  className,
  strokeWidth = 2.6,
}: {
  digit: "1" | "2" | "3";
  delay?: number;
  className?: string;
  strokeWidth?: number;
}) {
  return (
    <PenMark viewBox="0 0 40 60" className={className} strokeWidth={strokeWidth}>
      {DIGITS[digit].map((d, i) => (
        <PenStroke key={i} d={d} delay={delay + i * 0.2} duration={0.4} />
      ))}
    </PenMark>
  );
}

/** A word with a hand-drawn wavy underline beneath it. */
export function PenUnderlined({
  children,
  delay = 0,
  alt = false,
}: {
  children: ReactNode;
  delay?: number;
  alt?: boolean;
}) {
  return (
    <span className="relative inline-block">
      {children}
      <PenMark
        viewBox="0 0 100 12"
        className="absolute -bottom-1.5 -left-[4%] h-3 w-[108%]"
      >
        <PenStroke
          d={alt ? PEN_PATHS.underlineAlt : PEN_PATHS.underline}
          delay={delay}
          duration={0.38}
        />
      </PenMark>
    </span>
  );
}

/** A short hand-drawn arrow. `variant` picks the curve. */
export function PenArrow({
  className,
  delay = 0,
  variant,
}: {
  className?: string;
  delay?: number;
  variant: "up-left" | "right-up" | "right-down" | "down-right" | "up-right";
}) {
  const shapes = {
    // 70 x 50, rising from a note to the mark it explains
    "up-left": {
      viewBox: "0 0 70 50",
      shaft: "M64 46 C 52 30, 30 16, 9 7",
      head: "M9 7 L 21 5 M9 7 L 14 18",
    },
    // 48 x 30, from one step card to the next
    "right-up": {
      viewBox: "0 0 48 30",
      shaft: "M3 18 C 14 8, 30 8, 42 15",
      head: "M42 15 L 33 9 M42 15 L 34 22",
    },
    "right-down": {
      viewBox: "0 0 48 30",
      shaft: "M3 14 C 15 20, 30 19, 42 12",
      head: "M42 12 L 32 10 M42 12 L 37 21",
    },
    // 90 x 44, from a note down to a button
    "down-right": {
      viewBox: "0 0 90 44",
      shaft: "M10 4 C 26 26, 56 38, 84 34",
      head: "M84 34 L 73 27 M84 34 L 74 42",
    },
    // 80 x 40, from a note up to the first FAQ answer
    "up-right": {
      viewBox: "0 0 80 40",
      shaft: "M3 30 C 24 34, 52 26, 74 8",
      head: "M74 8 L 62 9 M74 8 L 71 20",
    },
  }[variant];

  return (
    <PenMark viewBox={shapes.viewBox} className={className} strokeWidth={2.5}>
      <PenStroke d={shapes.shaft} delay={delay} duration={0.3} />
      <PenStroke d={shapes.head} delay={delay + 0.35} duration={0.28} />
    </PenMark>
  );
}
