import { motion } from "framer-motion";

/**
 * A small handwritten "see how it works" under the hero, with an arrow that
 * bobs. Only on wide screens, where the hero fills the window; on phones the
 * page already reads as something to scroll.
 */
const ScrollCue = ({ href }: { href: string }) => (
  <div className="mt-10 hidden justify-center lg:flex">
    <a
      href={href}
      className="inline-flex min-h-11 flex-col items-center gap-1 px-3 py-1 text-pen-ink no-underline"
    >
      <span className="-rotate-2 font-hand text-[30px] leading-none">
        see how it works
      </span>
      {/* MotionConfig's reducedMotion="user" on the page stops the bob */}
      <motion.svg
        width="28"
        height="40"
        viewBox="0 0 28 40"
        fill="none"
        stroke="currentColor"
        strokeWidth={2.5}
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
        className="overflow-visible"
        animate={{ y: [0, 6, 0] }}
        transition={{ duration: 1.8, repeat: Infinity, ease: "easeInOut" }}
      >
        <path d="M14 3 C 11 13, 17 22, 14 34" />
        <path d="M6 27 C 9 30, 12 33, 14 35 C 17 31, 20 28, 23 25" />
      </motion.svg>
    </a>
  </div>
);

export default ScrollCue;
