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

const ActivityCard = ({ activity, onActivityClick }: ActivityCardProps) => {
  return (
    <Card
      className="group cursor-pointer rounded-xl bg-card border border-border hover:border-primary/30 hover:bg-muted/30 transition-colors duration-150 flex flex-col h-full shadow-sm"
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
          <div className="flex-shrink-0 w-9 h-9 bg-primary/10 rounded-lg flex items-center justify-center">
            <DynamicIcon
              name={activity.emoji_icon}
              className="w-4 h-4 text-primary"
              fallback="BookOpen"
            />
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-base text-foreground mb-1 leading-tight">
              {activity.title}
            </h3>
            <Badge
              variant="secondary"
              className="px-2 py-0.5 text-xs font-medium rounded-md"
            >
              {activity.activity_type}
            </Badge>
          </div>
        </div>
      </CardHeader>

      <CardContent className="px-4 pb-3 flex-1">
        <p className="text-sm text-muted-foreground leading-relaxed line-clamp-3">
          {activity.description}
        </p>
      </CardContent>

      <CardFooter className="p-4 pt-0 mt-auto">
        <Button
          size="sm"
          variant="outline"
          className="w-full rounded-lg font-medium gap-1.5 group-hover:border-primary/40 group-hover:text-primary transition-colors"
          aria-label={`Start activity ${activity.title}`}
        >
          <Play className="w-3.5 h-3.5" fill="currentColor" />
          Start Practice
        </Button>
      </CardFooter>
    </Card>
  );
};

export default ActivityCard;
