import type { ReactNode } from "react";
import { Mic, Volume2 } from "lucide-react";
import { cn } from "@/lib/utils";
import LandingSection from "./LandingSection";
import { PEN_PATHS } from "./penPaths";
import {
  PenArrow,
  PenGroup,
  PenMark,
  PenNumeral,
  PenStroke,
  PenWords,
} from "./TeacherPen";
import { penNote, sectionTitle } from "./styles";

const stepCard =
  "relative flex h-[250px] flex-col justify-between gap-4 rounded-3xl border border-border bg-card p-7 shadow-xl dark:shadow-black/40";

// Word chips in WordBadge's colors: "good" and "close" bands.
const goodChip =
  "border-2 border-transparent bg-pastel-mint text-pastel-mint-foreground";
const closeChip =
  "border-2 border-dashed border-pastel-yellow-foreground bg-pastel-yellow text-pastel-yellow-foreground";

const Step = ({
  number,
  numberTilt,
  card,
  note,
  noteTilt,
  title,
  text,
  arrow,
}: {
  number: "1" | "2" | "3";
  numberTilt: string;
  card: ReactNode;
  note: string;
  noteTilt: string;
  title: string;
  text: string;
  arrow?: "right-up" | "right-down";
}) => (
  <li>
    <PenGroup className="relative flex flex-col gap-[18px] pt-9" amount={0.5}>
      <PenNumeral
        digit={number}
        delay={0.1}
        className={cn("absolute -left-2 -top-5 z-10 h-[84px] w-14", numberTilt)}
      />
      <div className={stepCard}>
        {card}
        {arrow && (
          <PenArrow
            variant={arrow}
            delay={0.9}
            className="absolute -right-11 top-[110px] hidden h-[30px] w-12 lg:block"
          />
        )}
      </div>
      <PenWords
        delay={0.6}
        text={note}
        className={cn(penNote, noteTilt)}
      />
      <div className="space-y-1.5">
        <h3 className="text-xl font-semibold">{title}</h3>
        <p className="text-muted-foreground">{text}</p>
      </div>
    </PenGroup>
  </li>
);

const ReadingCard = () => (
  <>
    <div className="space-y-2.5">
      <span className="text-[13px] text-muted-foreground">Read this out loud</span>
      <p className="text-[26px] font-medium leading-snug">
        The brown dog ran to the park.
      </p>
    </div>
    <div className="flex items-center gap-3.5">
      <span className="flex size-[52px] items-center justify-center rounded-full bg-primary text-primary-foreground ring-8 ring-primary/10">
        <Mic className="size-[22px]" aria-hidden="true" />
      </span>
      <span aria-hidden="true" className="ml-1.5 flex h-[22px] items-end gap-[3px]">
        {[8, 16, 22, 12, 6].map((h, i) => (
          <span
            key={i}
            className="w-1 rounded-sm bg-primary/60"
            style={{ height: h }}
          />
        ))}
      </span>
      <span className="text-sm text-muted-foreground">Listening</span>
    </div>
  </>
);

const SOUNDS = [
  { letters: "b", sound: "b" },
  { letters: "r", sound: "r" },
  { letters: "ow", sound: "aʊ", missed: true },
  { letters: "n", sound: "n" },
];

const CheckedCard = () => (
  <>
    <div className="flex flex-wrap gap-2">
      {["The", "brown", "dog", "ran", "to", "the", "park"].map((word, i) =>
        word === "brown" ? (
          <span
            key={i}
            className={cn("relative rounded-xl px-3 py-1 text-xl font-medium", closeChip)}
          >
            brown
            <PenMark
              viewBox="0 0 108 64"
              className="absolute -left-[14%] -top-[30%] h-[160%] w-[128%]"
            >
              <PenStroke d={PEN_PATHS.loopFlat} delay={0.5} duration={0.9} />
            </PenMark>
          </span>
        ) : (
          <span
            key={i}
            className={cn("rounded-xl px-3 py-1 text-xl font-medium", goodChip)}
          >
            {word}
          </span>
        )
      )}
    </div>
    <div className="flex items-end gap-1.5">
      {SOUNDS.map((s) => (
        <div key={s.letters} className="flex flex-col items-center gap-1">
          <span
            className={cn(
              "rounded-lg border-[1.5px] px-2.5 py-1 font-medium",
              s.missed
                ? "border-pastel-pink-foreground bg-pastel-pink font-semibold text-pastel-pink-foreground"
                : "border-transparent bg-pastel-mint text-pastel-mint-foreground"
            )}
          >
            {s.letters}
          </span>
          <span
            className={cn(
              "font-ipa-sans text-[13px]",
              s.missed
                ? "font-bold text-pastel-pink-foreground"
                : "text-muted-foreground"
            )}
          >
            /{s.sound}/
          </span>
        </div>
      ))}
      <span className="ml-2.5 pb-6 text-[13px] text-muted-foreground">
        1 of 4 sounds off
      </span>
    </div>
  </>
);

const FeedbackCard = () => (
  <>
    <div className="flex items-start gap-3">
      <span className="flex size-10 flex-none items-center justify-center rounded-[14px] bg-orange-100 text-orange-700 dark:bg-orange-500/15 dark:text-orange-300">
        <Volume2 className="size-5" aria-hidden="true" />
      </span>
      <p className="text-[15px] leading-relaxed">
        Nice reading! Look at <strong className="font-semibold">brown</strong>.
        The <strong className="font-semibold">ow</strong> says{" "}
        <span className="font-ipa-sans">/aʊ/</span>, like when you bump your
        knee. Want to try it again?
      </p>
    </div>
    <div className="space-y-1.5 border-t-2 border-dashed border-border pt-3.5">
      <span className="text-[13px] text-muted-foreground">Next sentence</span>
      <p className="text-[22px] font-medium">Now the brown cow sat down.</p>
    </div>
  </>
);

/** How a session goes, shown with the practice screen's own pieces. */
const SessionStepsSection = ({ id }: { id: string }) => (
  <LandingSection id={id} className="scroll-mt-20 px-4 py-20 sm:px-6 md:py-24">
    <div className="mx-auto max-w-6xl space-y-14">
      <div className="max-w-2xl space-y-3.5">
        <h2 className={sectionTitle}>
          Read, get feedback,
          <br />
          <span className="text-primary">read again.</span>
        </h2>
        <p className="text-lg text-muted-foreground">
          Three steps, repeated for as long as your child wants to keep going.
        </p>
      </div>

      <ol className="grid grid-cols-1 gap-x-10 gap-y-12 lg:grid-cols-3">
        <Step
          number="1"
          numberTilt="-rotate-6"
          card={<ReadingCard />}
          note="one sentence at a time, at their pace"
          noteTilt="-rotate-1"
          title="Your child reads aloud"
          text="A sentence appears and Word Wiz listens through the microphone."
          arrow="right-up"
        />
        <Step
          number="2"
          numberTilt="rotate-[4deg]"
          card={<CheckedCard />}
          note="green means every sound landed"
          noteTilt="rotate-1"
          title="Every sound gets checked"
          text="The recording is broken into sounds and compared, word by word, with how the sentence should sound."
          arrow="right-down"
        />
        <Step
          number="3"
          numberTilt="-rotate-3"
          card={<FeedbackCard />}
          note="said out loud, so pre-readers get it too"
          noteTilt="-rotate-1"
          title="Feedback, then a new sentence"
          text="Your child hears what to try differently, and the next sentence is built around the sound that needs practice."
        />
      </ol>
    </div>
  </LandingSection>
);

export default SessionStepsSection;
