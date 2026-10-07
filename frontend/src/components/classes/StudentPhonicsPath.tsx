import { useContext, useEffect, useState } from "react";
import { AuthContext } from "@/contexts/AuthContext";
import { getStudentPhonicsPath, type PhonicsPath } from "@/api";
import PhonicsPathView from "@/components/phonics/PhonicsPathView";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { getApiErrorMessage } from "@/utils/errorHandling";

const StudentPhonicsPath = ({
  classId,
  studentId,
}: {
  classId: number;
  studentId: number;
}) => {
  const { token } = useContext(AuthContext);
  const [path, setPath] = useState<PhonicsPath | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    getStudentPhonicsPath(token, classId, studentId)
      .then((data) => {
        if (!cancelled) {
          setPath(data);
          setError("");
        }
      })
      .catch((err) => {
        if (!cancelled) setError(getApiErrorMessage(err, "Couldn't load the phonics path"));
      });
    return () => {
      cancelled = true;
    };
  }, [classId, studentId, token]);

  return (
    <Card className="gap-0 rounded-2xl py-0 shadow-xs">
      <div className="p-6">
        <h2 className="text-lg font-bold text-foreground mb-4">Phonics path</h2>
        {error ? (
          <div className="text-center text-destructive py-8">{error}</div>
        ) : path ? (
          <PhonicsPathView path={path} audience="teacher" />
        ) : (
          <Skeleton className="h-40 rounded-xl" />
        )}
      </div>
    </Card>
  );
};

export default StudentPhonicsPath;
