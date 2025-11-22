import PhonemeErrorsPieChart from "@/components/PhonemeErrorsPieChart";
import SentencePersChart from "@/components/SentencePersChart";
import { Card } from "@/components/ui/card";
import {
  BarChart3,
  BookOpen,
  Target,
  Flame,
  Star,
  TrendingUp,
  type LucideIcon,
} from "lucide-react";
import { useContext, useEffect, useState } from "react";
import { AuthContext } from "@/contexts/AuthContext";
import { getUserStatistics, type UserStatistics } from "@/api";

interface ProgressStatProps {
  icon: LucideIcon;
  label: string;
  value: string;
  iconColor: string;
}

const ProgressStat = ({
  icon: Icon,
  label,
  value,
  iconColor,
}: ProgressStatProps) => (
  <Card className="bg-card rounded-xl border-2 border-border shadow-sm relative overflow-hidden">
    <div className="p-3 relative z-10">
      <div className="text-lg md:text-xl font-bold text-center text-foreground">
        {value}
      </div>
      <div className="text-xs text-center text-muted-foreground font-medium mt-0.5">
        {label}
      </div>
    </div>
    <Icon
      className={`absolute -right-1 -bottom-1 w-12 h-12 md:w-14 md:h-14 ${iconColor} opacity-15`}
    />
  </Card>
);

const ProgressDashboard = () => {
  const { token } = useContext(AuthContext);
  const [statistics, setStatistics] = useState<UserStatistics | null>(null);
  const [statsLoading, setStatsLoading] = useState(true);

  // Fetch user statistics
  useEffect(() => {
    const fetchStatistics = async () => {
      if (!token) return;

      try {
        setStatsLoading(true);
        const stats = await getUserStatistics(token);
        setStatistics(stats);
      } catch (error) {
        console.error("Error fetching statistics:", error);
      } finally {
        setStatsLoading(false);
      }
    };

    fetchStatistics();
  }, [token]);

  return (
    <main className="flex-1 p-4 sm:p-6 bg-background space-y-6 overflow-auto flex flex-col min-h-0">
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-primary/10 mb-3">
          <BarChart3 className="w-8 h-8 text-primary" />
        </div>
        <h1 className="text-3xl font-bold text-foreground">Your Progress</h1>
        <p className="text-muted-foreground mt-2">
          Track your reading journey!
        </p>
      </div>

      {/* Progress Stats */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2 md:gap-3">
        <ProgressStat
          icon={BookOpen}
          label="Total Sessions"
          value={
            statsLoading ? "..." : statistics?.total_sessions?.toString() || "0"
          }
          iconColor="text-blue-600"
        />
        <ProgressStat
          icon={BookOpen}
          label="Words Read"
          value={
            statsLoading ? "..." : statistics?.words_read?.toString() || "0"
          }
          iconColor="text-purple-600"
        />
        <ProgressStat
          icon={Target}
          label="Accuracy"
          value="87%"
          iconColor="text-green-600"
        />
        <ProgressStat
          icon={Flame}
          label="Current Streak"
          value={
            statsLoading ? "..." : `${statistics?.current_streak || 0} days`
          }
          iconColor="text-orange-600"
        />
        <ProgressStat
          icon={Star}
          label="Best Streak"
          value={
            statsLoading ? "..." : `${statistics?.longest_streak || 0} days`
          }
          iconColor="text-yellow-600"
        />
        <ProgressStat
          icon={TrendingUp}
          label="Improvement"
          value="+15%"
          iconColor="text-teal-600"
        />
      </div>
      <SentencePersChart />
      <div className="flex flex-col md:flex-row gap-6 w-full min-w-0 min-h-0">
        <PhonemeErrorsPieChart errorType="substitution" className="flex-1" />
        <PhonemeErrorsPieChart errorType="insertion" className="flex-1" />
        <PhonemeErrorsPieChart errorType="deletion" className="flex-1" />
      </div>
    </main>
  );
};

export default ProgressDashboard;
