import { useContext, useEffect, useState } from "react";
import { ChevronDown, Trash2 } from "lucide-react";
import { AuthContext } from "@/contexts/AuthContext";
import { deleteAssignment, getClassAssignments, type ClassAssignment } from "@/api";
import PatternStatusChip from "@/components/phonics/PatternStatusChip";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { STATUS_LABEL, type PatternStatus } from "@/lib/phonics";
import { getApiErrorMessage } from "@/utils/errorHandling";

const BAR_ORDER: PatternStatus[] = ["mastered", "needs_practice", "in_progress", "not_started"];

// Just the fill colour of each status tone, for the bar segments.
const BAR_FILL: Record<PatternStatus, string> = {
  mastered: "bg-pastel-mint-foreground",
  needs_practice: "bg-pastel-yellow-foreground",
  in_progress: "bg-pastel-blue-foreground",
  not_started: "bg-muted",
};

const AssignmentsPanel = ({
  classId,
  refreshKey,
}: {
  classId: number;
  refreshKey: number;
}) => {
  const { token } = useContext(AuthContext);
  const [assignments, setAssignments] = useState<ClassAssignment[] | null>(null);
  const [error, setError] = useState("");
  const [removingId, setRemovingId] = useState<number | null>(null);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    getClassAssignments(token, classId)
      .then((data) => {
        if (cancelled) return;
        setAssignments(data);
        setError("");
      })
      .catch((err) => {
        if (!cancelled) setError(getApiErrorMessage(err, "Couldn't load assignments"));
      });
    return () => {
      cancelled = true;
    };
  }, [classId, token, refreshKey]);

  const remove = async (assignmentId: number) => {
    setRemovingId(assignmentId);
    try {
      await deleteAssignment(token ?? "", classId, assignmentId);
      setAssignments((list) => list?.filter((a) => a.id !== assignmentId) ?? null);
    } catch (err) {
      setError(getApiErrorMessage(err, "Couldn't remove that assignment"));
    } finally {
      setRemovingId(null);
    }
  };

  return (
    <Card className="gap-0 rounded-2xl py-0 shadow-xs">
      <div className="p-6">
        <h2 className="text-lg font-bold text-foreground">Assignments</h2>
        <p className="mt-1 mb-4 text-sm text-muted-foreground">
          Status comes from each student's latest finished session for the
          pattern, including practice at home. Reading 80% of the pattern's
          words right counts as mastered.
        </p>
        {error && (
          <p role="alert" className="mb-4 text-sm text-destructive">
            {error}
          </p>
        )}

        {assignments === null && error ? null : assignments === null ? (
          <div className="space-y-3">
            {Array.from({ length: 3 }, (_, i) => (
              <Skeleton key={i} className="h-16 rounded-xl" />
            ))}
          </div>
        ) : assignments.length === 0 ? (
          <div className="rounded-2xl border border-dashed px-6 py-10 text-center">
            <p className="font-medium text-foreground">Nothing assigned yet</p>
            <p className="mt-1 text-sm text-muted-foreground">
              Choose Assign practice to give the class a whole unit or a single pattern.
            </p>
          </div>
        ) : (
          <>
          <div className="mb-4 flex flex-wrap gap-2" aria-hidden>
            {BAR_ORDER.map((status) => (
              <PatternStatusChip key={status} status={status} audience="teacher" />
            ))}
          </div>
          <ul className="space-y-3">
            {assignments.map((assignment) => {
              const total = assignment.students.length;
              return (
                <li key={assignment.id}>
                  <details className="group rounded-xl border">
                    <summary className="flex cursor-pointer list-none flex-wrap rounded-xl outline-none focus-visible:ring-[3px] focus-visible:ring-ring/60 items-center gap-x-4 gap-y-2 px-4 py-3 [&::-webkit-details-marker]:hidden">
                      <span className="order-1 min-w-0 flex-1">
                        <span className="block font-medium text-foreground">
                          {assignment.pattern_name ?? "No longer available"}
                        </span>
                        <span className="block text-sm text-muted-foreground">
                          {assignment.unit_title ? `${assignment.unit_title} · ` : ""}
                          {assignment.whole_class
                            ? "Whole class"
                            : `${total} student${total === 1 ? "" : "s"}`}
                        </span>
                      </span>
                      <span className="order-3 flex w-full basis-full items-center gap-3 sm:order-2 sm:w-64 sm:basis-auto">
                        <span className="flex h-2.5 flex-1 gap-0.5 overflow-hidden rounded-full bg-muted" aria-hidden>
                          {total > 0 &&
                            BAR_ORDER.map((status) =>
                              assignment.counts[status] > 0 ? (
                                <span
                                  key={status}
                                  className={`h-full ${BAR_FILL[status]}`}
                                  style={{ width: `${(assignment.counts[status] / total) * 100}%` }}
                                />
                              ) : null
                            )}
                        </span>
                        <span className="sr-only">
                          {BAR_ORDER.map(
                            (s) => `${assignment.counts[s]} ${STATUS_LABEL[s].toLowerCase()}`
                          ).join(", ")}
                        </span>
                        <span className="text-xs whitespace-nowrap text-muted-foreground" aria-hidden>
                          {assignment.counts.mastered}/{total} mastered
                        </span>
                      </span>
                      <ChevronDown
                        className="order-2 size-4 sm:order-3 shrink-0 text-muted-foreground transition-transform group-open:rotate-180"
                        aria-hidden
                      />
                    </summary>

                    <div className="border-t px-4 py-3">
                      {total === 0 ? (
                        <p className="text-sm text-muted-foreground">
                          No one in the class has this right now.
                        </p>
                      ) : (
                        <div className="overflow-x-auto">
                          <table className="w-full text-sm">
                            <thead>
                              <tr className="text-left text-xs text-muted-foreground">
                                <th className="py-1 font-medium">Student</th>
                                <th className="py-1 font-medium">Status</th>
                                <th className="py-1 text-right font-medium">Words right</th>
                                <th className="py-1 text-right font-medium">Times finished</th>
                              </tr>
                            </thead>
                            <tbody>
                              {assignment.students.map((student) => (
                                <tr key={student.id} className="border-t">
                                  <td className="py-2 pr-3 text-foreground">
                                    {student.full_name || "Student"}
                                  </td>
                                  <td className="py-2 pr-3">
                                    <PatternStatusChip status={student.status} audience="teacher" />
                                  </td>
                                  <td className="py-2 text-right tabular-nums">
                                    {student.words_total
                                      ? `${student.words_correct}/${student.words_total}`
                                      : "–"}
                                  </td>
                                  <td className="py-2 text-right tabular-nums">{student.tries}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      )}
                      <div className="mt-3 flex justify-end">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => remove(assignment.id)}
                          disabled={removingId !== null}
                          className="text-muted-foreground hover:text-destructive"
                        >
                          <Trash2 className="size-4" />
                          {removingId === assignment.id ? "Removing…" : "Remove assignment"}
                        </Button>
                      </div>
                    </div>
                  </details>
                </li>
              );
            })}
          </ul>
          </>
        )}
      </div>
    </Card>
  );
};

export default AssignmentsPanel;
