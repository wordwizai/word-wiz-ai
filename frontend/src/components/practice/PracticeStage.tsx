import { useEffect, useRef, useState, type RefObject } from "react";
import { Link } from "react-router-dom";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { ArrowRight, House, Loader2, Mic, Puzzle, Volume2 } from "lucide-react";
import type { Session } from "@/api";
import WordBadgeRow from "@/components/WordBadgeRow";
import { Button } from "@/components/ui/button";
import { useSpeechSynthesis } from "@/hooks/useSpeechSynthesis";
import { activityTypeLabel } from "@/lib/activities";
import { cn } from "@/lib/utils";
import type { PracticeStageState, SentenceOptions } from "./types";
import PracticeCompanion from "./PracticeCompanion";
import { companionMood, isPraise } from "./companionMood";

// The children using this screen are still learning to read, so no step
// depends on reading an instruction. Every control is an icon whose look
// changes with its state, and the speaker button says out loud what to do.
interface PracticeStageProps extends PracticeStageState {
  session: Session;
  // Story and free practice: an arrow to the next sentence.
  next?: { visible: boolean; onNext: () => void };
  // Choice stories: two branches to pick from after reading.
  choices?: {
    visible: boolean;
    options: SentenceOptions | null;
    onChoose: (sentence: string) => void;
  };
}

