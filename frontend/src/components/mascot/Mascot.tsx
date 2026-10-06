import { useEffect, useId, useRef, type CSSProperties } from "react";
import { useReducedMotion } from "framer-motion";
import { cn } from "@/lib/utils";
import {
  BRIM,
  COLORS,
  CONE,
  CONE_SHADE,
  HAT_STARS,
  HEAD_SHINE,
  HEAD_TOP,
  MASCOT_VIEWBOX,
  SPARKLES,
  UNDER_BRIM,
} from "./mascotArt";
import "./mascot.css";

// "still" is the plain logo. The others are tied to moments: listening while
// the mic is on, talking while spoken feedback plays, celebrating a great
// read. Idle is for places with no reading task, and for the short wait while
// a reading is checked. Steady motion next to a sentence any longer than that
// pulls a child's eyes off the words.
export type MascotMood =
  | "still"
  | "idle"
  | "talking"
  | "listening"
  | "celebrating";

interface MascotProps {
  mood?: MascotMood;
  // Read by screen readers. Leave it out where the mascot is decoration.
  label?: string;
  // Sets the size, e.g. "size-9". The art keeps its shape inside the box,
  // and celebrating hops above it.
  className?: string;
  // Celebrating plays once. This fires when the hop lands so the caller can
  // move on to the next mood. To celebrate again, change the mood first.
  onCelebrateEnd?: () => void;
}

const Mascot = ({
  mood = "still",
  label,
  className,
  onCelebrateEnd,
}: MascotProps) => {
  const reduceMotion = useReducedMotion();
  // Masks are found by id, so every mascot on a page needs its own.
  const uid = `mascot${useId().replace(/[^a-zA-Z0-9_-]/g, "")}`;

  const onCelebrateEndRef = useRef(onCelebrateEnd);
  useEffect(() => {
    onCelebrateEndRef.current = onCelebrateEnd;
  });

  // With reduced motion the hop never runs, so it's over as soon as it starts.
  useEffect(() => {
    if (mood === "celebrating" && reduceMotion) onCelebrateEndRef.current?.();
  }, [mood, reduceMotion]);

  return (
    <svg
      viewBox={MASCOT_VIEWBOX}
      data-mood={mood}
      className={cn("mascot overflow-visible", className)}
      role={label ? "img" : undefined}
      aria-label={label}
      aria-hidden={label ? undefined : true}
      onAnimationEnd={(event) => {
        if (event.animationName === "mascot-hop") onCelebrateEnd?.();
      }}
    >
      <defs>
        {/* The head is the lower half of a circle, tucked under the brim. */}
        <mask
          id={`${uid}-head`}
          maskUnits="userSpaceOnUse"
          x="83"
          y="186"
          width="247"
          height="130"
        >
          <rect x="83" y="186" width="247" height="130" fill="#fff" />
        </mask>
        <mask
          id={`${uid}-shine`}
          maskUnits="userSpaceOnUse"
          x="83"
          y="78"
          width="216"
          height="216"
        >
          <circle cx="191" cy="186" r="108" fill="#fff" />
        </mask>
        <mask
          id={`${uid}-shade`}
          maskUnits="userSpaceOnUse"
          x="58"
          y="0"
          width="234"
          height="216"
        >
          <path d={CONE} fill="#fff" />
        </mask>
        {/* Animated with the hat, so it tracks the brim as the hat lifts. */}
        <clipPath id={`${uid}-under-brim`}>
          <path className="mascot-under-brim" d={UNDER_BRIM} />
        </clipPath>
      </defs>

      <g className="mascot-body">
        <g className="mascot-head">
          <path
            className="mascot-head-top"
            clipPath={`url(#${uid}-under-brim)`}
            d={HEAD_TOP}
            fill={COLORS.head}
          />
          <g mask={`url(#${uid}-head)`}>
            <circle cx="191" cy="186" r="108" fill={COLORS.head} />
          </g>
          <g mask={`url(#${uid}-shine)`}>
            <path d={HEAD_SHINE} fill={COLORS.headShine} />
          </g>
        </g>

        <g className="mascot-hat">
          <path d={BRIM} fill={COLORS.brim} />
          <path d={CONE} fill={COLORS.cone} />
          <g mask={`url(#${uid}-shade)`}>
            <path d={CONE_SHADE} fill={COLORS.coneShade} />
          </g>
          {HAT_STARS.map((d) => (
            <path key={d} d={d} fill={COLORS.star} />
          ))}
        </g>
      </g>

      {SPARKLES.map(({ d, burst, delay }) => (
        <path
          key={d}
          className="mascot-sparkle"
          d={d}
          fill={COLORS.sparkle}
          style={
            {
              "--burst-x": `${burst[0]}px`,
              "--burst-y": `${burst[1]}px`,
              "--twinkle-delay": `${delay}s`,
            } as CSSProperties
          }
        />
      ))}
    </svg>
  );
};

export default Mascot;
