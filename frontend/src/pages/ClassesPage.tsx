import { useContext, useEffect, useState } from "react";
import { AuthContext } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Plus } from "lucide-react";
import { AppPage, PageHeader, SectionHeader } from "@/components/AppPage";
import {
  getMyClasses,
  getMyStudentClasses,
  type Class,
  type ClassWithTeacher,
  type StudentWithStats,
} from "@/api";
import CreateClassDialog from "@/components/classes/CreateClassDialog";
import JoinClassDialog from "@/components/classes/JoinClassDialog";
import ClassCard from "@/components/classes/ClassCard";
import ViewToggle from "@/components/classes/ViewToggle";
import ClassDetailView from "@/components/classes/ClassDetailView";
import StudentDetailView from "@/components/classes/StudentDetailView";

type ViewMode = "student" | "teacher";

const ClassesPage = () => {
  const { token } = useContext(AuthContext);
  const [myClasses, setMyClasses] = useState<Class[]>([]);
  const [studentClasses, setStudentClasses] = useState<ClassWithTeacher[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showJoinDialog, setShowJoinDialog] = useState(false);

  // View mode state - defaults to student view
  const [viewMode, setViewMode] = useState<ViewMode>(() => {
    const savedMode = localStorage.getItem("classesViewMode");
    return (savedMode as ViewMode) || "student";
  });

  // Detail view state
  const [selectedClassId, setSelectedClassId] = useState<number | null>(null);
  const [selectedClassName, setSelectedClassName] = useState<string>("");
  const [selectedJoinCode, setSelectedJoinCode] = useState<string>("");

  // Student detail view state
  const [selectedStudent, setSelectedStudent] =
    useState<StudentWithStats | null>(null);

  useEffect(() => {
    fetchClasses();
  }, [token]);

  const fetchClasses = async () => {
    if (!token) return;

    setLoading(true);
    try {
      const [teacherClasses, enrolledClasses] = await Promise.all([
        getMyClasses(token),
        getMyStudentClasses(token),
      ]);
      setMyClasses(teacherClasses);
      setStudentClasses(enrolledClasses);
    } catch (error) {
      console.error("Error fetching classes:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleClassCreated = () => {
    setShowCreateDialog(false);
    fetchClasses();
  };

  const handleClassJoined = () => {
    setShowJoinDialog(false);
    fetchClasses();
  };

  const handleClassDeleted = () => {
    fetchClasses();
  };

  const handleClassLeft = () => {
    fetchClasses();
  };

  const handleViewChange = (mode: ViewMode) => {
    setViewMode(mode);
    localStorage.setItem("classesViewMode", mode);
  };

  const handleViewClassDetails = (classItem: Class) => {
    setSelectedClassId(classItem.id);
    setSelectedClassName(classItem.name);
    setSelectedJoinCode(classItem.join_code);
  };

  const handleBackToList = () => {
    setSelectedClassId(null);
    setSelectedClassName("");
    setSelectedJoinCode("");
    setSelectedStudent(null);
  };

  const handleViewStudent = (student: StudentWithStats) => {
    setSelectedStudent(student);
  };

  const handleBackToClassDetail = () => {
    setSelectedStudent(null);
  };

  const visibleClasses: (Class | ClassWithTeacher)[] =
    viewMode === "student" ? studentClasses : myClasses;

  // If viewing student details, show student detail view
  if (selectedStudent !== null && selectedClassId !== null) {
    return (
      <AppPage>
        <StudentDetailView
          student={selectedStudent}
          classId={selectedClassId}
          onBack={handleBackToClassDetail}
        />
      </AppPage>
    );
  }

  // If viewing class details, show detail view
  if (selectedClassId !== null) {
    return (
      <AppPage>
        <ClassDetailView
          classId={selectedClassId}
          className={selectedClassName}
          joinCode={selectedJoinCode}
          onBack={handleBackToList}
          onViewStudent={handleViewStudent}
        />
      </AppPage>
    );
  }

  return (
    <AppPage>
      <PageHeader
        title="Classes"
        description={
          viewMode === "student"
            ? "Classes you've joined with a teacher's code."
            : "Classes you teach, and how each student is reading."
        }
        actions={<ViewToggle mode={viewMode} onChange={handleViewChange} />}
      />

      <section aria-labelledby="classes-heading">
        <SectionHeader
          id="classes-heading"
          title={viewMode === "student" ? "My classes" : "Classes I teach"}
          action={
            viewMode === "student" ? (
              <Button
                onClick={() => setShowJoinDialog(true)}
                size="sm"
                className="rounded-xl"
              >
                <Plus />
                Join class
              </Button>
            ) : (
              <Button
                onClick={() => setShowCreateDialog(true)}
                size="sm"
                className="rounded-xl"
              >
                <Plus />
                Create class
              </Button>
            )
          }
        />

        {loading ? (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 3 }, (_, i) => (
              <Skeleton key={i} className="h-28 rounded-2xl" />
            ))}
          </div>
        ) : visibleClasses.length > 0 ? (
          <div className="grid grid-cols-1 items-start gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {visibleClasses.map((classItem) => (
              <ClassCard
                key={classItem.id}
                classItem={classItem}
                isTeacher={viewMode === "teacher"}
                viewMode={viewMode}
                onDeleted={handleClassDeleted}
                onLeft={handleClassLeft}
                onViewDetails={
                  viewMode === "teacher" ? handleViewClassDetails : undefined
                }
              />
            ))}
          </div>
        ) : (
          <div className="rounded-2xl border border-dashed px-6 py-10 text-center">
            {viewMode === "student" ? (
              <>
                <p className="font-medium text-foreground">
                  You haven't joined a class yet
                </p>
                <p className="mt-1 text-sm text-muted-foreground">
                  If a teacher gave you a join code, choose Join class to
                  enter it.
                </p>
              </>
            ) : (
              <>
                <p className="font-medium text-foreground">
                  You haven't created a class yet
                </p>
                <p className="mt-1 text-sm text-muted-foreground">
                  Create one to get a join code you can share with students.
                </p>
              </>
            )}
          </div>
        )}
      </section>

      {/* Dialogs */}
      <CreateClassDialog
        open={showCreateDialog}
        onOpenChange={setShowCreateDialog}
        onCreated={handleClassCreated}
      />
      <JoinClassDialog
        open={showJoinDialog}
        onOpenChange={setShowJoinDialog}
        onJoined={handleClassJoined}
        showAsCard={false}
      />
    </AppPage>
  );
};

export default ClassesPage;
