import { useContext, useEffect, useState } from "react";
import { AuthContext } from "@/contexts/AuthContext";
import { getPhonemesPerMistakeType } from "@/api";
import { Skeleton } from "./ui/skeleton";

type ErrorType = "substitution" | "insertion" | "deletion";

// Plain-language names for the three error kinds, written for parents.
const COPY: Record<ErrorType, { title: string; description: string }> = {
  substitution: {
    title: "Swapped",
    description: "Read as a different sound",
  },
  deletion: {
    title: "Left out",
    description: "Skipped inside a word",
  },
  insertion: {
    title: "Added",
    description: "Said but not in the word",
  },
};

const TOP_N = 5;

// A ranked bar list instead of a pie: counts across a handful of sounds are
// compared by length far more easily than by slice angle, and the sound
// itself stays readable as text.
const SoundErrorsCard = ({ errorType }: { errorType: ErrorType }) => {
  const { token } = useContext(AuthContext);
  const [rows, setRows] = useState<{ phoneme: string; count: number }[] | null>(
    null
  );

  useEffect(() => {
    if (!token) return;
    getPhonemesPerMistakeType(token, errorType)
      .then((res: Record<string, number>) =>
        setRows(
          Object.entries(res)
            .map(([phoneme, count]) => ({ phoneme, count }))
            .sort((a, b) => b.count - a.count)
            .slice(0, TOP_N)
        )
      )
      .catch((error: unknown) => {
        console.error("Error fetching phoneme errors:", error);
        setRows([]);
      });
  }, [errorType, token]);

  const max = Math.max(1, ...(rows ?? []).map((r) => r.count));
  const { title, description } = COPY[errorType];

  return (
    <div className="flex flex-col rounded-2xl border bg-card p-5 shadow-xs">
      <h3 className="font-semibold text-foreground">{title}</h3>
      <p className="text-sm text-muted-foreground">{description}</p>

      <div className="mt-4 flex-1">
        {rows === null ? (
          <div className="space-y-3">
            {Array.from({ length: 3 }, (_, i) => (
              <Skeleton key={i} className="h-7 w-full" />
            ))}
          </div>
        ) : rows.length === 0 ? (
          <p className="py-6 text-center text-sm text-muted-foreground">
            None in recent readings
          </p>
        ) : (
          <ol className="space-y-2.5">
            {rows.map((row) => (
              <li
                key={row.phoneme}
                className="grid grid-cols-[3.25rem_1fr_2rem] items-center gap-3"
              >
                <span className="font-ipa text-lg leading-none text-foreground">
                  /{row.phoneme}/
                </span>
                <span
                  className="h-2 rounded-full bg-primary"
                  style={{ width: `${Math.max(6, (row.count / max) * 100)}%` }}
                  aria-hidden
                />
                <span className="text-right text-sm text-muted-foreground tabular-nums">
                  {row.count}
                </span>
              </li>
            ))}
          </ol>
        )}
      </div>
    </div>
  );
};

export default SoundErrorsCard;
