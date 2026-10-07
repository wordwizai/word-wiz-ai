import ActivityCard from "./ActivityCard";
import { Skeleton } from "./ui/skeleton";
import { useStartActivity } from "@/hooks/useActivities";
import type { Activity } from "@/lib/activities";

interface ActivitiesListProps {
  activities: Activity[] | null;
  // How many placeholder cards to show while `activities` is still null.
  skeletonCount?: number;
}

const ActivitiesList = ({ activities, skeletonCount = 3 }: ActivitiesListProps) => {
  const { start, startingId } = useStartActivity();

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {activities === null
        ? Array.from({ length: skeletonCount }, (_, i) => (
            <Skeleton key={i} className="h-56 rounded-2xl" />
          ))
        : activities.map((activity) => (
            <ActivityCard
              key={activity.id}
              activity={activity}
              onStart={start}
              isStarting={startingId === activity.id}
              disabled={startingId !== null}
            />
          ))}
    </div>
  );
};

// Shown instead of an empty grid when the activities request fails, so the
// page doesn't look like it has nothing to offer.
export const ActivitiesLoadError = () => (
  <div className="rounded-2xl border border-dashed px-6 py-10 text-center">
    <p className="font-medium text-foreground">
      Couldn't load the activities
    </p>
    <p className="mt-1 text-sm text-muted-foreground">
      Check your connection and refresh the page.
    </p>
  </div>
);

export default ActivitiesList;
