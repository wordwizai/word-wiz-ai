// Shared classes for the home page's sections, so they stay in step with the
// hero's demo card (AnimatedPracticeDemo).

/** Two-line section headlines: first line foreground, second in primary. */
export const sectionTitle =
  "text-3xl font-bold leading-[1.1] tracking-tight md:text-4xl lg:text-[44px]";

/** Soft color halo behind a floating card, the same one the hero demo uses. */
export const cardGlow =
  "absolute inset-0 rounded-3xl bg-gradient-to-br from-purple-100/55 via-pink-50/35 to-blue-50/35 blur-xl dark:from-primary/15 dark:via-primary/5 dark:to-transparent";

/** The floating white card that sits on a cardGlow. */
export const floatingCard =
  "relative rounded-3xl border-2 border-purple-200/50 bg-white/85 shadow-2xl backdrop-blur-sm dark:border-primary/20 dark:bg-card/85 dark:shadow-black/50";

/** The pill the hero demo uses for "try this sound" feedback. */
export const tryPill =
  "inline-flex items-center gap-2 rounded-full bg-orange-100 px-4 py-2 text-[15px] font-medium text-orange-700 dark:bg-orange-500/15 dark:text-orange-300";

/** A handwritten note in pen ink. */
export const penNote = "font-hand text-[30px] leading-[1.05] text-pen-ink";
