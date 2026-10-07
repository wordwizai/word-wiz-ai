import { Check, ChevronDown, Loader2 } from "lucide-react";
import type { PatternProgress, PhonicsPath } from "@/api";
import {
  STATUS_LABEL,
  STATUS_TONE,
  STUDENT_LABEL,
} from "@/lib/phonics";
import { cn } from "@/lib/utils";

type Audience = "student" | "teacher";

// The units in order. The unit holding the next pattern starts open; the
// rest show how far along they are and open on tap. Without onStart it is
// read-only (a teacher looking at one student's path).
const PhonicsPathView = ({
  path,
  audience,
  onStart,
  startingSlug = null,
}: {
  path: PhonicsPath;
  audience: Audience;
  onStart?: (slug: string) => void;
  startingSlug?: string | null;
}) => {
  const nextUnit = path.units.find((unit) =>
    unit.patterns.some((p) => p.slug === path.next_slug)
  )?.id;
  const doneWord = audience === "student" ? "done" : "mastered";

  return (
    <ol className="space-y-3">
      {path.units.map((unit, i) => {
        const complete = unit.mastered_count === unit.patterns.length;
        return (
          <li key={unit.id}>
            <details
              open={unit.id === nextUnit}
              className="group rounded-2xl border bg-card shadow-xs"
            >
              <summary className="flex min-h-16 cursor-pointer list-none items-center gap-4 px-4 py-3 sm:px-5 [&::-webkit-details-marker]:hidden">
                <span
                  className={cn(
                    "flex size-9 shrink-0 items-center justify-center rounded-full text-sm font-semibold",
                    complete
                      ? "bg-pastel-mint text-pastel-mint-foreground"
                      : "bg-muted text-muted-foreground"
                  )}
                >
                  {complete ? <Check className="size-4" aria-label="Done" /> : i + 1}
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block font-semibold text-foreground">{unit.title}</span>
                  <span className="block text-sm text-muted-foreground">
                    {unit.grade} · {unit.mastered_count} of {unit.patterns.length} {doneWord}
                  </span>
                </span>
                <ChevronDown
                  className="size-4 shrink-0 text-muted-foreground transition-transform group-open:rotate-180"
                  aria-hidden
                />
              </summary>
              <ul className="flex flex-wrap gap-2 px-4 pb-4 sm:px-5 sm:pb-5">
                {unit.patterns.map((pattern) => (
                  <li key={pattern.slug}>
                    <PatternTile
                      pattern={pattern}
                      audience={audience}
                      isNext={pattern.slug === path.next_slug}
                      onStart={onStart}
                      isStarting={startingSlug === pattern.slug}
                      disabled={startingSlug !== null}
                    />
                  </li>
                ))}
              </ul>
            </details>
          </li>
        );
      })}
    </ol>
  );
};

const PatternTile = ({
  pattern,
  audience,
  isNext,
  onStart,
  isStarting,
  disabled,
}: {
  pattern: PatternProgress;
  audience: Audience;
  isNext: boolean;
  onStart?: (slug: string) => void;
  isStarting: boolean;
  disabled: boolean;
}) => {
  const label = (audience === "student" ? STUDENT_LABEL : STATUS_LABEL)[pattern.status];
  const body = (
    <>
      {isStarting ? (
        <Loader2 className="size-3.5 animate-spin" aria-hidden />
      ) : pattern.status === "mastered" ? (
        <Check className="size-3.5" aria-hidden />
      ) : pattern.status !== "not_started" ? (
        <span className="size-2 rounded-full bg-current" aria-hidden />
      ) : null}
      {pattern.name}
      <span className="sr-only">, {label}</span>
    </>
  );
  const className = cn(
    "inline-flex min-h-11 items-center gap-1.5 rounded-xl px-3 text-sm font-medium",
    STATUS_TONE[pattern.status],
    isNext && "ring-2 ring-primary"
  );

  if (!onStart) return <span className={className}>{body}</span>;
  return (
    <button
      type="button"
      onClick={() => onStart(pattern.slug)}
      disabled={disabled}
      aria-busy={isStarting}
      className={cn(
        className,
        "transition-transform outline-none hover:-translate-y-0.5 focus-visible:ring-[3px] focus-visible:ring-ring/60",
        "disabled:cursor-default disabled:hover:translate-y-0"
      )}
    >
      {body}
    </button>
  );
};

export default PhonicsPathView;
