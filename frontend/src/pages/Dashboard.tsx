import { Card, CardHeader, CardContent } from "@/components/ui/card";
import { useContext, useEffect, useState } from "react";
import { AuthContext } from "@/contexts/AuthContext";
import ActivitiesList from "@/components/ActivitiesList";
import {
  Clock,
  Sparkles,
  Target,
  Flame,
  BookOpen,
  type LucideIcon,
} from "lucide-react";
import { getSessions, getUserStatistics, type UserStatistics } from "@/api";
import { ScrollArea } from "@/components/ui/scroll-area";
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

const activityColors = [
  "pastel-blue",
  "pastel-mint",
  "pastel-peach",
  "pastel-purple",
  "pastel-pink",
  "pastel-lavender",
  "pastel-yellow",
  "pastel-coral",
  "pastel-teal",
];

interface AnimatedStatCardProps {
  icon: LucideIcon;
  label: string;
  value: number;
  suffix?: string;
  color: string;
  iconColor: string;
  isLoading: boolean;
}

const AnimatedStatCard = ({
  icon: Icon,
  label,
  value,
  suffix = "",
  color,
  iconColor,
  isLoading,
}: AnimatedStatCardProps) => {
  const animatedValue = useCountUp(isLoading ? 0 : value, 1200);
  const displayValue = isLoading ? "..." : `${animatedValue}${suffix}`;

  return (
    <Card
      className={`${color} rounded-xl border-2 border-white/80 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden`}
    >
      <div className="p-3 relative z-10">
        <div className="text-xl md:text-2xl font-bold text-foreground">
          {displayValue}
        </div>
        <div className="text-xs text-muted-foreground font-medium mt-0.5">
          {label}
        </div>
      </div>
      <Icon
        className={`absolute -right-2 -bottom-2 w-16 h-16 md:w-20 md:h-20 ${iconColor} opacity-20`}
      />
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
  const [statistics, setStatistics] = useState<UserStatistics | null>(null);
  const [statsLoading, setStatsLoading] = useState(true);
  const router = useNavigate();

  useEffect(() => {
    const fetchPastSessions = async () => {
      if (!token) return;
      try {
        const response = await getSessions(token);
        setPastSessions(response);
      } catch (error) {
        console.error("Error fetching past sessions:", error);
      }
    };
    fetchPastSessions();
  }, [token]);

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

  const formatActivityType = (type: string) => {
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
    if (hour < 12) return "Good Morning";
    if (hour < 18) return "Good Afternoon";
    return "Good Evening";
  };

  return (
    <main className="flex-1 p-4 sm:p-6 bg-background space-y-6 overflow-y-auto flex flex-col min-h-0 h-full">
      {/* Main content */}
      {/* Hero Header with visual appeal */}
      <div className="relative rounded-2xl overflow-hidden bg-gradient-to-br from-primary/10 via-accent/5 to-primary/5 border border-primary/20 p-6">
        {/* Decorative background elements */}
        <div className="absolute inset-0 overflow-hidden">
          {/* Gradient orbs */}
          <div className="absolute -top-10 -right-10 w-40 h-40 bg-primary/10 rounded-full blur-3xl" />
          <div className="absolute -bottom-10 -left-10 w-40 h-40 bg-accent/10 rounded-full blur-3xl" />

          {/* Floating icons */}
          <BookOpen className="absolute top-4 right-16 w-8 h-8 text-primary/10 rotate-12" />
          <Target className="absolute bottom-6 right-8 w-6 h-6 text-accent/10 -rotate-12" />
          <Sparkles className="absolute top-8 left-1/3 w-6 h-6 text-primary/10 rotate-45" />
        </div>

        {/* Main content */}
        <div className="relative z-10 flex items-center gap-6">
          {/* Hero graphic - Abstract icon composition */}
          <div className="hidden sm:flex relative shrink-0">
            <div className="relative w-24 h-24 md:w-28 md:h-28">
              {/* Layered circles with icons */}
              <div className="absolute inset-0 bg-gradient-to-br from-primary/20 to-accent/20 rounded-2xl rotate-6 transition-transform group-hover:rotate-12" />
              <div className="absolute inset-0 bg-gradient-to-tl from-accent/20 to-primary/20 rounded-2xl -rotate-6 transition-transform group-hover:-rotate-12" />
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="relative">
                  <BookOpen className="w-12 h-12 md:w-14 md:h-14 text-primary" />
                  <Sparkles className="absolute -top-1 -right-1 w-5 h-5 text-accent animate-pulse" />
                </div>
              </div>
            </div>
          </div>

          {/* Text content */}
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <p className="text-xs text-muted-foreground font-medium">
                {getGreeting()}
              </p>
              <Sparkles className="w-3 h-3 text-accent" />
            </div>
            <h1 className="text-2xl md:text-4xl font-bold text-foreground mb-2 bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text">
              {userName}!
            </h1>
            <p className="text-sm md:text-base text-muted-foreground/80 font-medium max-w-2xl">
              {motivational}
            </p>
          </div>
        </div>
      </div>

      {/* Quick Stats Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2 md:gap-3">
        <AnimatedStatCard
          icon={Target}
          label="Sessions"
          value={statistics?.total_sessions || 0}
          color="bg-pastel-blue"
          iconColor="text-blue-600"
          isLoading={statsLoading}
        />
        <AnimatedStatCard
          icon={Flame}
          label="Current Streak"
          value={statistics?.current_streak || 0}
          suffix=" days"
          color="bg-pastel-yellow"
          iconColor="text-orange-600"
          isLoading={statsLoading}
        />
        <AnimatedStatCard
          icon={BookOpen}
          label="Words Read"
          value={statistics?.words_read || 0}
          color="bg-pastel-mint"
          iconColor="text-green-600"
          isLoading={statsLoading}
        />
        <AnimatedStatCard
          icon={Target}
          label="Longest Streak"
          value={statistics?.longest_streak || 0}
          suffix=" days"
          color="bg-pastel-coral"
          iconColor="text-pink-600"
          isLoading={statsLoading}
        />
      </div>

      <div className="flex space-x-0 sm:space-x-4 space-y-4 flex-1 w-full min-w-0 min-h-0 flex-col md:flex-row md:space-y-0">
        {/* Activities with enhanced styling */}
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
              className="text-foreground border-primary/30 hover:border-primary/60 hover:bg-primary/5 transition-colors px-6 py-2 min-h-[44px]"
              onClick={() => router("/practice")}
            >
              View All Activities
            </Button>
          </div>
        </div>

        {/* Practice Calendar / Sidebar with enhanced styling */}
        <Card className="flex flex-col md:overflow-hidden md:min-h-0 rounded-2xl bg-card border-2 border-border shadow-md md:w-80">
          <CardHeader className="p-4">
            <div className="flex items-center gap-3">
              <Clock className="w-5 h-5 text-primary" />
              <h3 className="text-lg font-bold text-foreground">
                Recent Sessions
              </h3>
            </div>
          </CardHeader>
          <CardContent className="p-4 pt-0 md:flex-1 flex flex-col overflow-hidden min-h-0">
            {pastSessions.length > 0 ? (
              <ScrollArea className="rounded-xl h-full min-h-0">
                <div className="flex flex-col gap-3 pr-3">
                  {pastSessions.map((session) => {
                    const colorIndex =
                      Math.abs(session.activity.id) % activityColors.length;
                    const cardColor = activityColors[colorIndex];

                    return (
                      <Card
                        key={session.id}
                        className="group shadow-sm hover:shadow-md transition-shadow duration-200 rounded-lg border-2 border-white/80 cursor-pointer p-3"
                        onClick={() => router(`/practice/${session.id}`)}
                        style={{
                          backgroundColor: `var(--${cardColor})`,
                        }}
                      >
                        <div className="text-sm font-bold text-gray-800 flex items-center gap-2">
                          <DynamicIcon
                            name={session.activity.emoji_icon}
                            className="w-4 h-4 shrink-0"
                            fallback="Star"
                          />
                          <span className="line-clamp-1">
                            {session.activity.title}
                          </span>
                        </div>
                        <div className="text-xs text-gray-600 mt-1">
                          {formatActivityType(session.activity.activity_type)} •{" "}
                          {new Date(session.created_at).toLocaleDateString()}
                        </div>
                      </Card>
                    );
                  })}
                </div>
              </ScrollArea>
            ) : (
              <div className="flex flex-col items-center justify-center h-32 text-center">
                <div className="w-16 h-16 bg-muted rounded-full flex items-center justify-center mb-3">
                  <Clock className="w-8 h-8 text-gray-500" />
                </div>
                <p className="text-gray-500 font-medium">No sessions yet</p>
                <p className="text-sm text-gray-400">
                  Start practicing to see your progress!
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </main>
  );
};

export default Dashboard;
