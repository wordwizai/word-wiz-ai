import { useContext, useEffect, useState } from "react";
import { AuthContext } from "@/contexts/AuthContext";
import {
  getStudentInsights,
  type StudentWithStats,
  type StudentInsights,
} from "@/api";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import SessionHistoryList from "./SessionHistoryList";
import PhonemeInsightsCard from "./PhonemeInsightsCard";
import RecommendationsCard from "./RecommendationsCard";
import {
  ArrowLeft,
  BookOpen,
  Target,
  Flame,
  Calendar,
  TrendingUp,
  User,
} from "lucide-react";

interface StudentDetailViewProps {
  student: StudentWithStats;
  classId: number;
  onBack: () => void;
}

const StudentDetailView = ({
  student,
  classId,
  onBack,
}: StudentDetailViewProps) => {
  const { token } = useContext(AuthContext);
  const [insights, setInsights] = useState<StudentInsights | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchInsights();
  }, [student.id, classId, token]);

  const fetchInsights = async () => {
    if (!token) return;

    setLoading(true);
    setError("");
    try {
      const data = await getStudentInsights(token, classId, student.id);
      setInsights(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to load insights");
      console.error("Error fetching insights:", err);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return "Never";
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      month: "long",
      day: "numeric",
      year: "numeric",
    });
  };

  const getAccuracyColor = (per: number) => {
    if (per < 0.1) return "text-green-600";
    if (per < 0.2) return "text-yellow-600";
    return "text-orange-600";
  };

  const getStreakMessage = (streak: number) => {
    if (streak === 0) return "Start practicing to build a streak!";
    if (streak === 1) return "Great start! Keep it up!";
    if (streak < 7) return "You're building momentum!";
    if (streak < 30) return "Excellent consistency!";
    return "Amazing dedication!";
  };

  // Get initials for avatar
  const getInitials = (name: string | null, email: string) => {
    if (name) {
      const parts = name.split(" ");
      if (parts.length >= 2) {
        return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
      }
      return name.substring(0, 2).toUpperCase();
    }
    return email.substring(0, 2).toUpperCase();
  };

  // Use insights.recent_accuracy if available, fallback to student.statistics
  const accuracy = insights
    ? insights.recent_accuracy.toFixed(1)
    : student.statistics.average_per > 0
    ? ((1 - student.statistics.average_per) * 100).toFixed(1)
    : "N/A";

  const accuracyNumber = insights
    ? insights.recent_accuracy
    : student.statistics.average_per > 0
    ? (1 - student.statistics.average_per) * 100
    : 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card className="rounded-2xl bg-card border-2 border-border shadow-md">
        <div className="p-6">
          <Button
            variant="ghost"
            size="sm"
            onClick={onBack}
            className="mb-4 -ml-2"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Class
          </Button>

          {/* Student Profile */}
          <div className="flex items-start gap-4">
            {/* Avatar */}
            <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
              <span className="text-2xl font-bold text-primary">
                {getInitials(student.full_name, student.email)}
              </span>
            </div>

            {/* Info */}
            <div className="flex-1">
              <h1 className="text-2xl font-bold text-foreground">
                {student.full_name || "Student"}
              </h1>
              <p className="text-sm text-muted-foreground">{student.email}</p>
              <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
                <div className="flex items-center gap-1">
                  <Calendar className="w-4 h-4" />
                  <span>Joined {formatDate(student.joined_at)}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* Performance Overview */}
      <Card className="rounded-2xl bg-card border-2 border-border shadow-md">
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold text-foreground">
              Performance Overview
            </h2>
            {insights && (
              <span className="text-xs text-muted-foreground">
                {insights.calculation_window}
              </span>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Total Sessions */}
            <div className="bg-muted rounded-lg p-4">
              <div className="flex items-center gap-2 text-muted-foreground mb-2">
                <Target className="w-5 h-5" />
                <span className="text-sm font-medium">Total Sessions</span>
              </div>
              <p className="text-3xl font-bold text-foreground">
                {student.statistics.total_sessions}
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                Practice sessions completed
              </p>
            </div>

            {/* Words Read */}
            <div className="bg-muted rounded-lg p-4">
              <div className="flex items-center gap-2 text-muted-foreground mb-2">
                <BookOpen className="w-5 h-5" />
                <span className="text-sm font-medium">Words Read</span>
              </div>
              <p className="text-3xl font-bold text-foreground">
                {student.statistics.words_read}
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                Total words practiced
              </p>
            </div>

            {/* Accuracy */}
            <div className="bg-muted rounded-lg p-4">
              <div className="flex items-center gap-2 text-muted-foreground mb-2">
                <TrendingUp className="w-5 h-5" />
                <span className="text-sm font-medium">Recent Accuracy</span>
              </div>
              <p
                className={`text-3xl font-bold ${getAccuracyColor(
                  accuracyNumber / 100
                )}`}
              >
                {accuracy !== "N/A" ? `${accuracy}%` : accuracy}
              </p>
              {accuracy !== "N/A" && (
                <div className="mt-2">
                  <Progress value={parseFloat(accuracy)} className="h-2" />
                </div>
              )}
              <p className="text-xs text-muted-foreground mt-1">
                {accuracyNumber >= 90
                  ? "Excellent accuracy!"
                  : accuracyNumber >= 80
                  ? "Good progress"
                  : "Room for improvement"}
              </p>
            </div>

            {/* Current Streak */}
            <div className="bg-muted rounded-lg p-4">
              <div className="flex items-center gap-2 text-muted-foreground mb-2">
                <Flame className="w-5 h-5 text-orange-500" />
                <span className="text-sm font-medium">Current Streak</span>
              </div>
              <p className="text-3xl font-bold text-foreground">
                {student.statistics.current_streak}
                <span className="text-xl text-muted-foreground ml-2">days</span>
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                {getStreakMessage(student.statistics.current_streak)}
              </p>
            </div>
          </div>
        </div>
      </Card>

      {/* Recent Activity */}
      <Card className="rounded-2xl bg-card border-2 border-border shadow-md">
        <div className="p-6">
          <h2 className="text-lg font-bold text-foreground mb-4">
            Recent Activity
          </h2>

          {loading ? (
            <div className="text-center text-muted-foreground py-8">
              Loading session history...
            </div>
          ) : error ? (
            <div className="text-center text-destructive py-8">{error}</div>
          ) : insights ? (
            <SessionHistoryList
              sessions={insights.recent_sessions}
              calculationWindow={insights.calculation_window}
            />
          ) : (
            <div className="text-center text-muted-foreground py-8">
              <User className="w-12 h-12 mx-auto mb-2 opacity-50" />
              <p>No recent activity data available</p>
            </div>
          )}
        </div>
      </Card>

      {/* Problem Areas */}
      <Card className="rounded-2xl bg-card border-2 border-border shadow-md">
        <div className="p-6">
          <h2 className="text-lg font-bold text-foreground mb-4">
            Problem Areas
          </h2>
          {loading ? (
            <div className="text-center text-muted-foreground py-8">
              Analyzing phoneme errors...
            </div>
          ) : insights ? (
            <PhonemeInsightsCard insights={insights.phoneme_insights} />
          ) : (
            <div className="text-center text-muted-foreground py-8">
              No data available
            </div>
          )}
        </div>
      </Card>

      {/* Teaching Recommendations */}
      <Card className="rounded-2xl bg-card border-2 border-border shadow-md">
        <div className="p-6">
          <h2 className="text-lg font-bold text-foreground mb-4">
            Teaching Recommendations
          </h2>
          {loading ? (
            <div className="text-center text-muted-foreground py-8">
              Generating recommendations...
            </div>
          ) : insights ? (
            <RecommendationsCard recommendations={insights.recommendations} />
          ) : (
            <div className="text-center text-muted-foreground py-8">
              No recommendations available
            </div>
          )}
        </div>
      </Card>
    </div>
  );
};

export default StudentDetailView;
