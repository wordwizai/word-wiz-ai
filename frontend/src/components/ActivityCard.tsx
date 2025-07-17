import { CirclePlay } from "lucide-react";
import { Button } from "./ui/button";
import { Card, CardContent, CardFooter, CardHeader } from "./ui/card";
import { useTheme } from "@/contexts/ThemeContext";

interface ActivityCardProps {
  activity: {
    id: number;
    title: string;
    description: string;
    emoji_icon: string;
    activity_type: string;
    activity_settings: any;
  };
  onActivityClick: (activity: any) => void;
}

const activityColors = [
  "pastel-blue",
  "pastel-mint",
  "pastel-peach",
  "pastel-purple",
  "pastel-pink",
];

const ActivityCard = ({
  activity,
  onActivityClick,
}: ActivityCardProps & {
  onActivityClick: (activity: any) => void;
}) => {
  // decide on the bacground color based on a hash of the activity ID
  const colorIndex = Math.abs(activity.id) % activityColors.length;
  const cardColor = activityColors[colorIndex];
  const { theme } = useTheme();

  return (
    <Card className={`text-center bg-${cardColor} flex flex-col h-full`}>
      <CardHeader>
        <h3 className="text-2xl font-bold text-left flex flex-col gap-4">
          <div className="text-4xl">{activity.emoji_icon}</div>
          <div className="">{activity.title}</div>
        </h3>
      </CardHeader>
      <CardContent className="flex-1">
        <p className="text-base text- text-left">{activity.description}</p>
      </CardContent>
      <CardFooter className="flex justify-center">
        <Button
          onClick={() => {
            onActivityClick(activity);
          }}
          size="lg"
          variant="ghost"
          className={`rounded-full w-12 h-12 p-0 flex items-center justify-center shadow-lg hover:scale-110 transition-transform `}
        >
          <CirclePlay
            className="size-10"
            color={theme == "light" ? "black" : "white"}
          />
        </Button>
      </CardFooter>
    </Card>
  );
};

export default ActivityCard;
