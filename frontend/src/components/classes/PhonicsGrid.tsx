import { useContext, useEffect, useState } from "react";
import { AuthContext } from "@/contexts/AuthContext";
import { getClassPhonicsProgress, type ClassPhonicsProgress } from "@/api";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { unitTone } from "@/lib/phonics";
import { cn } from "@/lib/utils";

// Students down the side, units across the top. Each cell is how many of the
// unit's patterns the student has mastered. Scrolls sideways on phones.
const PhonicsGrid = ({
  classId,
  refreshKey,
}: {
  classId: number;
  refreshKey: number;
}) => {
  const { token } = useContext(AuthContext);
  const [data, setData] = useState<ClassPhonicsProgress | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    getClassPhonicsProgress(token, classId)
      .then((progress) => {
        if (!cancelled) setData(progress);
      })
      .catch((err) => {
        if (!cancelled) setError(err.response?.data?.detail || "Couldn't load the phonics path");
      });
    return () => {
      cancelled = true;
    };
  }, [classId, token, refreshKey]);

  return (
    <Card className="gap-0 rounded-2xl py-0 shadow-xs">
      <div className="p-6">
        <h2 className="text-lg font-bold text-foreground">Phonics path</h2>
        <p className="mt-1 mb-4 text-sm text-muted-foreground">
          Patterns mastered in each unit, counting practice at home too.
        </p>

        {error ? (
          <div className="py-8 text-center text-destructive">{error}</div>
        ) : !data ? (
          <Skeleton className="h-40 rounded-xl" />
        ) : data.students.length === 0 ? (
          <div className="py-8 text-center text-muted-foreground">
            No students have joined this class yet.
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="border-separate border-spacing-1 text-sm">
                <thead>
                  <tr>
                    <th
                      scope="col"
                      className="sticky left-0 z-10 bg-card px-2 py-1 text-left text-xs font-medium text-muted-foreground"
                    >
                      Student
                    </th>
                    {data.units.map((unit, i) => (
                      <th
                        key={unit.id}
                        scope="col"
                        className="min-w-12 px-1 py-1 text-center text-xs font-medium text-muted-foreground"
                      >
                        <abbr title={unit.title} className="no-underline">
                          {i + 1}
                        </abbr>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {data.students.map((student) => (
                    <tr key={student.id}>
                      <th
                        scope="row"
                        className="sticky left-0 z-10 max-w-40 truncate bg-card px-2 py-1 text-left font-medium text-foreground"
                      >
                        {student.full_name || "Student"}
                      </th>
                      {data.units.map((unit) => {
                        const mastered = unit.patterns.filter(
                          (p) => student.statuses[p.slug] === "mastered"
                        ).length;
                        return (
                          <td
                            key={unit.id}
                            title={`${unit.title}: ${mastered} of ${unit.patterns.length} mastered`}
                            className={cn(
                              "rounded-lg px-1 py-2 text-center text-xs font-medium tabular-nums",
                              unitTone(mastered, unit.patterns.length)
                            )}
                          >
                            {mastered}/{unit.patterns.length}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <ol className="mt-4 grid grid-cols-1 gap-x-6 gap-y-1 text-xs text-muted-foreground sm:grid-cols-2 lg:grid-cols-3">
              {data.units.map((unit, i) => (
                <li key={unit.id}>
                  {i + 1}. {unit.title}
                </li>
              ))}
            </ol>
          </>
        )}
      </div>
    </Card>
  );
};

export default PhonicsGrid;
