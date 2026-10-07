import { motion } from "framer-motion";
import { Volume2 } from "lucide-react";
import { cn } from "@/lib/utils";
import LandingSection from "./LandingSection";
import { PEN_PATHS } from "./penPaths";
import {
  PenArrow,
  PenGroup,
  PenMark,
  PenStroke,
  PenUnderlined,
  PenWords,
} from "./TeacherPen";
import {
  cardGlow,
  floatingCard,
  penNote,
  sectionTitle,
  tryPill,
} from "./styles";

const POINTS = [
  "Checks every sound in every word",
  "Builds the next sentence around the miss",
  "Free, with no ads and nothing to upgrade",
];

// "brown" as a reading teacher's sound boxes: one box per sound.
const BOXES = [
  { letters: "b", sound: "b" },
  { letters: "r", sound: "r" },
  { letters: "ow", sound: "aʊ", missed: true },
  { letters: "n", sound: "n" },
];

const rise = (i: number) => ({
  hidden: { opacity: 0, y: 10, scale: 0.97 },
  visible: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: {
      delay: 0.1 + i * 0.08,
      duration: 0.55,
      ease: [0.2, 0.8, 0.2, 1] as const,
    },
  },
});

/** "It hears the sound, not just the word": sound boxes, marked up in pen. */
const SoundBoxesSection = ({ id }: { id: string }) => (
  <LandingSection
    id={id}
    className="scroll-mt-20 bg-gradient-to-b from-primary/5 to-background px-4 py-20 sm:px-6 md:py-24"
  >
    <div className="mx-auto flex max-w-6xl flex-col items-center gap-14 lg:flex-row lg:gap-16">
      <PenGroup className="w-full max-w-[460px] space-y-5 lg:flex-none lg:basis-[420px]">
        <h2 className={sectionTitle}>
          It hears the sound,
          <br />
          <span className="text-primary">not just the word.</span>
        </h2>
        <p className="text-lg text-muted-foreground">
          Most reading apps can tell your child a word was wrong. Word Wiz
          tells them which sound was wrong.
        </p>
        <p className="text-muted-foreground">
          Reading teachers draw one box for each sound in a word. Word Wiz
          checks your child&rsquo;s reading the same way, then circles the
          sound that slipped.
        </p>
        <ul className="space-y-3.5 pt-1">
          {POINTS.map((point, i) => (
            <li key={point} className="flex items-center gap-3.5 font-medium">
              <PenMark viewBox="0 0 30 24" className="h-6 w-[30px] flex-none">
                <PenStroke
                  d={PEN_PATHS.ticks[i]}
                  delay={0.5 + i * 0.2}
                  duration={0.28}
                />
              </PenMark>
              {point}
            </li>
          ))}
        </ul>
      </PenGroup>

      <div className="relative w-full min-w-0 flex-1 p-3 sm:p-6">
        <div aria-hidden="true" className={cardGlow} />
        <PenGroup
          amount={0.5}
          className={cn(floatingCard, "p-6 sm:p-10")}
        >
          <figure className="m-0 space-y-7">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <span className={tryPill}>
                <Volume2 className="size-[18px]" aria-hidden="true" />
                Try the ow sound in brown
              </span>
              <span className="text-[13px] text-muted-foreground">
                Your child read{" "}
                <strong className="font-semibold text-foreground">brown</strong>
              </span>
            </div>

            <div className="pl-1.5 pt-4">
              <div className="flex w-max" role="img" aria-label="brown in sound boxes: b, r, ow, n. The ow box is circled.">
                {BOXES.map((box, i) => (
                  <motion.div
                    key={box.letters}
                    variants={rise(i)}
                    className={cn(
                      "flex flex-col items-center gap-2.5",
                      i > 0 && "-ml-0.5",
                      box.missed && "relative z-10"
                    )}
                  >
                    <div
                      className={cn(
                        "relative flex aspect-square w-[min(96px,17vw)] items-center justify-center border-2 text-[clamp(28px,4vw,40px)] font-medium",
                        i === 0 && "rounded-l-[14px]",
                        i === BOXES.length - 1 && "rounded-r-[14px]",
                        box.missed
                          ? "border-pastel-pink-foreground bg-pastel-pink font-semibold text-pastel-pink-foreground"
                          : "border-foreground/15 bg-card"
                      )}
                    >
                      {box.letters}
                      {box.missed && (
                        <PenMark
                          viewBox="0 0 160 140"
                          strokeWidth={3.5}
                          className="absolute -left-[32%] -top-[26%] h-[152%] w-[164%]"
                        >
                          <PenStroke
                            d={PEN_PATHS.loop}
                            delay={0.75}
                            duration={0.9}
                          />
                        </PenMark>
                      )}
                    </div>
                    <span
                      className={cn(
                        "font-ipa-sans text-lg",
                        box.missed
                          ? "font-bold text-pastel-pink-foreground"
                          : "text-muted-foreground"
                      )}
                    >
                      /{box.sound}/
                    </span>
                  </motion.div>
                ))}
              </div>
              <div className="mt-0.5 flex flex-col items-start gap-1 sm:flex-row sm:pl-[176px]">
                <PenArrow
                  variant="up-left"
                  delay={1.5}
                  className="ml-[29vw] h-[50px] w-[70px] flex-none sm:-ml-2"
                />
                <PenWords
                  delay={1.7}
                  className={cn(
                    penNote,
                    "-mt-1 ml-[14vw] max-w-[240px] -rotate-2 sm:ml-0 sm:mt-6"
                  )}
                  text="came out as “brone.” That’s the one to practice."
                />
              </div>
            </div>

            <figcaption className="space-y-3.5 border-t-2 border-dashed border-border pt-6">
              <span className="block text-sm text-muted-foreground">
                Next sentence, built around{" "}
                <span className="font-ipa-sans text-base text-foreground">
                  /aʊ/
                </span>
              </span>
              <p className="text-[clamp(24px,3vw,32px)] font-medium leading-normal">
                <PenUnderlined delay={2.3}>Now</PenUnderlined> the{" "}
                <PenUnderlined delay={2.5} alt>
                  brown
                </PenUnderlined>{" "}
                <PenUnderlined delay={2.7}>cow</PenUnderlined> sat{" "}
                <PenUnderlined delay={2.9} alt>
                  down
                </PenUnderlined>
                .
              </p>
              <PenWords
                delay={3.2}
                className={cn(penNote, "text-right -rotate-[1.5deg]")}
                text="four more tries at the same sound"
              />
            </figcaption>
          </figure>
        </PenGroup>
      </div>
    </div>
  </LandingSection>
);

export default SoundBoxesSection;
