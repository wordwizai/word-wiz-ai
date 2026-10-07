import { Link } from "react-router-dom";
import { ArrowRight, ChevronRight, Loader2 } from "lucide-react";
import type { StudentAssignment } from "@/api";
import { SectionHeader } from "@/components/AppPage";
import PatternStatusChip from "@/components/phonics/PatternStatusChip";
import { useStartPattern } from "@/hooks/usePhonics";
import { activityPastel } from "@/lib/activities";
import { orderAssignments, type PatternStatus } from "@/lib/phonics";
import { cn } from "@/lib/utils";

const ACTION: Record<PatternStatus, string> = {
  not_started: "Start",
  in_progress: "Continue",
  needs_practice: "Practice again",
  mastered: "Read again",
};

// The patterns a teacher assigned, open ones first. Renders nothing for a
// child with no teacher or nothing assigned.
const TeacherAssignments = ({
  assignments,
  onlyOpen = false,
  limit,
}: {
  assignments: StudentAssignment[] | null;
  onlyOpen?: boolean;
  limit?: number;
}) => {
  const { start, startingSlug } = useStartPattern();
  if (!assignments) return null;
  const ordered = orderAssignments(assignments).filter(
    (a) => !onlyOpen || a.status !== "mastered"
  );
  if (ordered.length === 0) return null;
  const shown = limit ? ordered.slice(0, limit) : ordered;

  return (
    <section aria-labelledby="teacher-assignments-heading">
      <SectionHeader
        id="teacher-assignments-heading"
        title="From your teacher"
        action={
          shown.length < ordered.length && (
            <Link
              to="/practice"
              className="inline-flex min-h-11 items-center gap-1 text-sm font-semibold text-primary hover:underline underline-offset-4"
            >
              See all
              <ChevronRight className="size-4" />
            </Link>
          )
        }
      />
      <ul className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {shown.map((assignment) => {
          const pastel = activityPastel(assignment.id);
          const isStarting = startingSlug === assignment.pattern_slug;
          return (
            <li key={assignment.id}>
              <button
                type="button"
                onClick={() => start(assignment.pattern_slug)}
                disabled={startingSlug !== null}
                aria-busy={isStarting}
                className={cn(
                  "flex h-full w-full flex-col rounded-2xl p-5 text-left",
                  "shadow-sm ring-1 ring-inset ring-black/5",
                  "dark:shadow-black/50 dark:inset-shadow-2xs dark:inset-shadow-white/10",
                  "transition-all duration-200 outline-none",
                  "hover:-translate-y-0.5 hover:shadow-lg active:translate-y-0 active:scale-[0.99]",
                  "focus-visible:ring-[3px] focus-visible:ring-ring/60",
                  "disabled:cursor-default disabled:hover:translate-y-0 disabled:hover:shadow-sm",
                  startingSlug !== null && !isStarting && "opacity-60"
                )}
                style={{ backgroundColor: pastel.background }}
              >
                <span className="flex items-center justify-between gap-2">
                  <span className="truncate text-xs font-medium text-foreground/70">
                    {assignment.class_name}
                  </span>
                  <PatternStatusChip
                    status={assignment.status}
                    audience="student"
                    className="ring-1 ring-inset ring-black/5"
                  />
                </span>
                <span
                  className="mt-3 text-lg font-semibold leading-snug"
                  style={{ color: pastel.foreground }}
                >
                  {assignment.pattern_name}
                </span>
                <span className="mt-1 text-sm text-foreground/70">
                  {assignment.unit_title}
                </span>
                <span
                  className="mt-auto inline-flex items-center gap-1.5 pt-4 text-sm font-semibold"
                  style={{ color: pastel.foreground }}
                >
                  {isStarting ? (
                    <>
                      <Loader2 className="size-4 animate-spin" />
                      Starting…
                    </>
                  ) : (
                    <>
                      {ACTION[assignment.status]}
                      <ArrowRight className="size-4" />
                    </>
                  )}
                </span>
              </button>
            </li>
          );
        })}
      </ul>
    </section>
  );
};

export default TeacherAssignments;
