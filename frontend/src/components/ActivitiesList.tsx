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
import { motion } from "framer-motion";
import { 
  staggerContainer, 
  staggerChild, 
  fadeInUp,
  iconHover 
} from "@/lib/animations";

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

  const onActivityClick = async (activity: Record<string, unknown>) => {
    console.log("Activity clicked:", activity, token);
    const response = await createSession(token ?? "", (activity as any).id);
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
        className={className + " overflow-y-visible"}
        >
          <CarouselContent className="overflow-y-visible">
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
                      <motion.div
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ duration: 0.4, delay: idx * 0.1 }}
                      >
                        <Skeleton className="h-80 rounded-3xl" />
                      </motion.div>
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
                      className="xl:basis-1/5 lg:basis-1/4 md:basis-1/3 sm:basis-1/2 @xs:basis-1 overflow-y-visible"
                    >
                      <motion.div
                        initial={{ opacity: 0, x: 50 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ duration: 0.5, delay: idx * 0.1 }}
                      >
                        <ActivityCard
                          activity={activity}
                          onActivityClick={onActivityClick}
                        />
                      </motion.div>
                    </CarouselItem>
                  ))}
          </CarouselContent>
          <motion.div
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
          >
            <CarouselPrevious className="bg-white/80 border-2 border-gray-200 hover:bg-white hover:border-gray-300 transition-all duration-200" />
          </motion.div>
          <motion.div
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
          >
            <CarouselNext className="bg-white/80 border-2 border-gray-200 hover:bg-white hover:border-gray-300 transition-all duration-200" />
          </motion.div>
        </Carousel>
    );
  }
  
  return (
    <motion.div 
      className={"space-y-6 flex flex-col " + className}
      initial="hidden"
      animate="visible"
      variants={staggerContainer}
    >
      {/* Header section */}
      <motion.div 
        className="flex items-center gap-3 mb-6"
        variants={staggerChild}
      >
        <motion.div 
          className="p-2 bg-gradient-to-r from-blue-200 to-purple-200 rounded-xl"
          whileHover={iconHover}
        >
          <BookOpen className="w-5 h-5 text-blue-600" />
        </motion.div>
        <h2 className="text-2xl font-bold text-gray-800">Choose Your Practice</h2>
      </motion.div>
      
      {/* Activities grid */}
      <motion.div 
        className="grid grid-cols-1 md:grid-cols-3 gap-6 flex-1"
        variants={staggerContainer}
      >
        {activities.length === 0
          ? Array.from(
              { length: numberOfActivities === -1 ? 3 : numberOfActivities },
              (_, idx) => (
                <motion.div
                  key={idx}
                  variants={staggerChild}
                  transition={{ delay: idx * 0.1 }}
                >
                  <Skeleton className="h-80 rounded-3xl" />
                </motion.div>
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
                <motion.div
                  key={idx}
                  variants={staggerChild}
                  transition={{ delay: idx * 0.1 }}
                >
                  <ActivityCard
                    activity={activity}
                    onActivityClick={onActivityClick}
                  />
                </motion.div>
              ))}
      </motion.div>
      
      {/* Empty state with enhanced styling */}
      {activities.length === 0 && !useInputActivities && (
        <motion.div 
          className="text-center py-12"
          variants={fadeInUp}
        >
          <motion.div 
            className="w-20 h-20 bg-gradient-to-r from-gray-200 to-gray-300 rounded-full flex items-center justify-center mx-auto mb-4"
            whileHover={{ scale: 1.1, rotate: 5 }}
            transition={{ type: "spring", stiffness: 300 }}
          >
            <BookOpen className="w-10 h-10 text-gray-500" />
          </motion.div>
          <h3 className="text-xl font-semibold text-gray-700 mb-2">No activities available</h3>
          <p className="text-gray-500">Check back later for new practice activities!</p>
        </motion.div>
      )}
    </motion.div>
  );
};

export default ActivitiesList;
