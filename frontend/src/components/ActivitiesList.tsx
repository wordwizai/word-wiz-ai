import { useContext, useEffect, useState } from "react";
import { Button } from "./ui/button";
import { Card, CardContent, CardFooter, CardHeader } from "./ui/card";
import { AuthContext } from "@/contexts/AuthContext";
import { createSession, getActivities } from "@/api";
import { CirclePlay } from "lucide-react";
import ActivityCard from "./ActivityCard";
import { Skeleton } from "./ui/skeleton";

interface Activity {
  id: number;
  title: string;
  description: string;
  emoji_icon: string;
  activity_type: string;
  activity_settings: any;
}

interface ActivitiesListProps {
  numberOfActivities?: number;
  displayMode?: "featured" | "list"; // list just lists them out, featured shows 1 big and the rest small
  type?: string; // filter by activity type
}

const ActivitiesList = ({
  numberOfActivities = -1,
  displayMode = "list",
  type = null,
}: ActivitiesListProps) => {
  const [activities, setActivities] = useState<Activity[]>([]);
  const { token } = useContext(AuthContext);

  useEffect(() => {
    if (!token) return;
    const fetchActivities = async (token: string) => {
      try {
        const activitiesData = await getActivities(token);
        console.log("Fetched activities:", activitiesData);
        setActivities(activitiesData);
      } catch (error) {
        console.error("Failed to fetch activities:", error);
      }
    };
    fetchActivities(token);
  }, [token]);

  const onActivityClick = async (activity: Activity) => {
    console.log("Activity clicked:", activity, token);
    const response = await createSession(token ?? "", activity.id);
    console.log("Session created:", response);
    // Redirect to the practice session page
    window.location.href = `/practice/${response.id}`;
  };

  return (
    <div className="flex-1 grid grid-cols-1 md:grid-cols-3 gap-4">
      {activities.length === 0
        ? Array.from(
            { length: numberOfActivities === -1 ? 1 : numberOfActivities },
            (_, idx) => <Skeleton key={idx} />,
          )
        : activities
            .filter((a) => (type ? a.activity_type == type : true))
            .slice(0, numberOfActivities ?? -1)
            .map((activity, idx) => (
              <ActivityCard
                key={idx}
                activity={activity}
                onActivityClick={onActivityClick}
              />
            ))}
    </div>
  );
};

export default ActivitiesList;
