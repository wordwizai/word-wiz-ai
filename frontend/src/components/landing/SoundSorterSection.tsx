import { Suspense, lazy, useCallback, useEffect, useRef, useState } from "react";
import { Volume2 } from "@/components/icons";
import { cn } from "@/lib/utils";
import LandingSection from "./LandingSection";
import { PenGroup } from "./TeacherPen";
import { cardGlow, floatingCard, sectionTitle, tryPill } from "./styles";
import { BOXES, PRAISE_PER, READINGS, type Score } from "./soundSorter/model";
import type { SorterControls, SorterInfo } from "./soundSorter/live";

const SoundSorterFigure = lazy(() => import("./soundSorter/SoundSorterFigure"));

const SOUNDS = BOXES.length;
const NUMBERS = ["no", "one", "two", "three", "four", "five", "six", "seven", "eight"];
const say = (n: number) => NUMBERS[n] ?? String(n);
const Say = (n: number) => say(n).charAt(0).toUpperCase() + say(n).slice(1);

/** Why the machine said what it said, in a parent's words. */
function whyOf(score: Score): string {
  const flagged = score.words.find((word) => word.clear);
  if (flagged) {
    const wrong = flagged.errors === flagged.total ? `All ${say(flagged.total)} sounds` : `${Say(flagged.errors)} of the ${say(flagged.total)} sounds`;
    return `${wrong} in “${flagged.text}” were wrong, so Word Wiz names one and shows how to say it.`;
  }
  if (!score.errors) return "Every sound fit in its box.";
  const slipped = `${Say(score.errors)} of ${say(SOUNDS)} sounds slipped`;
  if (score.sentencePer <= PRAISE_PER) return `${slipped}, and no word was clearly wrong, so the reading still earns praise.`;
  return `${slipped}, more than one in five, but no word was clearly wrong. So Word Wiz encourages without picking on a word.`;
}

/** Follows the site's light/dark switch, which lives on <html class="dark">. */
function useDarkClass() {
  const [dark, setDark] = useState(() => typeof document !== "undefined" && document.documentElement.classList.contains("dark"));
  useEffect(() => {
    const root = document.documentElement;
    const observer = new MutationObserver(() => setDark(root.classList.contains("dark")));
    observer.observe(root, { attributes: true, attributeFilter: ["class"] });
    return () => observer.disconnect();
  }, []);
  return dark;
}

/** "Watch it check every sound", the sound sorter, an isometric machine that acts out the scoring. */
const SoundSorterSection = ({ id }: { id: string }) => {
  const holder = useRef<HTMLDivElement>(null);
  const controls = useRef<SorterControls | null>(null);
  const [near, setNear] = useState(false);
  const [info, setInfo] = useState<SorterInfo | null>(null);
  const dark = useDarkClass();

  // Load the machine only when the section comes near, so it never weighs on the first paint.
  useEffect(() => {
    const node = holder.current;
    if (!node) return;
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          setNear(true);
          observer.disconnect();
        }
      },
      { rootMargin: "600px 0px" },
    );
    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  const onChange = useCallback((next: SorterInfo) => setInfo(next), []);
  const reading = info?.reading ?? 0;
  const spoken = info?.spoken ?? false;

  return (
    <LandingSection id={id} className="scroll-mt-20 px-4 py-20 sm:px-6 md:py-24">
      <div className="mx-auto max-w-6xl">
        <PenGroup className="max-w-2xl space-y-5">
          <h2 className={sectionTitle}>
            Watch it check
            <br />
            <span className="text-primary">every sound.</span>
          </h2>
          <p className="text-lg text-muted-foreground">
            Each word gets a row of boxes, one for every sound it needs. Word
            Wiz drops each sound your child says into its box. A sound that
            matches drops right in, and one that doesn&rsquo;t fit sticks, so
            the app knows exactly which sound slipped.
          </p>
          <p className="text-muted-foreground">
            It only corrects a word when three or more of its sounds were
            wrong. A small slip in an otherwise good reading still gets a
            &ldquo;Great job!&rdquo;
          </p>
        </PenGroup>

        <div className="relative -mx-2 mt-10 sm:mx-0 sm:p-5">
          <div aria-hidden="true" className={cardGlow} />
          <figure className={cn(floatingCard, "m-0 space-y-5 px-2 py-4 sm:p-7")}>
            <div ref={holder} className={near ? "w-full" : "aspect-[760/424] w-full"}>
              {near && (
                <Suspense fallback={<div className="aspect-[760/424] w-full" />}>
                  <SoundSorterFigure dark={dark} onChange={onChange} controlsRef={controls} />
                </Suspense>
              )}
            </div>

            <figcaption className="space-y-4 px-1 pb-1 sm:px-2">
              <div className="flex flex-wrap items-center gap-2">
                <span className="mr-1 text-[13px] text-muted-foreground">Your child reads</span>
                {READINGS.map((r, i) => (
                  <button
                    key={r.said}
                    type="button"
                    aria-pressed={reading === i}
                    onClick={() => controls.current?.play(i)}
                    className={cn(
                      "min-h-9 rounded-full border px-3.5 text-[14px] font-medium transition-colors",
                      reading === i
                        ? "border-primary bg-primary text-primary-foreground"
                        : "border-border bg-card hover:border-primary/50 hover:text-primary"
                    )}
                  >
                    {r.said}
                  </button>
                ))}
              </div>
              <div className="min-h-[76px] space-y-2" aria-live="polite">
                {spoken && info ? (
                  <>
                    <p className={cn(tryPill, "max-w-full rounded-2xl")}>
                      <Volume2 className="size-[18px] flex-none" aria-hidden="true" />
                      <span>{info.score.says}</span>
                    </p>
                    <p className="text-[14px] text-muted-foreground">{whyOf(info.score)}</p>
                  </>
                ) : (
                  <p className="pt-2 text-[15px] text-muted-foreground">
                    Listening to &ldquo;{READINGS[reading].said}&rdquo; and checking every sound&hellip;
                  </p>
                )}
              </div>
            </figcaption>
          </figure>
        </div>
      </div>
    </LandingSection>
  );
};

export default SoundSorterSection;
