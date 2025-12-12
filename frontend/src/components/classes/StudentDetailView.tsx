import { type StudentWithStats } from "@/api";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
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
  onBack: () => void;
}

const StudentDetailView = ({ student, onBack }: StudentDetailViewProps) => {
  const formatDate = (dateString: string | null) => {
    if (!dateString) return "Never";
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      month: "long",
      day: "numeric",
      year: "numeric",
    });
  };

  const accuracy = student.statistics.average_per > 0
    ? ((1 - student.statistics.average_per) * 100).toFixed(1)
    : "N/A";

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
          <h2 className="text-lg font-bold text-foreground mb-4">
            Performance Overview
          </h2>

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
                <span className="text-sm font-medium">Average Accuracy</span>
              </div>
              <p
                className={`text-3xl font-bold ${getAccuracyColor(
                  student.statistics.average_per
                )}`}
              >
                {accuracy !== "N/A" ? `${accuracy}%` : accuracy}
              </p>
              {accuracy !== "N/A" && (
                <div className="mt-2">
                  <Progress
                    value={parseFloat(accuracy)}
                    className="h-2"
                  />
                </div>
              )}
              <p className="text-xs text-muted-foreground mt-1">
                {student.statistics.average_per < 0.1
                  ? "Excellent accuracy!"
                  : student.statistics.average_per < 0.2
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

          <div className="space-y-3">
            {/* Last Session */}
            <div className="bg-muted rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Calendar className="w-5 h-5 text-muted-foreground" />
                  <span className="font-medium text-foreground">
                    Last Active
                  </span>
                </div>
                <span className="text-sm text-muted-foreground">
                  {formatDate(student.statistics.last_session_date)}
                </span>
              </div>
            </div>

            {/* Placeholder for future session history */}
            {student.statistics.total_sessions === 0 ? (
              <div className="text-center text-muted-foreground py-8">
                <User className="w-12 h-12 mx-auto mb-2 opacity-50" />
                <p>No practice sessions yet</p>
                <p className="text-sm mt-1">
                  Encourage this student to start practicing!
                </p>
              </div>
            ) : (
              <div className="bg-muted/50 rounded-lg p-4 border-2 border-dashed border-muted-foreground/20">
                <p className="text-sm text-muted-foreground text-center">
                  Detailed session history coming soon
                </p>
              </div>
            )}
          </div>
        </div>
      </Card>

      {/* Insights & Recommendations */}
      <Card className="rounded-2xl bg-card border-2 border-border shadow-md">
        <div className="p-6">
          <h2 className="text-lg font-bold text-foreground mb-4">
            Insights & Recommendations
          </h2>

          <div className="space-y-3">
            {/* Based on accuracy */}
            {student.statistics.average_per > 0 && (
              <div className="bg-muted rounded-lg p-4">
                <h3 className="font-medium text-foreground mb-2">
                  Reading Accuracy
                </h3>
                <p className="text-sm text-muted-foreground">
                  {student.statistics.average_per < 0.1
                    ? "This student is doing excellent! Their accuracy is very high. Consider introducing more challenging material."
                    : student.statistics.average_per < 0.2
                    ? "This student is making good progress. Continue with consistent practice to improve further."
                    : "This student would benefit from more practice. Consider focusing on foundational phonemes and providing additional support."}
                </p>
              </div>
            )}

            {/* Based on streak */}
            <div className="bg-muted rounded-lg p-4">
              <h3 className="font-medium text-foreground mb-2">
                Practice Consistency
              </h3>
              <p className="text-sm text-muted-foreground">
                {student.statistics.current_streak === 0
                  ? "This student hasn't established a practice routine yet. Encourage daily practice to build momentum."
                  : student.statistics.current_streak < 7
                  ? "This student is building a practice habit. Encourage them to keep it up!"
                  : "This student shows excellent practice consistency! They're building strong habits."}
              </p>
            </div>

            {/* Placeholder for phoneme analysis */}
            <div className="bg-muted/50 rounded-lg p-4 border-2 border-dashed border-muted-foreground/20">
              <h3 className="font-medium text-foreground mb-2">
                Problem Areas
              </h3>
              <p className="text-sm text-muted-foreground">
                Detailed phoneme analysis coming soon
              </p>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default StudentDetailView;
