import { ArrowRight, Blocks, Loader2, PartyPopper } from "lucide-react";
import type { PhonicsPath } from "@/api";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useStartPattern } from "@/hooks/usePhonics";

// The Practice page's way into the phonics path: the next pattern to work
// on, and a link to every unit. Laid out by its own width, like the
// Dashboard's continue card.
const ContinuePathCard = ({ path }: { path: PhonicsPath | null }) => {
  const { start, startingSlug } = useStartPattern();
  if (!path) return <Skeleton className="h-40 rounded-3xl" />;

  const unitIndex = path.units.findIndex((unit) =>
    unit.patterns.some((p) => p.slug === path.next_slug)
  );
  const unit = unitIndex >= 0 ? path.units[unitIndex] : null;
  const pattern = unit?.patterns.find((p) => p.slug === path.next_slug) ?? null;

  return (
    <div className="@container rounded-3xl bg-pastel-mint p-5 shadow-sm ring-1 ring-inset ring-black/5 sm:p-8 dark:shadow-black/50 dark:inset-shadow-2xs dark:inset-shadow-white/10">
      <div className="flex flex-col gap-5 @xl:flex-row @xl:items-center @xl:gap-6">
        <div className="flex min-w-0 flex-1 items-center gap-4 sm:gap-6">
          <span className="flex size-14 shrink-0 items-center justify-center rounded-2xl bg-white/60 text-pastel-mint-foreground sm:size-20 dark:bg-white/10">
            {pattern ? (
              <Blocks className="size-7 sm:size-10" />
            ) : (
              <PartyPopper className="size-7 sm:size-10" />
            )}
          </span>
          <div className="min-w-0">
            <p className="text-sm font-medium text-foreground/70">
              {unit ? `Unit ${unitIndex + 1} · ${unit.title}` : "Phonics path"}
            </p>
            <h3 className="mt-1 text-xl leading-tight font-bold tracking-tight text-pastel-mint-foreground sm:text-3xl">
              {pattern ? pattern.name : "Every unit done!"}
            </h3>
            <p className="mt-1 text-sm text-foreground/70">
              {unit
                ? `${unit.mastered_count} of ${unit.patterns.length} done in this unit`
                : "Pick any pattern to read it again."}
            </p>
          </div>
        </div>
        {pattern && (
          <Button
            size="lg"
            onClick={() => start(pattern.slug)}
            disabled={startingSlug !== null}
            aria-busy={startingSlug !== null}
            className="h-14 w-full shrink-0 rounded-xl px-8 text-base font-semibold @xl:w-auto active:scale-[0.98]"
          >
            {startingSlug ? "Starting…" : "Start"}
            {startingSlug ? (
              <Loader2 className="size-5 animate-spin" />
            ) : (
              <ArrowRight className="size-5" />
            )}
          </Button>
        )}
      </div>
    </div>
  );
};

export default ContinuePathCard;
