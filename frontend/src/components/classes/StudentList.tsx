import { useContext, useEffect, useState } from "react";
import { AuthContext } from "@/contexts/AuthContext";
import { getClassStudents, type StudentWithStats } from "@/api";
import { Skeleton } from "@/components/ui/skeleton";
import StudentCard from "./StudentCard";

interface StudentListProps {
  classId: number;
}

const StudentList = ({ classId }: StudentListProps) => {
  const { token } = useContext(AuthContext);
  const [students, setStudents] = useState<StudentWithStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchStudents();
  }, [classId, token]);

  const fetchStudents = async () => {
    if (!token) return;

    setLoading(true);
    setError("");
    try {
      const response = await getClassStudents(token, classId);
      setStudents(response.students);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to load students");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-2 py-2" aria-label="Loading students">
        <Skeleton className="h-14 w-full rounded-xl" />
        <Skeleton className="h-14 w-full rounded-xl" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center text-destructive py-4">
        {error}
      </div>
    );
  }

  if (students.length === 0) {
    return (
      <div className="py-4 text-center text-sm text-muted-foreground">
        <p>No students have joined this class yet.</p>
        <p className="mt-1">Share the join code above to get them started.</p>
      </div>
    );
  }

  return (
    <ul className="divide-y">
      {students.map((student) => (
        <li key={student.id}>
          <StudentCard student={student} />
        </li>
      ))}
    </ul>
  );
};

export default StudentList;
