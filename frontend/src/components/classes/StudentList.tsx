import { useContext, useEffect, useState } from "react";
import { AuthContext } from "@/contexts/AuthContext";
import { getClassStudents, type StudentWithStats } from "@/api";
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
      <div className="text-center text-gray-600 py-4">
        Loading students...
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
      <div className="text-center text-gray-600 py-4">
        <p>No students have joined this class yet.</p>
        <p className="text-sm mt-2">
          Share the join code with students to get started!
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {students.map((student) => (
        <StudentCard key={student.id} student={student} />
      ))}
    </div>
  );
};

export default StudentList;
