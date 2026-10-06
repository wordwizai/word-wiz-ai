import { Button } from "@/components/ui/button";
import { GraduationCap, User } from "lucide-react";

interface ViewToggleProps {
  mode: "student" | "teacher";
  onChange: (mode: "student" | "teacher") => void;
}

// A segmented control, not two buttons: the selected side reads as raised
// rather than as a second primary action next to "Join Class".
const segment = (active: boolean) =>
  active
    ? "rounded-lg bg-background text-foreground shadow-xs hover:bg-background"
    : "rounded-lg text-muted-foreground hover:bg-background/60 hover:text-foreground";

const ViewToggle = ({ mode, onChange }: ViewToggleProps) => {
  return (
    <div className="flex items-center gap-1 rounded-xl bg-muted p-1" role="group" aria-label="View as">
      <Button
        variant="ghost"
        size="sm"
        onClick={() => onChange("student")}
        aria-pressed={mode === "student"}
        className={segment(mode === "student")}
      >
        <User />
        Student
      </Button>
      <Button
        variant="ghost"
        size="sm"
        onClick={() => onChange("teacher")}
        aria-pressed={mode === "teacher"}
        className={segment(mode === "teacher")}
      >
        <GraduationCap />
        Teacher
      </Button>
    </div>
  );
};

export default ViewToggle;
