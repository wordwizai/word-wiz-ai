import { Card, CardHeader, CardContent } from "@/components/ui/card";
import { Calendar } from "@/components/ui/calendar";
import { useContext } from "react";
import { AuthContext } from "@/contexts/AuthContext";
import ActivitiesList from "@/components/ActivitiesList";
import SentencePersChart from "@/components/SentencePersChart";

const Dashboard = () => {
  const { user } = useContext(AuthContext);

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

  return (
    <main className="flex-1 p-6 bg-background space-y-8 overflow-auto">
      {/* Main content */}
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold">Hi, {userName}</h1>
        <p className="text-muted-foreground">{motivational}</p>
      </div>

      {/* Progress */}
      <div>
        <SentencePersChart />
      </div>

      <div className="flex space-x-6">
        {/* Activities */}
        <ActivitiesList numberOfActivities={3} />

        {/* Practice Calendar / Sidebar */}
        <div className="space-y-4">
          <Card className="bg-orange-100 dark:bg-orange-600/20 transition-colors">
            <CardHeader>
              <h3 className="text-base font-medium">Practice Sessions</h3>
            </CardHeader>
            <CardContent>
              <Calendar mode="single" className="rounded-lg border" />
            </CardContent>
          </Card>
          <Card className="bg-blue-100 dark:bg-blue-600/20 transition-colors">
            <CardHeader>
              <h3 className="text-base font-medium">Something Else</h3>
            </CardHeader>
            <CardContent>
              <p>Put something here</p>
            </CardContent>
          </Card>
        </div>
      </div>
    </main>
  );
};

export default Dashboard;
