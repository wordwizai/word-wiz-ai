import { Card, CardHeader, CardContent } from "@/components/ui/card";
import { useContext, useEffect, useState } from "react";
import { AuthContext } from "@/contexts/AuthContext";
import ActivitiesList from "@/components/ActivitiesList";
import SentencePersChart from "@/components/SentencePersChart";
import { Clock, Play, TrendingUp } from "lucide-react";
import { getSessions } from "@/api";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useNavigate } from "react-router-dom";
import { wordWizIcon } from "@/assets";
import { Button } from "@/components/ui/button";

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

const Dashboard = () => {
  const { user, token } = useContext(AuthContext);

  const userName = user?.full_name || "Guest";
  const motivationalQuotes = [
    "🎉 Keep turning the page—every chapter brings you closer to your goals!",
    "✨ Every word you read is a step forward. Keep going!",
    "🚀 Reading today, leading tomorrow. Stay inspired!",
    "🧠 Feed your mind—read something new every day!",
    "💡 Each book is a new adventure. Dive in!",
    "🎯 Consistency in reading leads to mastery. You've got this!",
    "🌱 Grow your knowledge, one page at a time.",
    "🔥 Ignite your passion for learning—read on!",
    "🏆 Every page read is a victory. Celebrate your progress!",
    "⭐ The more you read, the more you succeed. Keep it up!",
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
    <main className="flex-1 p-4 sm:p-6 bg-gradient-to-br from-background via-background to-accent/5 space-y-6 sm:space-y-8 overflow-y-auto flex flex-col min-h-0 h-full">
      {/* Main content */}
      {/* Header with enhanced styling */}
      <div className="relative text-center">
        <div className="relative z-10">
          <h1 className="text-3xl md:text-4xl font-bold bg-gradient-to-r from-primary via-purple-600 to-pink-600 bg-clip-text text-transparent">
            Hi, {userName}!
          </h1>
          <div className="flex items-center justify-center gap-3 mt-3">
            <p className="text-sm sm:text-base md:text-lg text-muted-foreground font-medium text-center px-2">
              {motivational}
            </p>
          </div>
        </div>
      </div>

      {/* Progress Chart with enhanced styling */}
      <div className="hidden md:block">
        <div className="relative">
          <SentencePersChart />
        </div>
      </div>

      <div className="flex space-x-0 sm:space-x-6 space-y-6 flex-1 w-full min-w-0 min-h-0 flex-col md:flex-row md:space-y-0">
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
              className="text-foreground border-primary/30 hover:border-primary/60 hover:bg-primary/5 transition-all duration-200 px-6 py-2 min-h-[44px]"
              onClick={() => router("/practice")}
            >
              View All Activities
            </Button>
          </div>
        </div>

        {/* Progress -- Mobile */}
        <div className="md:hidden w-full">
          <SentencePersChart />
        </div>

        {/* Practice Calendar / Sidebar with enhanced styling */}
        <Card className="gap-4 pb-1 px-2 flex flex-col md:overflow-hidden md:min-h-0 rounded-3xl bg-gradient-to-br from-white to-purple-50/50 border-2 border-purple-100/50 shadow-xl md:w-80">
          <CardHeader className="relative">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-r from-purple-200 to-pink-200 rounded-xl">
                <Clock className="w-5 h-5 sm:w-6 sm:h-6 text-purple-600" />
              </div>
              <h3 className="text-lg sm:text-xl font-bold text-purple-800">
                Past Sessions
              </h3>
            </div>
          </CardHeader>
          <CardContent className="px-1 md:flex-1 flex flex-col overflow-hidden min-h-0">
            {pastSessions.length > 0 ? (
              <ScrollArea className="rounded-2xl h-full min-h-0">
                <div className="flex flex-col gap-3">
                  {pastSessions.map((session) => {
                    const colorIndex =
                      Math.abs(session.activity.id) % activityColors.length;
                    const cardColor = activityColors[colorIndex];

                    return (
                      <Card
                        key={session.id}
                        className={`h-fit py-4 group shadow-lg hover:shadow-xl transition-all duration-300 rounded-2xl border-2 border-white/50 cursor-pointer hover:-translate-y-2 hover:scale-105`}
                        onClick={() => router(`/practice/${session.id}`)}
                        style={{
                          backgroundColor: `var(--${cardColor})`,
                        }}
                      >
                        <CardContent className="relative">
                          <div className="absolute top-2 right-2 w-2 h-2 bg-white/60 rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                          <div className="text-lg font-bold text-gray-800">
                            {session.activity.emoji_icon}{" "}
                            {session.activity.title}
                          </div>
                          <div className="text-sm text-gray-600 mt-1">
                            {formatActivityType(session.activity.activity_type)}{" "}
                            - {new Date(session.created_at).toDateString()}
                          </div>
                          <div className="absolute bottom-2 right-2 opacity-0 group-hover:opacity-100 transition-all duration-300 transform translate-x-2">
                            <Play className="w-4 h-4 text-gray-600" />
                          </div>
                        </CardContent>
                      </Card>
                    );
                  })}
                </div>
              </ScrollArea>
            ) : (
              <div className="flex flex-col items-center justify-center h-32 text-center">
                <div className="w-16 h-16 bg-gradient-to-r from-gray-200 to-gray-300 rounded-full flex items-center justify-center mb-3">
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
