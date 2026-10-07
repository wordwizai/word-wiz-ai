import { Check } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  STATUS_LABEL,
  STATUS_TONE,
  STUDENT_LABEL,
  type PatternStatus,
} from "@/lib/phonics";

// Teachers see the plain status. Children (and the parents beside them) see
// gentler words, so nothing on their screens says "Needs practice".
const PatternStatusChip = ({
  status,
  audience,
  className,
}: {
  status: PatternStatus;
  audience: "student" | "teacher";
  className?: string;
}) => (
  <span
    className={cn(
      "inline-flex items-center gap-1 whitespace-nowrap rounded-full px-2.5 py-0.5 text-xs font-medium",
      STATUS_TONE[status],
      className
    )}
  >
    {status === "mastered" && <Check className="size-3" aria-hidden />}
    {(audience === "student" ? STUDENT_LABEL : STATUS_LABEL)[status]}
  </span>
);

export default PatternStatusChip;
