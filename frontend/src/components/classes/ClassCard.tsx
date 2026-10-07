import { useState, useContext } from "react";
import { AuthContext } from "@/contexts/AuthContext";
import { Button, buttonVariants } from "@/components/ui/button";
import {
  ArrowRight,
  Check,
  ChevronDown,
  Copy,
  LogOut,
  Trash2,
  Users,
} from "lucide-react";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { deleteClass, leaveClass, type Class, type ClassWithTeacher } from "@/api";
import { activityPastel } from "@/lib/activities";
import { cn } from "@/lib/utils";
import StudentList from "./StudentList";

interface ClassCardProps {
  classItem: Class | ClassWithTeacher;
  isTeacher: boolean;
  viewMode: "student" | "teacher";
  onDeleted: () => void;
  onLeft: () => void;
  onViewDetails?: (classItem: Class) => void;
}

const ClassCard = ({
  classItem,
  isTeacher,
  viewMode,
  onDeleted,
  onLeft,
  onViewDetails,
}: ClassCardProps) => {
  const { token } = useContext(AuthContext);
  const [copied, setCopied] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [leaving, setLeaving] = useState(false);

  const handleCopyCode = () => {
    navigator.clipboard.writeText(classItem.join_code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDelete = async () => {
    if (!token) return;
    setDeleting(true);
    try {
      await deleteClass(token, classItem.id);
      onDeleted();
    } catch (error) {
      console.error("Error deleting class:", error);
      alert("Failed to delete class");
    } finally {
      setDeleting(false);
    }
  };

  const handleLeave = async () => {
    if (!token) return;
    setLeaving(true);
    try {
      await leaveClass(token, classItem.id);
      onLeft();
    } catch (error) {
      console.error("Error leaving class:", error);
      alert("Failed to leave class");
    } finally {
      setLeaving(false);
    }
  };

  const studentCount = "student_count" in classItem ? classItem.student_count : undefined;
  const teacher = "teacher" in classItem ? classItem.teacher : null;
  const showTeacherTools = isTeacher && viewMode === "teacher";
  // Same id-to-pastel rule as activities, so a class keeps its colour.
  const pastel = activityPastel(classItem.id);

  return (
    <article className="flex flex-col rounded-2xl border bg-card p-5 shadow-xs">
      {/* Header */}
      <div className="flex items-start gap-4">
        <span
          className="flex size-10 shrink-0 items-center justify-center rounded-xl"
          style={{ backgroundColor: pastel.background, color: pastel.foreground }}
        >
          <Users className="size-5" />
        </span>
        <div className="min-w-0 flex-1">
          <h3 className="text-lg font-semibold leading-snug break-words text-foreground">
            {classItem.name}
          </h3>
          {teacher && (
            <p className="truncate text-sm text-muted-foreground">
              Taught by {teacher.full_name || teacher.email}
            </p>
          )}
          {showTeacherTools && studentCount !== undefined && (
            <p className="text-sm text-muted-foreground">
              {studentCount} {studentCount === 1 ? "student" : "students"}
            </p>
          )}
        </div>

        {/* Only show delete/leave actions in teacher view */}
        {viewMode === "teacher" &&
          (isTeacher ? (
            <AlertDialog>
              <AlertDialogTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="-mt-1 -mr-2 text-muted-foreground hover:bg-destructive/10 hover:text-destructive dark:hover:bg-destructive/20"
                  disabled={deleting}
                  aria-label={`Delete ${classItem.name}`}
                >
                  <Trash2 />
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>Delete Class</AlertDialogTitle>
                  <AlertDialogDescription>
                    Are you sure you want to delete "{classItem.name}"? This
                    will remove all students from the class. This action
                    cannot be undone.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                  <AlertDialogAction
                    onClick={handleDelete}
                    className={buttonVariants({ variant: "destructive" })}
                  >
                    Delete
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          ) : (
            <AlertDialog>
              <AlertDialogTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="-mt-1 -mr-2 text-muted-foreground hover:text-foreground"
                  disabled={leaving}
                  aria-label={`Leave ${classItem.name}`}
                >
                  <LogOut />
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>Leave Class</AlertDialogTitle>
                  <AlertDialogDescription>
                    Are you sure you want to leave "{classItem.name}"? You can
                    rejoin later using the join code.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                  <AlertDialogAction onClick={handleLeave}>
                    Leave
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          ))}
      </div>

      {/* Join Code - Only show in teacher view */}
      {viewMode === "teacher" && (
        <div className="mt-4 flex items-center justify-between gap-3 rounded-xl bg-muted py-2 pr-2 pl-4">
          <div className="min-w-0">
            <p className="text-xs font-medium text-muted-foreground">Join code</p>
            <p className="font-mono text-lg font-semibold tracking-widest text-foreground">
              {classItem.join_code}
            </p>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={handleCopyCode}
            aria-label={copied ? "Join code copied" : "Copy join code"}
            className="shrink-0 hover:bg-background dark:hover:bg-background"
          >
            {copied ? <Check className="text-primary" /> : <Copy />}
          </Button>
        </div>
      )}

      {/* Open the class, or peek at its students in place */}
      {showTeacherTools && (
        <div className="mt-4 flex flex-col gap-2">
          <Button
            onClick={() => onViewDetails && onViewDetails(classItem as Class)}
            className="w-full rounded-xl"
          >
            View class
            <ArrowRight />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setExpanded(!expanded)}
            aria-expanded={expanded}
            className="w-full justify-between rounded-xl text-muted-foreground hover:text-foreground"
          >
            Quick view students
            <ChevronDown
              className={cn(
                "transition-transform duration-200",
                expanded && "rotate-180"
              )}
            />
          </Button>
        </div>
      )}

      {/* Student List (Expandable - Teacher View Only) */}
      {showTeacherTools && expanded && (
        <div className="mt-2 border-t pt-1">
          <StudentList classId={classItem.id} />
        </div>
      )}
    </article>
  );
};

export default ClassCard;
