import { motion } from "framer-motion";
import { Check, Volume2 } from "@/components/icons";
import { cn } from "@/lib/utils";
import LandingSection from "./LandingSection";
import { PEN_PATHS } from "./penPaths";
import { PenGroup, PenMark, PenStroke } from "./TeacherPen";
import { cardGlow, floatingCard, sectionTitle, tryPill } from "./styles";

const POINTS = [
  "Checks every sound in every word",
  "Builds the next sentence around the miss",
  "Free, with no ads and nothing to upgrade",
];

// "brown" as a reading teacher's sound boxes, one box per sound.
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

/** The practice sound, picked out in the next sentence. */
const Ow = () => <span className="text-primary">ow</span>;

/** "It hears the sound, not just the word", shown as sound boxes with the missed one circled. */
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
          {POINTS.map((point) => (
            <li key={point} className="flex items-center gap-3.5 font-medium">
              <Check className="size-5 flex-none text-primary" aria-hidden="true" />
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
                <strong className="font-semibold text-foreground">brown</strong>{" "}
                as &ldquo;brone&rdquo;
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
                        "relative flex aspect-square w-[min(96px,17vw)] items-center justify-center border-2 border-foreground/15 bg-card text-[clamp(28px,4vw,40px)] font-medium",
                        i === 0 && "rounded-l-[14px]",
                        i === BOXES.length - 1 && "rounded-r-[14px]"
                      )}
                    >
                      {/* The missed sound gets a soft tile inside its box, so the row keeps one rounded outline. */}
                      {box.missed && (
                        <span
                          aria-hidden="true"
                          className="absolute inset-[7px] rounded-[11px] bg-pastel-pink"
                        />
                      )}
                      <span
                        className={cn(
                          "relative",
                          box.missed && "font-semibold text-pastel-pink-foreground"
                        )}
                      >
                        {box.letters}
                      </span>
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
            </div>

            <figcaption className="space-y-3 border-t border-border pt-6">
              <span className="block text-sm text-muted-foreground">
                Next sentence, built around{" "}
                <span className="font-ipa-sans text-base text-foreground">
                  /aʊ/
                </span>
              </span>
              <p className="text-[clamp(24px,3vw,32px)] font-medium leading-normal">
                N<Ow />
                {" the br"}
                <Ow />
                {"n c"}
                <Ow />
                {" sat d"}
                <Ow />
                n.
              </p>
            </figcaption>
          </figure>
        </PenGroup>
      </div>
    </div>
  </LandingSection>
);

export default SoundBoxesSection;
