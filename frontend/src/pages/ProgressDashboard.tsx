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
  Sparkles,
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
  iconColor: string;
  isLoading: boolean;
}

const AnimatedProgressStat = ({
  icon: Icon,
  label,
  value,
  suffix = "",
  iconColor,
  isLoading,
}: AnimatedProgressStatProps) => {
  const animatedValue = useCountUp(value, 1200);

  return (
    <Card className="bg-card rounded-xl border-2 border-border shadow-sm relative overflow-hidden">
      <div className="p-3 relative z-10">
        <div className="text-lg md:text-xl font-bold text-center text-foreground">
          {isLoading ? "..." : `${Math.round(animatedValue)}${suffix}`}
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
};

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
      {/* Hero Header */}
      <div className="relative rounded-2xl overflow-hidden bg-gradient-to-br from-green-500/10 via-primary/5 to-teal-500/10 border border-green-500/20 p-6">
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-10 -right-10 w-40 h-40 bg-green-500/10 rounded-full blur-3xl" />
          <div className="absolute -bottom-10 -left-10 w-40 h-40 bg-teal-500/10 rounded-full blur-3xl" />
          <BarChart3 className="absolute top-4 right-16 w-8 h-8 text-green-500/10 rotate-12" />
          <TrendingUp className="absolute bottom-6 right-8 w-6 h-6 text-primary/10 -rotate-12" />
          <Sparkles className="absolute top-8 left-1/3 w-5 h-5 text-accent/10 rotate-45" />
        </div>
        <div className="relative z-10 flex items-center gap-5">
          <div className="hidden sm:flex shrink-0">
            <div className="relative w-16 h-16">
              <div className="absolute inset-0 bg-gradient-to-br from-green-500/20 to-teal-500/20 rounded-2xl rotate-6" />
              <div className="absolute inset-0 bg-gradient-to-tl from-teal-500/20 to-green-500/20 rounded-2xl -rotate-6" />
              <div className="absolute inset-0 flex items-center justify-center">
                <BarChart3 className="w-8 h-8 text-green-600" />
              </div>
            </div>
          </div>
          <div>
            <p className="text-xs text-muted-foreground font-medium uppercase tracking-wide mb-1">
              Statistics
            </p>
            <h1 className="text-2xl md:text-3xl font-bold bg-gradient-to-r from-green-600 via-primary to-teal-600 bg-clip-text text-transparent">
              Your Progress
            </h1>
            <p className="text-sm text-muted-foreground mt-1">
              Track your reading journey and celebrate your growth!
            </p>
          </div>
        </div>
      </div>

      {/* Progress Stats */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2 md:gap-3">
        <AnimatedProgressStat
          icon={BookOpen}
          label="Total Sessions"
          value={statistics?.total_sessions || 0}
          iconColor="text-blue-600"
          isLoading={statsLoading}
        />
        <AnimatedProgressStat
          icon={BookOpen}
          label="Words Read"
          value={statistics?.words_read || 0}
          iconColor="text-purple-600"
          isLoading={statsLoading}
        />
        <AnimatedProgressStat
          icon={Target}
          label="Accuracy"
          value={87}
          suffix="%"
          iconColor="text-green-600"
          isLoading={false}
        />
        <AnimatedProgressStat
          icon={Flame}
          label="Current Streak"
          value={statistics?.current_streak || 0}
          suffix=" days"
          iconColor="text-orange-600"
          isLoading={statsLoading}
        />
        <AnimatedProgressStat
          icon={Star}
          label="Best Streak"
          value={statistics?.longest_streak || 0}
          suffix=" days"
          iconColor="text-yellow-600"
          isLoading={statsLoading}
        />
        <AnimatedProgressStat
          icon={TrendingUp}
          label="Improvement"
          value={15}
          suffix="%"
          iconColor="text-teal-600"
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
