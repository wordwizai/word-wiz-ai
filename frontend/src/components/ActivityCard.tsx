import { Play } from "lucide-react";
import { Button } from "./ui/button";
import { Card, CardContent, CardFooter, CardHeader } from "./ui/card";
import { Badge } from "./ui/badge";
import DynamicIcon from "./DynamicIcon";

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

  return (
    <Card
      className="group cursor-pointer rounded-2xl border-2 border-white/80 shadow-sm hover:shadow-lg hover:-translate-y-0.5 transition-all duration-200 flex flex-col h-full"
      style={{ backgroundColor: `var(--${cardColor})` }}
      onClick={() => onActivityClick(activity)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") onActivityClick(activity);
      }}
    >
      <CardHeader className="p-4 pb-3">
        <div className="flex items-start gap-3">
          {/* Icon container */}
          <div className="flex-shrink-0 w-10 h-10 bg-white/60 rounded-xl flex items-center justify-center shadow-sm">
            <DynamicIcon
              name={activity.emoji_icon}
              className="w-5 h-5 text-foreground/80"
              fallback="BookOpen"
            />
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <h3 className="font-bold text-base text-foreground mb-1 leading-tight">
              {activity.title}
            </h3>
            <Badge
              variant="secondary"
              className="px-2 py-0.5 text-xs font-medium rounded-full bg-white/60 text-foreground/70 border border-white/40"
            >
              {activity.activity_type}
            </Badge>
          </div>
        </div>
      </CardHeader>

      <CardContent className="px-4 pb-3 flex-1">
        <p className="text-sm text-foreground/60 leading-relaxed line-clamp-3">
          {activity.description}
        </p>
      </CardContent>

      <CardFooter className="p-4 pt-0 mt-auto">
        <Button
          size="sm"
          className="w-full bg-white/70 hover:bg-white text-foreground border border-white/80 hover:border-white rounded-xl font-semibold shadow-sm hover:shadow-md transition-all duration-200 group-hover:bg-white"
          aria-label={`Start activity ${activity.title}`}
        >
          <Play className="w-3.5 h-3.5 mr-1.5" fill="currentColor" />
          Start Practice
        </Button>
      </CardFooter>
    </Card>
  );
};

export default ActivityCard;
