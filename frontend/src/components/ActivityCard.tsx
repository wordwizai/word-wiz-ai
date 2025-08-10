import { Play } from "lucide-react";
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
];

const ActivityCard = ({ activity, onActivityClick }: ActivityCardProps) => {
  const colorIndex = Math.abs(activity.id) % activityColors.length;
  const cardColor = activityColors[colorIndex];
  const { theme } = useTheme();

  return (
    <motion.div
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      className="h-full"
    >
      <Card
        className="flex flex-col h-full rounded-3xl shadow-md cursor-pointer transition-shadow hover:shadow-lg overflow-visible"
        style={{ backgroundColor: `var(--${cardColor})` }}
        onClick={() => onActivityClick(activity)}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") onActivityClick(activity);
        }}
      >
        <CardHeader className="flex flex-col items-start gap-3">
          <div className="text-5xl">{activity.emoji_icon}</div>
          <h3 className="text-2xl font-bold">{activity.title}</h3>
          <Badge
            variant="secondary"
            className="px-2 py-0.5 text-sm font-semibold rounded-full"
          >
            {activity.activity_type}
          </Badge>
        </CardHeader>
        <CardContent className="flex-1 text-left text-base leading-relaxed">
          {activity.description}
        </CardContent>
        <CardFooter className="flex justify-center">
          <motion.div
            whileHover={{ scale: 1.2, rotate: 15 }}
            whileTap={{ scale: 0.9, rotate: -15 }}
          >
            <Button
              size="lg"
              variant="ghost"
              className="rounded-full w-14 h-14 p-0 flex items-center justify-center shadow-md transition-transform transform-gpu bg-gradient-to-br from-cyan-200 via-indigo-300 to-purple-500 hover:from-cyan-300 hover:via-indigo-400 hover:to-purple-500"
              aria-label={`Start activity ${activity.title}`}
            >
              <Play
                className="size-8"
                color={theme === "light" ? "#000" : "#fff"}
              />
            </Button>
          </motion.div>
        </CardFooter>
      </Card>
    </motion.div>
  );
};

export default ActivityCard;
