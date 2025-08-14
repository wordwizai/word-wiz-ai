import { Play, Star } from "lucide-react";
import { motion } from "framer-motion";
import { Button } from "./ui/button";
import { Card, CardContent, CardFooter, CardHeader } from "./ui/card";
import { useTheme } from "@/contexts/ThemeContext";
import { Badge } from "./ui/badge";

interface ActivityCardProps {
  activity: {
    id: number;
    title: string;
    description: string;
    emoji_icon: string;
    activity_type: string;
    activity_settings: Record<string, unknown>;
  };
  onActivityClick: (activity: Record<string, unknown>) => void;
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

const ActivityCard = ({ activity, onActivityClick }: ActivityCardProps) => {
  const colorIndex = Math.abs(activity.id) % activityColors.length;
  const cardColor = activityColors[colorIndex];
  const { theme } = useTheme();

  return (
    <motion.div
      whileHover={{ scale: 1.03, y: -8 }}
      whileTap={{ scale: 0.98 }}
      className="h-full"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Card
        className="flex flex-col h-full rounded-3xl shadow-lg cursor-pointer transition-all duration-300 overflow-visible border-2 border-white/50 hover:-translate-y-2 hover:scale-105 relative group"
        style={{ backgroundColor: `var(--${cardColor})` }}
        onClick={() => onActivityClick(activity)}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") onActivityClick(activity);
        }}
      >
        <CardHeader className="flex flex-col items-start gap-4 p-6">
          <div className="relative">
            <div className="text-6xl relative z-10">{activity.emoji_icon}</div>
          </div>
          
          <div className="space-y-2">
            <h3 className="text-lg sm:text-xl md:text-2xl font-bold text-gray-800 leading-tight">{activity.title}</h3>
            <Badge
              variant="secondary"
              className="px-2 sm:px-3 py-1 text-xs sm:text-sm font-semibold rounded-full bg-white/60 text-gray-700 border border-white/40 hover:bg-white/80 transition-colors duration-200"
            >
              {activity.activity_type}
            </Badge>
          </div>
        </CardHeader>
        
        <CardContent className="flex-1 text-left text-sm sm:text-base leading-relaxed px-4 sm:px-6 pb-4">
          <p className="text-gray-700 leading-relaxed">{activity.description}</p>
        </CardContent>
        
        <CardFooter className="flex justify-center pb-4 sm:pb-6">
          <motion.div
            whileHover={{ scale: 1.1, rotate: 5 }}
            whileTap={{ scale: 0.9, rotate: -5 }}
            className="relative"
          >
            <Button
              size="lg"
              variant="ghost"
              className="rounded-full w-14 h-14 sm:w-16 sm:h-16 p-0 flex items-center justify-center shadow-lg transition-all duration-300 transform-gpu bg-gradient-to-br from-white/80 via-white/90 to-white/80 hover:from-white hover:via-white hover:to-white border-2 border-white/60 hover:border-white/80 hover:shadow-xl min-h-[44px] min-w-[44px]"
              aria-label={`Start activity ${activity.title}`}
            >
              <Play
                className="size-6 sm:size-8 text-gray-700"
                fill="currentColor"
              />
            </Button>
          </motion.div>
        </CardFooter>
        
        {/* Bottom accent line */}
        <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 w-20 h-1 bg-gradient-to-r from-transparent via-white/60 to-transparent rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
      </Card>
    </motion.div>
  );
};

export default ActivityCard;
