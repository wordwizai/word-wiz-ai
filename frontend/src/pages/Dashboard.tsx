import { Card, CardHeader, CardContent } from "@/components/ui/card";
import { useContext, useEffect, useState } from "react";
import { AuthContext } from "@/contexts/AuthContext";
import ActivitiesList from "@/components/ActivitiesList";
import {
  Clock,
  Target,
  Flame,
  BookOpen,
  Trophy,
  ArrowRight,
  type LucideIcon,
} from "lucide-react";
import { getSessions, getUserStatistics, type UserStatistics } from "@/api";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import DynamicIcon from "@/components/DynamicIcon";
import { useCountUp } from "@/hooks/useCountUp";

interface Session {
  id: string;
  created_at: string;
  activity: {
    id: number;
    title: string;
    activity_type: string;
    emoji_icon: string;
  };
  is_completed: boolean;
}

interface AnimatedStatCardProps {
  icon: LucideIcon;
  label: string;
  value: number;
  suffix?: string;
  isLoading: boolean;
}

const AnimatedStatCard = ({
  icon: Icon,
  label,
  value,
  suffix = "",
  isLoading,
}: AnimatedStatCardProps) => {
  const animatedValue = useCountUp(isLoading ? 0 : value, 1200);
  const displayValue = isLoading ? null : `${animatedValue}${suffix}`;

  return (
    <Card className="bg-card rounded-xl border border-border shadow-sm relative overflow-hidden">
      <div className="p-4 relative z-10">
        {isLoading ? (
          <>
            <Skeleton className="h-8 w-16 mb-1.5 rounded-lg" />
            <Skeleton className="h-3 w-20 rounded" />
          </>
        ) : (
          <>
            <div className="text-2xl md:text-3xl font-bold text-foreground tracking-tight">
              {displayValue}
            </div>
            <div className="text-xs text-muted-foreground font-medium mt-1">
              {label}
            </div>
          </>
        )}
      </div>
      <Icon className="absolute -right-2 -bottom-2 w-16 h-16 md:w-20 md:h-20 text-muted-foreground/10" />
    </Card>
  );
};

