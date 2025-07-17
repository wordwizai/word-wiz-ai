import { useContext, useEffect, useState } from "react";
import { AuthContext } from "@/contexts/AuthContext";
import { createSession, getActivities } from "@/api";
import ActivityCard from "./ActivityCard";
import { Skeleton } from "./ui/skeleton";
import {
  Carousel,
  CarouselContent,
  CarouselItem,
  CarouselNext,
  CarouselPrevious,
} from "./ui/carousel";

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
  displayMode?: "featured" | "list" | "carousel"; // list just lists them out, featured shows 1 big and the rest small
  type?: string; // filter by activity type
  filter?: string; // filter by activity settings
  useInputActivities?: boolean; // if true, use inputActivities prop instead of fetching
  inputActivities?: Activity[];
  className?: string; // additional class names for styling
}

const ActivitiesList = ({
  numberOfActivities = -1,
  displayMode = "list",
  type,
  useInputActivities = false, // if true, use inputActivities prop instead of fetching
  inputActivities,
  className = "",
}: ActivitiesListProps) => {
  const [activities, setActivities] = useState<Activity[]>([]);
  const { token } = useContext(AuthContext);

  useEffect(() => {
    if (useInputActivities) {
      setActivities(inputActivities || []);
      return;
    }
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
  }, [token, useInputActivities, inputActivities]);

  const onActivityClick = async (activity: Activity) => {
    console.log("Activity clicked:", activity, token);
    const response = await createSession(token ?? "", activity.id);
    console.log("Session created:", response);
    // Redirect to the practice session page
    window.location.href = `/practice/${response.id}`;
  };

  if (displayMode === "carousel") {
    return (
      <Carousel
        opts={{
          align: "start",
        }}
        className={className}
      >
        <CarouselContent>
          {activities.length === 0
            ? Array.from(
                {
                  length: numberOfActivities === -1 ? 1 : numberOfActivities,
                },
                (_, idx) => (
                  <CarouselItem
                    key={idx}
                    className="md:basis-1/6 sm:basis-1/3 @xs:basis-1"
                  >
                    <Skeleton />
                  </CarouselItem>
                ),
              )
            : activities
                .filter((a) => (type ? a.activity_type === type : true))
                .slice(
                  0,
                  numberOfActivities === -1
                    ? activities.length
                    : numberOfActivities,
                )
                .map((activity, idx) => (
                  <CarouselItem
                    key={idx}
                    className="xl:basis-1/5 lg:basis-1/4 md:basis-1/3 sm:basis-1/2 @xs:basis-1"
                  >
                    <ActivityCard
                      activity={activity}
                      onActivityClick={onActivityClick}
                    />
                  </CarouselItem>
                ))}
        </CarouselContent>
        <CarouselPrevious />
        <CarouselNext />
      </Carousel>
    );
  }
  return (
    <div
      className={"flex-1 grid grid-cols-1 md:grid-cols-3 gap-4 " + className}
    >
      {activities.length === 0
        ? Array.from(
            { length: numberOfActivities === -1 ? 1 : numberOfActivities },
            (_, idx) => <Skeleton key={idx} />,
          )
        : activities
            .filter((a) => (type ? a.activity_type === type : true))
            .slice(
              0,
              numberOfActivities === -1
                ? activities.length
                : numberOfActivities,
            )
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
