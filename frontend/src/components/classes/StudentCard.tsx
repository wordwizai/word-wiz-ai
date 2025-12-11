import { type StudentWithStats } from "@/api";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { BookOpen, Target, Flame, Calendar } from "lucide-react";

interface StudentCardProps {
  student: StudentWithStats;
}

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

  const getPerformanceColor = (per: number) => {
    if (per < 0.1) return "text-green-600 bg-green-100";
    if (per < 0.2) return "text-yellow-600 bg-yellow-100";
    return "text-orange-600 bg-orange-100";
  };

  return (
    <Card className="p-3 bg-white/80 border border-gray-200 hover:bg-white/90 transition-colors">
      <div className="space-y-2">
        {/* Student Info */}
        <div>
          <h4 className="font-semibold text-gray-800">
            {student.full_name || "Student"}
          </h4>
          <p className="text-xs text-gray-600">{student.email}</p>
        </div>

        {/* Statistics */}
        <div className="grid grid-cols-2 gap-2">
          {/* Sessions */}
          <div className="flex items-center gap-2 text-xs">
            <Target className="w-3 h-3 text-blue-600" />
            <span className="font-medium">
              {student.statistics.total_sessions}
            </span>
            <span className="text-gray-600">sessions</span>
          </div>

          {/* Words Read */}
          <div className="flex items-center gap-2 text-xs">
            <BookOpen className="w-3 h-3 text-green-600" />
            <span className="font-medium">{student.statistics.words_read}</span>
            <span className="text-gray-600">words</span>
          </div>

          {/* Streak */}
          <div className="flex items-center gap-2 text-xs">
            <Flame className="w-3 h-3 text-orange-600" />
            <span className="font-medium">
              {student.statistics.current_streak}
            </span>
            <span className="text-gray-600">day streak</span>
          </div>

          {/* Last Activity */}
          <div className="flex items-center gap-2 text-xs">
            <Calendar className="w-3 h-3 text-purple-600" />
            <span className="text-gray-600">
              {formatDate(student.statistics.last_session_date)}
            </span>
          </div>
        </div>

        {/* Performance Badge */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-600">Avg. Accuracy:</span>
          <Badge
            variant="secondary"
            className={`text-xs ${getPerformanceColor(
              student.statistics.average_per
            )}`}
          >
            {student.statistics.average_per > 0
              ? `${(
                  (1 - student.statistics.average_per) *
                  100
                ).toFixed(1)}%`
              : "N/A"}
          </Badge>
        </div>
      </div>
    </Card>
  );
};

export default StudentCard;
