import { useContext, useEffect, useState } from "react";
import { AuthContext } from "@/contexts/AuthContext";
import {
  assignPatterns,
  getCurriculum,
  type Curriculum,
  type CurriculumUnit,
  type StudentWithStats,
} from "@/api";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { assignSummary } from "@/lib/phonics";
import { getApiErrorMessage } from "@/utils/errorHandling";

interface AssignPracticeDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  classId: number;
  students: StudentWithStats[];
  onAssigned: () => void;
}

const AssignPracticeDialog = ({
  open,
  onOpenChange,
  classId,
  students,
  onAssigned,
}: AssignPracticeDialogProps) => {
  const { token } = useContext(AuthContext);
  const [curriculum, setCurriculum] = useState<Curriculum | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [wholeClass, setWholeClass] = useState(true);
  const [chosen, setChosen] = useState<Set<number>>(new Set());
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!open || !token || curriculum) return;
    getCurriculum(token)
      .then(setCurriculum)
      .catch(() => setError("Couldn't load the units. Please try again."));
  }, [open, token, curriculum]);

  const reset = () => {
    setSelected(new Set());
    setWholeClass(true);
    setChosen(new Set());
    setError("");
  };

  const handleOpenChange = (next: boolean) => {
    if (!next) reset();
    onOpenChange(next);
  };

  const toggleUnit = (unit: CurriculumUnit) => {
    const all = unit.patterns.every((p) => selected.has(p.slug));
    const next = new Set(selected);
    unit.patterns.forEach((p) => (all ? next.delete(p.slug) : next.add(p.slug)));
    setSelected(next);
  };

  const toggle = <T,>(set: Set<T>, value: T, update: (next: Set<T>) => void) => {
    const next = new Set(set);
    if (next.has(value)) next.delete(value);
    else next.add(value);
    update(next);
  };

  const studentCount = wholeClass ? students.length : chosen.size;
  const canAssign = selected.size > 0 && studentCount > 0 && !saving;

  const handleAssign = async () => {
    if (!curriculum) return;
    setSaving(true);
    setError("");
    try {
      // Curriculum order, so the class's list reads in teaching order.
      const slugs = curriculum.units
        .flatMap((unit) => unit.patterns.map((p) => p.slug))
        .filter((slug) => selected.has(slug));
      await assignPatterns(token ?? "", classId, slugs, wholeClass ? null : [...chosen]);
      reset();
      onAssigned();
      onOpenChange(false);
    } catch (err) {
      setError(getApiErrorMessage(err, "Couldn't assign that. Please try again."));
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="flex max-h-[90dvh] flex-col sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Assign practice</DialogTitle>
          <DialogDescription>
            Pick whole units or single patterns. Each pattern is one short
            session of words and sentences for your students to read.
          </DialogDescription>
        </DialogHeader>

        <div className="min-h-0 flex-1 space-y-6 overflow-y-auto pr-1">
          <fieldset className="space-y-2">
            <legend className="mb-2 text-sm font-semibold text-foreground">Patterns</legend>
            {!curriculum ? (
              Array.from({ length: 5 }, (_, i) => (
                <Skeleton key={i} className="h-11 rounded-xl" />
              ))
            ) : (
              curriculum.units.map((unit, i) => {
                const count = unit.patterns.filter((p) => selected.has(p.slug)).length;
                return (
                  <details key={unit.id} className="rounded-xl border">
                    <summary className="flex min-h-11 cursor-pointer list-none items-center gap-3 px-3 py-2 [&::-webkit-details-marker]:hidden">
                      <input
                        type="checkbox"
                        checked={count === unit.patterns.length}
                        ref={(el) => {
                          if (el) el.indeterminate = count > 0 && count < unit.patterns.length;
                        }}
                        onChange={() => toggleUnit(unit)}
                        aria-label={`All of ${unit.title}`}
                        className="size-4 accent-primary"
                      />
                      <span className="flex-1 text-sm font-medium text-foreground">
                        {i + 1}. {unit.title}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {count > 0 ? `${count} of ${unit.patterns.length}` : unit.grade}
                      </span>
                    </summary>
                    <div className="grid grid-cols-1 gap-1 px-3 pb-3 sm:grid-cols-2">
                      {unit.patterns.map((pattern) => (
                        <label
                          key={pattern.slug}
                          className="flex min-h-9 items-center gap-2 rounded-lg px-2 text-sm hover:bg-muted"
                        >
                          <input
                            type="checkbox"
                            checked={selected.has(pattern.slug)}
                            onChange={() => toggle(selected, pattern.slug, setSelected)}
                            className="size-4 accent-primary"
                          />
                          {pattern.name}
                        </label>
                      ))}
                    </div>
                  </details>
                );
              })
            )}
          </fieldset>

          <fieldset className="space-y-2">
            <legend className="mb-2 text-sm font-semibold text-foreground">Students</legend>
            <label className="flex min-h-9 items-center gap-2 text-sm">
              <input
                type="radio"
                name="assign-to"
                checked={wholeClass}
                onChange={() => setWholeClass(true)}
                className="size-4 accent-primary"
              />
              Whole class ({students.length}), including students who join later
            </label>
            <label className="flex min-h-9 items-center gap-2 text-sm">
              <input
                type="radio"
                name="assign-to"
                checked={!wholeClass}
                onChange={() => setWholeClass(false)}
                className="size-4 accent-primary"
              />
              Chosen students
            </label>
            {!wholeClass && (
              <div className="grid grid-cols-1 gap-1 rounded-xl border p-3 sm:grid-cols-2">
                {students.map((student) => (
                  <label
                    key={student.id}
                    className="flex min-h-9 items-center gap-2 rounded-lg px-2 text-sm hover:bg-muted"
                  >
                    <input
                      type="checkbox"
                      checked={chosen.has(student.id)}
                      onChange={() => toggle(chosen, student.id, setChosen)}
                      className="size-4 accent-primary"
                    />
                    {student.full_name || student.email}
                  </label>
                ))}
              </div>
            )}
          </fieldset>
        </div>

        {students.length === 0 && (
          <p className="text-sm text-muted-foreground">
            No students have joined yet. Share your join code first.
          </p>
        )}
        {error && <p className="text-sm text-destructive">{error}</p>}

        <DialogFooter className="items-center gap-3 sm:justify-between">
          <p className="text-sm text-muted-foreground">
            {assignSummary(selected.size, studentCount)}
          </p>
          <Button onClick={handleAssign} disabled={!canAssign} className="rounded-xl">
            {saving ? "Assigning..." : "Assign"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default AssignPracticeDialog;
