import { Button } from "@/components/ui/button";
import { GraduationCap, User } from "lucide-react";

interface ViewToggleProps {
  mode: "student" | "teacher";
  onChange: (mode: "student" | "teacher") => void;
}

const ViewToggle = ({ mode, onChange }: ViewToggleProps) => {
  return (
    <div className="flex items-center gap-2 p-1 bg-muted rounded-lg">
      <Button
        variant={mode === "student" ? "default" : "ghost"}
        size="sm"
        onClick={() => onChange("student")}
        className={mode === "student" ? "" : "hover:bg-background"}
      >
        <User className="w-4 h-4 mr-2" />
        Student View
      </Button>
      <Button
        variant={mode === "teacher" ? "default" : "ghost"}
        size="sm"
        onClick={() => onChange("teacher")}
        className={mode === "teacher" ? "" : "hover:bg-background"}
      >
        <GraduationCap className="w-4 h-4 mr-2" />
        Teacher View
      </Button>
    </div>
  );
};

export default ViewToggle;