const Dashboard = () => {
  const { user, token } = useContext(AuthContext);

  const userName = user?.full_name || "Guest";
  const motivationalQuotes = [
    "Keep turning the page—every chapter brings you closer to your goals!",
    "Every word you read is a step forward. Keep going!",
    "Reading today, leading tomorrow. Stay inspired!",
    "Feed your mind—read something new every day!",
    "Each book is a new adventure. Dive in!",
    "Consistency in reading leads to mastery. You've got this!",
    "Grow your knowledge, one page at a time.",
    "Ignite your passion for learning—read on!",
    "Every page read is a victory. Celebrate your progress!",
    "The more you read, the more you succeed. Keep it up!",
  ];
  const today = new Date();
  const quoteIndex = today.getDate() % motivationalQuotes.length;
  const motivational = motivationalQuotes[quoteIndex];

  const [pastSessions, setPastSessions] = useState<Session[]>([]);
  const [sessionsLoading, setSessionsLoading] = useState(true);
  const [statistics, setStatistics] = useState<UserStatistics | null>(null);
  const [statsLoading, setStatsLoading] = useState(true);
  const router = useNavigate();

  useEffect(() => {
    const fetchPastSessions = async () => {
      if (!token) return;
      try {
        setSessionsLoading(true);
        const response = await getSessions(token);
        setPastSessions(response);
      } catch (error) {
        console.error("Error fetching past sessions:", error);
      } finally {
        setSessionsLoading(false);
      }
    };
    fetchPastSessions();
  }, [token]);

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

  const formatActivityType = (type: string | undefined) => {
    if (!type) return "Unknown";
    switch (type.toLowerCase()) {
      case "unlimited":
        return "Unlimited";
      case "choice-story":
        return "Choice Story";
      default:
        return type.charAt(0).toUpperCase() + type.slice(1);
    }
  };

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return "Good morning";
    if (hour < 18) return "Good afternoon";
    return "Good evening";
  };

  return (
    <main className="flex-1 p-4 sm:p-6 bg-background space-y-6 overflow-y-auto flex flex-col min-h-0 h-full">
      {/* Page header */}
      <div className="pb-5 border-b border-border">
        <p className="text-sm text-muted-foreground">{getGreeting()}</p>
        <h1 className="text-2xl md:text-3xl font-bold text-foreground mt-0.5">
          {userName}
        </h1>
        <p className="text-sm text-muted-foreground mt-1 max-w-2xl">
          {motivational}
        </p>
      </div>

      {/* Quick Stats Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <AnimatedStatCard
          icon={Target}
          label="Total Sessions"
          value={statistics?.total_sessions || 0}
          isLoading={statsLoading}
        />
        <AnimatedStatCard
          icon={Flame}
          label="Current Streak"
          value={statistics?.current_streak || 0}
          suffix=" days"
          isLoading={statsLoading}
        />
        <AnimatedStatCard
          icon={BookOpen}
          label="Words Read"
          value={statistics?.words_read || 0}
          isLoading={statsLoading}
        />
        <AnimatedStatCard
          icon={Trophy}
          label="Longest Streak"
          value={statistics?.longest_streak || 0}
          suffix=" days"
          isLoading={statsLoading}
        />
      </div>

      <div className="flex space-x-0 sm:space-x-4 space-y-4 flex-1 w-full min-w-0 min-h-0 flex-col md:flex-row md:space-y-0">
        {/* Activities */}
        <div className="relative flex-1 flex flex-col">
          <ActivitiesList
            numberOfActivities={3}
            className="w-full md:h-full flex-1"
            shuffleDaily={true}
          />
          <div className="flex justify-center mt-4">
            <Button
              variant="outline"
              size="sm"
              className="text-foreground gap-2 min-h-[44px] px-6 py-2"
              onClick={() => router("/practice")}
            >
              View All Activities
              <ArrowRight className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Recent Sessions panel */}
        <Card className="flex flex-col md:overflow-hidden md:min-h-0 rounded-xl bg-card border border-border shadow-sm md:w-80">
          <CardHeader className="p-4 pb-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-muted-foreground" />
                <h3 className="text-base font-semibold text-foreground">
                  Recent Sessions
                </h3>
              </div>
              {pastSessions.length > 0 && (
                <span className="text-xs text-muted-foreground bg-muted rounded-full px-2 py-0.5">
                  {pastSessions.length}
                </span>
              )}
            </div>
          </CardHeader>
          <Separator />
          <CardContent className="p-4 pt-3 md:flex-1 flex flex-col overflow-hidden min-h-0">
            {sessionsLoading ? (
              <div className="flex flex-col gap-3">
                {Array.from({ length: 4 }).map((_, i) => (
                  <div key={i} className="flex items-center gap-3 p-3 rounded-lg bg-muted/40">
                    <Skeleton className="w-7 h-7 rounded-lg shrink-0" />
                    <div className="flex-1 space-y-1.5">
                      <Skeleton className="h-3.5 w-3/4 rounded" />
                      <Skeleton className="h-3 w-1/2 rounded" />
                    </div>
                  </div>
                ))}
              </div>
            ) : pastSessions.length > 0 ? (
              <ScrollArea className="rounded-lg h-full min-h-0">
                <div className="flex flex-col gap-1.5 pr-3">
                  {pastSessions.map((session) => (
                    <button
                      key={session.id}
                      className="w-full text-left rounded-lg border border-border hover:border-border/80 hover:bg-muted/40 cursor-pointer p-3 transition-colors"
                      onClick={() => router(`/practice/${session.id}`)}
                    >
                      <div className="flex items-center gap-2">
                        <DynamicIcon
                          name={session.activity.emoji_icon}
                          className="w-4 h-4 shrink-0 text-muted-foreground"
                          fallback="Star"
                        />
                        <span className="text-sm font-medium text-foreground line-clamp-1 flex-1">
                          {session.activity.title}
                        </span>
                      </div>
                      <div className="text-xs text-muted-foreground mt-1 pl-6">
                        {formatActivityType(session.activity.activity_type)} ·{" "}
                        {new Date(session.created_at).toLocaleDateString()}
                      </div>
                    </button>
                  ))}
                </div>
              </ScrollArea>
            ) : (
              <div className="flex flex-col items-center justify-center h-36 text-center gap-2">
                <div className="w-12 h-12 bg-muted rounded-xl flex items-center justify-center">
                  <Clock className="w-6 h-6 text-muted-foreground" />
                </div>
                <p className="text-sm font-semibold text-foreground">No sessions yet</p>
                <p className="text-xs text-muted-foreground">
                  Start practicing to see your history here
                </p>
                <Button
                  size="sm"
                  variant="outline"
                  className="mt-1 text-xs h-8 px-3"
                  onClick={() => router("/practice")}
                >
                  Start practicing
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </main>
  );
};

export default Dashboard;
