import { Card, CardHeader, CardContent } from "@/components/ui/card";
import { useContext, useEffect, useState } from "react";
import { AuthContext } from "@/contexts/AuthContext";
import ActivitiesList from "@/components/ActivitiesList";
import SentencePersChart from "@/components/SentencePersChart";
import { Clock, Play } from "lucide-react";
import { getSessions } from "@/api";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useNavigate } from "react-router-dom";

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
];

const Dashboard = () => {
  const { user, token } = useContext(AuthContext);

  const userName = user?.full_name || "Guest";
  const motivationalQuotes = [
    "📚 Keep turning the page—every chapter brings you closer to your goals!",
    "🌟 Every word you read is a step forward. Keep going!",
    "🚀 Reading today, leading tomorrow. Stay inspired!",
    "🧠 Feed your mind—read something new every day!",
    "💡 Each book is a new adventure. Dive in!",
    "🎯 Consistency in reading leads to mastery. You’ve got this!",
    "🌱 Grow your knowledge, one page at a time.",
    "🔥 Ignite your passion for learning—read on!",
    "🏆 Every page read is a victory. Celebrate your progress!",
    "✨ The more you read, the more you succeed. Keep it up!",
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
    <main className="flex-1 p-6 bg-background space-y-8 overflow-auto flex flex-col min-h-0">
      {/* Main content */}
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold">Hi, {userName}</h1>
        <p className="text-muted-foreground">{motivational}</p>
      </div>

      {/* Progress */}
      <SentencePersChart />

      <div className="flex space-x-6 flex-1 w-full min-w-0 min-h-0">
        {/* Activities */}
        <ActivitiesList numberOfActivities={3} />

        {/* Practice Calendar / Sidebar */}
        <Card className="gap-1 pb-1 flex flex-col overflow-hidden min-h-0">
          <CardHeader>
            <h3 className="text-lg font-bold">
              <Clock className="inline-block mr-2" />
              Past Sessions
            </h3>
          </CardHeader>
          <CardContent className="px-1 flex-1 flex flex-col overflow-hidden min-h-0">
            {pastSessions.length > 0 ? (
              <ScrollArea className="rounded-2xl h-full min-h-0">
                {pastSessions.map((session) => {
                  const colorIndex =
                    Math.abs(session.activity.id) % activityColors.length;
                  const cardColor = activityColors[colorIndex];

                  return (
                    <Card
                      key={session.id}
                      className={`h-fit py-2 group`}
                      onClick={() => router(`/practice/${session.id}`)}
                      style={{
                        cursor: "pointer",
                        backgroundColor: `var(--${cardColor})`,
                      }}
                    >
                      <CardContent>
                        <div className="text-lg font-bold">
                          {session.activity.emoji_icon} {session.activity.title}
                        </div>
                        <div className="text-sm text-muted-foreground">
                          {formatActivityType(session.activity.activity_type)} -{" "}
                          {new Date(session.created_at).toDateString()}
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </ScrollArea>
            ) : (
              <div>No past sessions found.</div>
            )}
          </CardContent>
        </Card>
      </div>
    </main>
  );
};

export default Dashboard;