const PracticeStage = ({
  session,
  wordArray,
  analysisData,
  feedback,
  showHighlightedWords,
  isRecording,
  isProcessing,
  isFeedbackPlaying,
  audioLevel,
  onStartRecording,
  onStopRecording,
  onReplayFeedback,
  next,
  choices,
}: PracticeStageProps) => {
  const [splitIntoSounds, setSplitIntoSounds] = useState(false);
  const { speak } = useSpeechSynthesis();

  const showNext = !!next?.visible;
  const showChoices = !!choices?.visible && !!choices.options;
  // Once there's somewhere to go, that becomes the main action and the mic
  // steps back to "read it again".
  const micIsSecondary = showNext || showChoices;
  const hasAttempted = showHighlightedWords || !!feedback;

  // An attempt runs from the moment the child starts reading until its
  // result comes back. Results are matched by the analysis object, which is
  // new for every attempt even when the feedback text repeats, so this
  // doesn't depend on seeing `isProcessing` (the server's events can land in
  // one render). Feedback restored with a saved session never opened an
  // attempt, so it can't celebrate.
  const [attemptOpen, setAttemptOpen] = useState(false);
  const [celebrating, setCelebrating] = useState(false);
  const analysisAtStart = useRef(analysisData);

  useEffect(() => {
    if (!isRecording) return;
    setAttemptOpen(true);
    setCelebrating(false);
    // Anything that lands while the child is still reading belongs to an
    // earlier attempt.
    analysisAtStart.current = analysisData;
  }, [isRecording, analysisData]);

  useEffect(() => {
    if (isRecording || !attemptOpen || !feedback) return;
    if (analysisData === analysisAtStart.current) return;
    setAttemptOpen(false);
    if (isPraise(feedback)) setCelebrating(true);
  }, [isRecording, attemptOpen, feedback, analysisData]);

  const mascotMood = companionMood({
    isRecording,
    isProcessing,
    isFeedbackPlaying,
    celebrating,
  });

  const spokenHelp = () => {
    if (isRecording) return "I'm listening. Read the words out loud.";
    if (showChoices && choices?.options) {
      const { option_1, option_2 } = choices.options;
      return `Pick what happens next. ${option_1.action}. Or, ${option_2.action}.`;
    }
    if (showNext)
      return "Tap the arrow for the next sentence, or tap the microphone to read this one again.";
    return "Tap the microphone, then read the words out loud. Tap any word to hear it.";
  };

  return (
    <div className="flex min-h-dvh flex-col bg-background">
      <header className="grid h-16 grid-cols-[1fr_auto_1fr] items-center gap-2 px-3 sm:px-6">
        <Button
          variant="ghost"
          asChild
          className="justify-self-start rounded-xl text-muted-foreground hover:text-foreground"
        >
          <Link to="/dashboard" aria-label="Home">
            <House className="size-5" />
            <span className="hidden sm:inline">Home</span>
          </Link>
        </Button>

        <div className="min-w-0 text-center">
          <h1 className="line-clamp-2 text-sm leading-snug font-semibold text-balance text-foreground sm:text-lg">
            {session.activity.title}
          </h1>
          <p className="text-xs text-muted-foreground">
            {activityTypeLabel(session.activity.activity_type)}
          </p>
        </div>

        <Button
          variant="outline"
          size="icon"
          onClick={() => setSplitIntoSounds((on) => !on)}
          aria-pressed={splitIntoSounds}
          aria-label="Split words into sounds"
          title="Split words into sounds"
          className={cn(
            "justify-self-end rounded-xl",
            splitIntoSounds &&
              "border-primary/40 bg-sidebar-accent text-primary hover:bg-sidebar-accent",
          )}
        >
          <Puzzle className="size-5" />
        </Button>
      </header>

      <main className="flex flex-1 flex-col items-center justify-center gap-6 px-4 pt-2">
        <section
          aria-label="Sentence to read"
          className="flex w-full max-w-4xl flex-col items-center gap-6 rounded-3xl bg-card p-5 shadow-sm ring-1 ring-border sm:p-8 md:p-10"
        >
          <WordBadgeRow
            wordArray={wordArray}
            analysisData={analysisData}
            showHighlightedWords={showHighlightedWords}
            splitIntoSounds={splitIntoSounds}
          />

          {/* While the child reads, the old feedback keeps its space (unseen)
              so the sentence doesn't jump. Once they stop it's gone until
              the new feedback arrives. */}
          <PracticeCompanion
            mood={mascotMood}
            feedback={attemptOpen && !isRecording ? null : feedback}
            quiet={isRecording}
            onReplay={onReplayFeedback}
            onCelebrateEnd={() => setCelebrating(false)}
          />

          {showChoices && choices?.options && (
            <ChoicePicker
              options={choices.options}
              onChoose={choices.onChoose}
            />
          )}
        </section>

        {/* Pinned to the bottom so the mic stays in reach under a long
            sentence or a pair of story choices. */}
        <div className="sticky bottom-0 z-10 flex w-full justify-center bg-gradient-to-t from-background from-70% to-background/0 pt-4 pb-[max(1.5rem,env(safe-area-inset-bottom))]">
          <div className="grid w-full max-w-md grid-cols-[1fr_auto_1fr] items-center gap-5">
            <Button
              variant="outline"
              size="icon"
              onClick={() => speak(spokenHelp(), { rate: 0.95 })}
              aria-label="Hear what to do"
              className="size-14 justify-self-end rounded-full"
            >
              <Volume2 className="size-6" />
            </Button>

            <RecordButton
              isRecording={isRecording}
              isProcessing={isProcessing}
              secondary={micIsSecondary}
              invite={!hasAttempted}
              audioLevel={audioLevel}
              onStart={onStartRecording}
              onStop={onStopRecording}
            />

            <div className="justify-self-start">
              <AnimatePresence>
                {showNext && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.6 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.6 }}
                    transition={{ type: "spring", stiffness: 260, damping: 18 }}
                  >
                    <Button
                      size="icon"
                      onClick={next?.onNext}
                      aria-label="Next sentence"
                      className="size-24 rounded-full shadow-lg active:scale-95"
                    >
                      <ArrowRight className="size-10" />
                    </Button>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

const RecordButton = ({
  isRecording,
  isProcessing,
  secondary,
  invite,
  audioLevel,
  onStart,
  onStop,
}: {
  isRecording: boolean;
  isProcessing: boolean;
  secondary: boolean;
  invite: boolean;
  audioLevel: RefObject<number>;
  onStart: () => void;
  onStop: () => void;
}) => {
  const reduceMotion = useReducedMotion();
  const idle = !isRecording && !isProcessing;

  return (
    <div className="relative flex size-24 items-center justify-center">
      {/* A slow halo on the one thing to tap, only before the first try. */}
      {idle && invite && !reduceMotion && (
        <motion.span
          aria-hidden
          className="absolute inset-0 rounded-full bg-primary/25"
          animate={{ scale: [1, 1.35], opacity: [0.6, 0] }}
          transition={{ duration: 2.2, repeat: Infinity, ease: "easeOut" }}
        />
      )}
      <button
        type="button"
        onClick={isRecording ? onStop : onStart}
        disabled={isProcessing}
        aria-label={
          isProcessing
            ? "Checking your reading"
            : isRecording
              ? "Stop recording"
              : "Start reading out loud"
        }
        className={cn(
          "relative flex size-24 items-center justify-center rounded-full transition-all duration-200 outline-none",
          "focus-visible:ring-[4px] focus-visible:ring-ring/50 active:scale-95",
          isProcessing && "cursor-default bg-secondary text-primary",
          isRecording &&
            "bg-primary text-primary-foreground shadow-lg ring-8 ring-primary/20",
          idle &&
            (secondary
              ? "border-2 border-primary/30 bg-card text-primary hover:bg-secondary"
              : "bg-primary text-primary-foreground shadow-lg hover:bg-primary/90"),
        )}
      >
        {isProcessing ? (
          <Loader2 className="size-10 animate-spin" />
        ) : isRecording ? (
          <LevelBars levelRef={audioLevel} />
        ) : (
          <Mic className="size-10" />
        )}
      </button>
    </div>
  );
};

// Five bars that follow the microphone level, so a child can see it hears
// them. Driven by a rAF loop writing transforms directly; no React state.
const BAR_SHAPE = [0.55, 0.8, 1, 0.8, 0.55];

const LevelBars = ({ levelRef }: { levelRef: RefObject<number> }) => {
  const barsRef = useRef<(HTMLSpanElement | null)[]>([]);

  useEffect(() => {
    let frame = 0;
    let smoothed = 0;
    const tick = () => {
      // Speech RMS sits around 0.02-0.2; map that onto 0-1.
      const target = Math.min(1, (levelRef.current ?? 0) * 7);
      smoothed += (target - smoothed) * 0.35;
      barsRef.current.forEach((bar, i) => {
        if (bar)
          bar.style.transform = `scaleY(${0.22 + 0.78 * smoothed * BAR_SHAPE[i]})`;
      });
      frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [levelRef]);

  return (
    <span aria-hidden className="flex h-10 items-center gap-1.5">
      {BAR_SHAPE.map((_, i) => (
        <span
          key={i}
          ref={(el) => {
            barsRef.current[i] = el;
          }}
          className="h-full w-1.5 origin-center scale-y-[0.22] rounded-full bg-current"
        />
      ))}
    </span>
  );
};

const ChoicePicker = ({
  options,
  onChoose,
}: {
  options: SentenceOptions;
  onChoose: (sentence: string) => void;
}) => {
  const ref = useRef<HTMLDivElement>(null);
  const reduceMotion = useReducedMotion();

  // The choices are the next step, so bring them above the pinned controls
  // when they arrive under a long sentence.
  useEffect(() => {
    ref.current?.scrollIntoView({
      behavior: reduceMotion ? "auto" : "smooth",
      block: "nearest",
    });
  }, [reduceMotion]);

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full max-w-2xl scroll-mb-40"
    >
      <h2 className="mb-3 text-center text-base font-semibold text-foreground">
        What happens next?
      </h2>
      <div className="grid gap-3 sm:grid-cols-2">
        {[options.option_1, options.option_2].map((option) => (
          <button
            key={option.sentence}
            type="button"
            onClick={() => onChoose(option.sentence)}
            className={cn(
              "flex min-h-20 items-center gap-4 rounded-2xl border-2 border-border bg-card p-4 text-left",
              "transition-all duration-200 outline-none hover:-translate-y-0.5 hover:border-primary/50 hover:shadow-lg",
              "focus-visible:ring-[3px] focus-visible:ring-ring/50 active:scale-[0.98]",
            )}
          >
            <span
              aria-hidden
              className="flex size-12 shrink-0 items-center justify-center rounded-xl bg-secondary text-3xl"
            >
              {option.icon}
            </span>
            <span className="text-lg font-semibold text-foreground">
              {option.action}
            </span>
          </button>
        ))}
      </div>
    </motion.div>
  );
};

export default PracticeStage;
