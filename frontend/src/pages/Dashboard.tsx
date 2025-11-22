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
  Palette,
  type LucideIcon,
} from "lucide-react";
import { getSessions } from "@/api";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import DynamicIcon from "@/components/DynamicIcon";

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

interface StatCardProps {
  icon: LucideIcon;
  label: string;
  value: string;
  color: string;
  iconColor: string;
}

const StatCard = ({
  icon: Icon,
  label,
  value,
  color,
  iconColor,
}: StatCardProps) => (
  <Card
    className={`${color} rounded-xl border-2 border-white/80 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden`}
  >
    <div className="p-3 relative z-10">
      <div className="text-xl md:text-2xl font-bold text-foreground">
        {value}
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

  return (
    <main className="flex-1 p-4 sm:p-6 bg-background space-y-6 overflow-y-auto flex flex-col min-h-0 h-full">
      {/* Main content */}
      {/* Header with enhanced styling */}
      <div className="relative text-center">
        <div className="relative z-10">
          <h1 className="text-3xl md:text-4xl font-bold text-foreground">
            Hi, {userName}!
          </h1>
          <div className="mt-4 max-w-2xl mx-auto">
            <div className="bg-accent/10 border-2 border-accent/30 rounded-2xl p-4">
              <div className="flex items-center justify-center gap-2">
                <Sparkles className="w-5 h-5 text-accent shrink-0" />
                <p className="text-base text-foreground/80 text-center font-medium">
                  {motivational}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Stats Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2 md:gap-3">
        <StatCard
          icon={Target}
          label="Sessions"
          value={pastSessions.length.toString()}
          color="bg-pastel-blue"
          iconColor="text-blue-600"
        />
        <StatCard
          icon={Flame}
          label="Streak"
          value="5 days"
          color="bg-pastel-yellow"
          iconColor="text-orange-600"
        />
        <StatCard
          icon={BookOpen}
          label="Words Read"
          value="342"
          color="bg-pastel-mint"
          iconColor="text-green-600"
        />
        <StatCard
          icon={Palette}
          label="Activities"
          value="8"
          color="bg-pastel-coral"
          iconColor="text-pink-600"
        />
      </div>

      <div className="flex space-x-0 sm:space-x-4 space-y-4 flex-1 w-full min-w-0 min-h-0 flex-col md:flex-row md:space-y-0">
        {/* Activities with enhanced styling */}
        <div className="relative flex-1 flex flex-col">
          <ActivitiesList
            numberOfActivities={3}
            className="w-full md:h-full flex-1"
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
