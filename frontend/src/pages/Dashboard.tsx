import { Card, CardHeader, CardContent } from "@/components/ui/card";
import { useContext, useEffect, useState } from "react";
import { AuthContext } from "@/contexts/AuthContext";
import ActivitiesList from "@/components/ActivitiesList";
import SentencePersChart from "@/components/SentencePersChart";
import { Clock, Play } from "lucide-react";
import { getSessions } from "@/api";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { motion } from "framer-motion";
import { 
  staggerContainer, 
  staggerChild, 
  fadeInUp, 
  cardHover,
  buttonHover,
  buttonTap
} from "@/lib/animations";

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
    <motion.main 
      className="flex-1 p-6 bg-gradient-to-br from-background via-background to-accent/5 space-y-8 overflow-y-auto flex flex-col min-h-0 h-full"
      initial="hidden"
      animate="visible"
      variants={staggerContainer}
    >
      {/* Main content */}
      {/* Header with enhanced styling */}
      <motion.div 
        className="relative text-center"
        variants={staggerChild}
      >
        <div className="relative z-10">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-primary via-purple-600 to-pink-600 bg-clip-text text-transparent">
            Hi, {userName}!
          </h1>
          <div className="flex items-center justify-center gap-3 mt-3">
            <p className="text-lg text-muted-foreground font-medium">{motivational}</p>
          </div>
        </div>
      </motion.div>

      {/* Progress Chart with enhanced styling */}
      <motion.div 
        className="hidden md:block"
        variants={staggerChild}
      >
        <div className="relative">
          <SentencePersChart />
        </div>
      </motion.div>

      <motion.div 
        className="flex space-x-6 space-y-6 flex-1 w-full min-w-0 min-h-0 flex-col md:flex-row"
        variants={staggerChild}
      >
        {/* Activities with enhanced styling */}
        <motion.div 
          className="relative flex-1 flex flex-col"
          variants={fadeInUp}
        >
            <ActivitiesList numberOfActivities={3} className="w-full md:h-full flex-1" />
            <div className="flex justify-center mt-4">
              <motion.div
                whileHover={buttonHover}
                whileTap={buttonTap}
              >
                <Button 
                  variant="outline" 
                  size="sm" 
                  className="text-foreground border-primary/30 hover:border-primary/60 hover:bg-primary/5 transition-all duration-200 px-6"
                  onClick={() => router("/practice")}
                >
                  View All Activities
                </Button>
              </motion.div>
            </div>
        </motion.div>
        
        {/* Progress -- Mobile */}
        <motion.div 
          className="md:hidden w-full"
          variants={staggerChild}
        >
          <SentencePersChart />
        </motion.div>

        {/* Practice Calendar / Sidebar with enhanced styling */}
        <motion.div
          variants={fadeInUp}
          whileHover={cardHover}
        >
          <Card className="gap-4 pb-1 px-2 flex flex-col md:overflow-hidden md:min-h-0 rounded-3xl bg-gradient-to-br from-white to-purple-50/50 border-2 border-purple-100/50 shadow-xl md:w-80">
            <CardHeader className="relative">
              <div className="flex items-center gap-3">
                <motion.div 
                  className="p-2 bg-gradient-to-r from-purple-200 to-pink-200 rounded-xl"
                  whileHover={{ rotate: 5 }}
                  transition={{ type: "spring", stiffness: 300 }}
                >
                  <Clock className="w-6 h-6 text-purple-600" />
                </motion.div>
                <h3 className="text-xl font-bold text-purple-800">Past Sessions</h3>
              </div>
            </CardHeader>
            <CardContent className="px-1 md:flex-1 flex flex-col overflow-hidden min-h-0">
              {pastSessions.length > 0 ? (
                <ScrollArea className="rounded-2xl h-full min-h-0">
                  <motion.div 
                    className="flex flex-col gap-3"
                    variants={staggerContainer}
                    initial="hidden"
                    animate="visible"
                  >
                    {pastSessions.map((session, index) => {
                      const colorIndex =
                        Math.abs(session.activity.id) % activityColors.length;
                      const cardColor = activityColors[colorIndex];

                      return (
                        <motion.div
                          key={session.id}
                          variants={staggerChild}
                          whileHover={{ 
                            y: -4, 
                            scale: 1.02,
                            transition: { type: "spring", stiffness: 300 }
                          }}
                          whileTap={{ scale: 0.98 }}
                        >
                          <Card
                            className={`h-fit py-4 group shadow-lg hover:shadow-xl transition-all duration-300 rounded-2xl border-2 border-white/50 cursor-pointer relative overflow-hidden`}
                            onClick={() => router(`/practice/${session.id}`)}
                            style={{
                              backgroundColor: `var(--${cardColor})`,
                            }}
                          >
                            <CardContent className="relative">
                              <motion.div 
                                className="absolute top-2 right-2 w-2 h-2 bg-white/60 rounded-full opacity-0 group-hover:opacity-100"
                                initial={{ scale: 0 }}
                                whileHover={{ scale: 1 }}
                                transition={{ duration: 0.3 }}
                              />
                              <div className="text-lg font-bold text-gray-800">
                                {session.activity.emoji_icon}{" "}
                                {session.activity.title}
                              </div>
                              <div className="text-sm text-gray-600 mt-1">
                                {formatActivityType(session.activity.activity_type)}{" "}
                                - {new Date(session.created_at).toDateString()}
                              </div>
                              <motion.div 
                                className="absolute bottom-2 right-2 opacity-0 group-hover:opacity-100"
                                initial={{ x: 8, opacity: 0 }}
                                whileHover={{ x: 0, opacity: 1 }}
                                transition={{ duration: 0.3 }}
                              >
                                <Play className="w-4 h-4 text-gray-600" />
                              </motion.div>
                            </CardContent>
                          </Card>
                        </motion.div>
                      );
                    })}
                  </motion.div>
                </ScrollArea>
              ) : (
                <motion.div 
                  className="flex flex-col items-center justify-center h-32 text-center"
                  variants={fadeInUp}
                >
                  <motion.div 
                    className="w-16 h-16 bg-gradient-to-r from-gray-200 to-gray-300 rounded-full flex items-center justify-center mb-3"
                    whileHover={{ scale: 1.1, rotate: 5 }}
                    transition={{ type: "spring", stiffness: 300 }}
                  >
                    <Clock className="w-8 h-8 text-gray-500" />
                  </motion.div>
                  <p className="text-gray-500 font-medium">No sessions yet</p>
                  <p className="text-sm text-gray-400">Start practicing to see your progress!</p>
                </motion.div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      </motion.div>
    </motion.main>
  );
};

export default Dashboard;
