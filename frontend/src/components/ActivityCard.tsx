import { CirclePlay } from "lucide-react";
import { Button } from "./ui/button";
import { Card, CardContent, CardFooter, CardHeader } from "./ui/card";

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

const ActivityCard = ({
  activity,
  onActivityClick,
}: ActivityCardProps & {
  onActivityClick: (activity: any) => void;
}) => {
  return (
    <Card className="text-center">
      <CardHeader>
        <h3 className="text-2xl font-bold">
          <span className="mr-2">{activity.emoji_icon}</span>
          {activity.title}
        </h3>
      </CardHeader>
      <CardContent>
        <p className="text-base">{activity.description}</p>
      </CardContent>
      <CardFooter className="flex justify-center">
        <Button
          onClick={() => {
            onActivityClick(activity);
          }}
          size="lg"
        >
          <CirclePlay />
          Start Activity
        </Button>
      </CardFooter>
    </Card>
  );
};

export default ActivityCard;
