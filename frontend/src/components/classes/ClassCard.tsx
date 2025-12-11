import { useState, useContext } from "react";
import { AuthContext } from "@/contexts/AuthContext";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Copy,
  Check,
  ChevronDown,
  ChevronUp,
  Trash2,
  LogOut,
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
import StudentList from "./StudentList";

interface ClassCardProps {
  classItem: Class | ClassWithTeacher;
  isTeacher: boolean;
  onDeleted: () => void;
  onLeft: () => void;
}

const ClassCard = ({
  classItem,
  isTeacher,
  onDeleted,
  onLeft,
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

  return (
    <Card className="rounded-xl border-2 border-white/80 shadow-sm hover:shadow-md transition-all duration-200 bg-pastel-purple">
      <div className="p-4">
        {/* Header */}
        <div className="flex items-start justify-between mb-2">
          <div className="flex-1">
            <h3 className="text-lg font-bold text-gray-800 flex items-center gap-2">
              {classItem.name}
              {isTeacher && studentCount !== undefined && (
                <span className="text-xs font-normal text-gray-600 bg-white/60 px-2 py-1 rounded-full">
                  <Users className="w-3 h-3 inline mr-1" />
                  {studentCount} {studentCount === 1 ? "student" : "students"}
                </span>
              )}
            </h3>
            {teacher && (
              <p className="text-sm text-gray-600 mt-1">
                Teacher: {teacher.full_name || teacher.email}
              </p>
            )}
          </div>
          <div className="flex items-center gap-2">
            {isTeacher ? (
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="text-red-600 hover:text-red-700 hover:bg-red-100"
                    disabled={deleting}
                  >
                    <Trash2 className="w-4 h-4" />
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
                      className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
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
                    className="text-gray-600 hover:text-gray-700 hover:bg-gray-100"
                    disabled={leaving}
                  >
                    <LogOut className="w-4 h-4" />
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
            )}
          </div>
        </div>

        {/* Join Code */}
        <div className="flex items-center gap-2 mb-3">
          <div className="flex-1 bg-white/60 p-2 rounded-lg border border-gray-200">
            <p className="text-xs text-gray-600 mb-1">Join Code</p>
            <p className="font-mono font-bold text-lg tracking-wider text-gray-800">
              {classItem.join_code}
            </p>
          </div>
          <Button
            variant="outline"
            size="icon"
            onClick={handleCopyCode}
            className="shrink-0"
          >
            {copied ? (
              <Check className="w-4 h-4 text-green-600" />
            ) : (
              <Copy className="w-4 h-4" />
            )}
          </Button>
        </div>

        {/* Expand Students Button (Teachers Only) */}
        {isTeacher && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setExpanded(!expanded)}
            className="w-full justify-between hover:bg-white/40"
          >
            <span>View Students</span>
            {expanded ? (
              <ChevronUp className="w-4 h-4" />
            ) : (
              <ChevronDown className="w-4 h-4" />
            )}
          </Button>
        )}

        {/* Student List (Expandable) */}
        {isTeacher && expanded && (
          <div className="mt-3 pt-3 border-t border-gray-200">
            <StudentList classId={classItem.id} />
          </div>
        )}
      </div>
    </Card>
  );
};

export default ClassCard;
