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
import { useCountUp } from "@/hooks/useCountUp";

interface AnimatedProgressStatProps {
  icon: LucideIcon;
  label: string;
  value: number;
  suffix?: string;
  isLoading: boolean;
}

const AnimatedProgressStat = ({
  icon: Icon,
  label,
  value,
  suffix = "",
  isLoading,
}: AnimatedProgressStatProps) => {
  const animatedValue = useCountUp(value, 1200);

  return (
    <Card className="bg-card rounded-xl border border-border shadow-sm relative overflow-hidden">
      <div className="p-3 relative z-10">
        <div className="text-lg md:text-xl font-bold text-center text-foreground">
          {isLoading ? "..." : `${Math.round(animatedValue)}${suffix}`}
        </div>
        <div className="text-xs text-center text-muted-foreground font-medium mt-0.5">
          {label}
        </div>
      </div>
      <Icon className="absolute -right-1 -bottom-1 w-12 h-12 md:w-14 md:h-14 text-muted-foreground/10" />
    </Card>
  );
};

const ProgressDashboard = () => {
  const { token } = useContext(AuthContext);
  const [statistics, setStatistics] = useState<UserStatistics | null>(null);
  const [statsLoading, setStatsLoading] = useState(true);

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
      {/* Page header */}
      <div className="pb-5 border-b border-border flex items-center gap-3">
        <div className="p-2 bg-primary/10 rounded-lg">
          <BarChart3 className="w-5 h-5 text-primary" />
        </div>
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-foreground">
            Progress
          </h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            Track your reading journey and celebrate your growth
          </p>
        </div>
      </div>

      {/* Progress Stats */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2 md:gap-3">
        <AnimatedProgressStat
          icon={BookOpen}
          label="Total Sessions"
          value={statistics?.total_sessions || 0}
          isLoading={statsLoading}
        />
        <AnimatedProgressStat
          icon={BookOpen}
          label="Words Read"
          value={statistics?.words_read || 0}
          isLoading={statsLoading}
        />
        <AnimatedProgressStat
          icon={Target}
          label="Accuracy"
          value={87}
          suffix="%"
          isLoading={false}
        />
        <AnimatedProgressStat
          icon={Flame}
          label="Current Streak"
          value={statistics?.current_streak || 0}
          suffix=" days"
          isLoading={statsLoading}
        />
        <AnimatedProgressStat
          icon={Star}
          label="Best Streak"
          value={statistics?.longest_streak || 0}
          suffix=" days"
          isLoading={statsLoading}
        />
        <AnimatedProgressStat
          icon={TrendingUp}
          label="Improvement"
          value={15}
          suffix="%"
          isLoading={false}
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
