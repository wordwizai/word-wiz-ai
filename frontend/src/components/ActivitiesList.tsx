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
import { BookOpen } from "lucide-react";

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
  shuffleDaily?: boolean; // if true, shuffle activities based on date seed
}

// Seeded random number generator using mulberry32 algorithm
// Provides excellent distribution and fast performance
const seededRandom = (seed: number) => {
  let t = seed + 0x6D2B79F5;
  t = Math.imul(t ^ (t >>> 15), t | 1);
  t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
  const result = ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  return result;
};

// Seed offset to ensure different selections for different activity types
const CHOICE_STORY_SEED_OFFSET = 1000;

// Get date-based seed (changes daily)
const getDailySeed = () => {
  const today = new Date();
  // Use year, month, and day to create a unique seed for each day
  return today.getFullYear() * 10000 + (today.getMonth() + 1) * 100 + today.getDate();
};

const ActivitiesList = ({
  numberOfActivities = -1,
  displayMode = "list",
  type,
  useInputActivities = false, // if true, use inputActivities prop instead of fetching
  inputActivities,
  className = "",
  shuffleDaily = false,
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

  const onActivityClick = async (activity: Record<string, unknown>) => {
    console.log("Activity clicked:", activity, token);
    const response = await createSession(token ?? "", (activity as any).id);
    console.log("Session created:", response);
    // Redirect to the practice session page
    window.location.href = `/practice/${response.id}`;
  };

  // Select featured activities for daily display
  const getDisplayedActivities = () => {
    // Don't shuffle if explicitly disabled or if showing all activities
    // When numberOfActivities === -1, we want to show all activities unshuffled
    if (!shuffleDaily || numberOfActivities === -1) {
      return activities.filter((a) => (type ? a.activity_type === type : true));
    }

    // Separate activities by type
    const unlimitedActivities = activities.filter(
      (a) => a.activity_type === "unlimited"
    );
    const storyActivities = activities.filter(
      (a) => a.activity_type === "story"
    );
    const choiceStoryActivities = activities.filter(
      (a) => a.activity_type === "choice-story"
    );

    const featured: Activity[] = [];

    // Always show the first unlimited activity
    if (unlimitedActivities.length > 0) {
      featured.push(unlimitedActivities[0]);
    }

    // Use daily seed to select one story activity
    if (storyActivities.length > 0) {
      const seed = getDailySeed();
      const randomValue = seededRandom(seed);
      const index = Math.floor(randomValue * storyActivities.length);
      featured.push(storyActivities[index]);
    }

    // Use daily seed (with offset) to select one choice-story activity
    if (choiceStoryActivities.length > 0) {
      const seed = getDailySeed() + CHOICE_STORY_SEED_OFFSET;
      const randomValue = seededRandom(seed);
      const index = Math.floor(randomValue * choiceStoryActivities.length);
      featured.push(choiceStoryActivities[index]);
    }

    return featured;
  };

  const displayedActivities = getDisplayedActivities();

  if (displayMode === "carousel") {
    return (
      <Carousel
        opts={{
          align: "start",
        }}
        className={className + " overflow-y-visible w-full"}
      >
        <CarouselContent className="overflow-y-visible -ml-4">
          {activities.length === 0
            ? Array.from(
                {
                  length: numberOfActivities === -1 ? 1 : numberOfActivities,
                },
                (_, idx) => (
                  <CarouselItem
                    key={idx}
                    className="xl:basis-1/4 lg:basis-1/3 md:basis-1/2 overflow-y-visible pl-4"
                  >
                    <Skeleton className="h-80 rounded-3xl" />
                  </CarouselItem>
                )
              )
            : displayedActivities
                .slice(
                  0,
                  numberOfActivities === -1
                    ? displayedActivities.length
                    : numberOfActivities
                )
                .map((activity, idx) => (
                  <CarouselItem
                    key={idx}
                    className="xl:basis-1/4 lg:basis-1/3 md:basis-1/2 overflow-y-visible pl-4"
                  >
                    <ActivityCard
                      activity={activity}
                      onActivityClick={onActivityClick}
                    />
                  </CarouselItem>
                ))}
        </CarouselContent>
        <CarouselPrevious className="bg-card/90 border-2 border-border hover:bg-card transition-colors -left-12" />
        <CarouselNext className="bg-card/90 border-2 border-border hover:bg-card transition-colors -right-12" />
      </Carousel>
    );
  }

  return (
    <div className={"space-y-4 flex flex-col " + className}>
      {/* Header section */}
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-primary/10 rounded-xl">
          <BookOpen className="w-5 h-5 text-primary" />
        </div>
        <h2 className="text-xl md:text-2xl font-bold text-foreground">
          Choose Your Practice
        </h2>
      </div>

      {/* Activities grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 flex-1">
        {activities.length === 0
          ? Array.from(
              { length: numberOfActivities === -1 ? 3 : numberOfActivities },
              (_, idx) => (
                <Skeleton
                  key={idx}
                  className="h-64 sm:h-72 md:h-80 rounded-3xl"
                />
              )
            )
          : displayedActivities
              .slice(
                0,
                numberOfActivities === -1
                  ? displayedActivities.length
                  : numberOfActivities
              )
              .map((activity, idx) => (
                <ActivityCard
                  key={idx}
                  activity={activity}
                  onActivityClick={onActivityClick}
                />
              ))}
      </div>
    </div>
  );
};

export default ActivitiesList;
