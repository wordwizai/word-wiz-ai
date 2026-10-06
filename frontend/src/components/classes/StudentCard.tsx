import { type StudentWithStats } from "@/api";
import { cn } from "@/lib/utils";
import { ACCURACY_TONE, perAccuracyLabel, perTone } from "./accuracy";

interface StudentCardProps {
  student: StudentWithStats;
}

// One row in a class's quick view: who the student is, how much they've
// read, and their average accuracy on the right where it's easy to scan.
const StudentCard = ({ student }: StudentCardProps) => {
  const formatDate = (dateString: string | null) => {
    if (!dateString) return "Never";
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  const { total_sessions, words_read, current_streak, last_session_date, average_per } =
    student.statistics;

  return (
    <div className="flex items-start justify-between gap-3 py-3">
      <div className="min-w-0">
        <p className="truncate font-medium text-foreground">
          {student.full_name || "Student"}
        </p>
        <p className="truncate text-xs text-muted-foreground">{student.email}</p>
        <p className="mt-1.5 text-xs text-muted-foreground">
          {total_sessions} {total_sessions === 1 ? "session" : "sessions"} ·{" "}
          {words_read} words
          {current_streak > 0 && ` · ${current_streak}-day streak`}
        </p>
        <p className="text-xs text-muted-foreground">
          Last read {formatDate(last_session_date)}
        </p>
      </div>
      <span
        className={cn(
          "shrink-0 rounded-full px-2.5 py-0.5 text-xs font-medium tabular-nums",
          ACCURACY_TONE[perTone(average_per)]
        )}
        title="Average accuracy"
      >
        <span className="sr-only">Average accuracy </span>
        {perAccuracyLabel(average_per)}
      </span>
    </div>
  );
};

export default StudentCard;
