import { useEffect } from "react";
import { Link } from "react-router-dom";
import { motion, useReducedMotion } from "framer-motion";
import { ArrowRight, RotateCcw, Star, Volume2 } from "lucide-react";
import type { Session } from "@/api";
import { Button } from "@/components/ui/button";
import { useSpeechSynthesis } from "@/hooks/useSpeechSynthesis";
import { useStartPattern } from "@/hooks/usePhonics";
import { finishMessage, type SessionResult } from "@/lib/phonics";

// The screen after the last line of a pattern session. It reads its message
// out loud, since the children using it are still learning to read, and it
// never shows the "Needs practice" label teachers see.
const PatternFinish = ({
  session,
  result,
}: {
  session: Session;
  result: SessionResult;
}) => {
  const { start, startingSlug } = useStartPattern();
  const { speak } = useSpeechSynthesis();
  const reduceMotion = useReducedMotion();
  const { title, detail } = finishMessage(result);
  const spoken = `${title} ${detail}`;

  useEffect(() => {
    speak(spoken, { rate: 0.95 });
  }, [speak, spoken]);

  return (
    <main className="flex min-h-dvh items-center justify-center bg-background p-6">
      <section
        aria-labelledby="finish-heading"
        className="w-full max-w-md rounded-3xl bg-card p-8 text-center shadow-sm ring-1 ring-border"
      >
        <motion.span
          initial={reduceMotion ? false : { scale: 0.6, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ type: "spring", stiffness: 260, damping: 16 }}
          className="mx-auto flex size-20 items-center justify-center rounded-full bg-pastel-yellow text-pastel-yellow-foreground"
        >
          <Star className="size-10" aria-hidden />
        </motion.span>
        <p className="mt-6 text-sm font-medium text-muted-foreground">
          {result.pattern_name}
        </p>
        <h1
          id="finish-heading"
          className="mt-1 text-3xl font-bold tracking-tight text-foreground"
        >
          {title}
        </h1>
        <p className="mt-3 text-lg text-foreground/80">{detail}</p>

        <div className="mt-8 flex flex-col gap-3">
          <Button
            size="lg"
            className="h-14 rounded-xl text-base"
            disabled={startingSlug !== null || !session.pattern_slug}
            onClick={() => session.pattern_slug && start(session.pattern_slug)}
          >
            <RotateCcw className="size-5" />
            {startingSlug ? "Starting…" : "Practice again"}
          </Button>
          <Button asChild variant="outline" size="lg" className="h-14 rounded-xl text-base">
            <Link to="/practice">
              Back to practice
              <ArrowRight className="size-5" />
            </Link>
          </Button>
          <Button
            variant="ghost"
            onClick={() => speak(spoken, { rate: 0.95 })}
            className="mx-auto rounded-xl text-muted-foreground"
          >
            <Volume2 className="size-5" />
            Hear it again
          </Button>
        </div>
      </section>
    </main>
  );
};

export default PatternFinish;
