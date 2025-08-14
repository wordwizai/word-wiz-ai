import { getActivities } from "@/api";
import ActivitiesList from "@/components/ActivitiesList";
import { AuthContext } from "@/contexts/AuthContext";
import { Target } from "lucide-react";
import { useContext, useEffect, useState } from "react";
import { motion } from "framer-motion";
import { 
  staggerContainer, 
  staggerChild, 
  fadeInUp 
} from "@/lib/animations";
interface Activity {
  id: number;
  title: string;
  description: string;
  emoji_icon: string;
  activity_type: string;
  activity_settings: any;
}

const PracticeDashboard = () => {
  const sections = [
    {
      title: "Unlimited Practice",
      filter: "unlimited",
    },
    {
      title: "Choice Story Practice",
      filter: "choice-story",
    },
    {
      title: "Story Practice",
      filter: "story",
    },
  ];

  const [activities, setActivities] = useState<Activity[]>([]);
  const { token } = useContext(AuthContext);

  useEffect(() => {
    if (!token) return;
    const fetchActivities = async (token: string) => {
      try {
        const activitiesData = await getActivities(token);
        setActivities(activitiesData);
      } catch (error) {
        console.error("Failed to fetch activities:", error);
      }
    };
    fetchActivities(token);
  }, [token]);

  return (
    <motion.main 
      className="flex-1 p-6 bg-background space-y-8 overflow-auto w-full"
      initial="hidden"
      animate="visible"
      variants={staggerContainer}
    >
      {/* Header */}
      <motion.div 
        className="space-y-2 mx-auto w-fit text-center"
        variants={staggerChild}
      >
        <h1 className="text-3xl font-bold">
          <motion.div
            whileHover={{ scale: 1.05, rotate: 5 }}
            transition={{ type: "spring", stiffness: 300 }}
            className="inline-block"
          >
            <Target className="inline size-7 mr-2 mb-1.5" />
          </motion.div>
          <span>Practice Dashboard</span>
        </h1>
        <p className="text-muted-foreground">
          Manage your practice sessions and activities.
        </p>
      </motion.div>
      
      {/* Content */}
      {sections.map((section, idx) => (
        <motion.div 
          key={idx} 
          className="space-y-2 px-10"
          variants={fadeInUp}
          transition={{ delay: idx * 0.1 }}
        >
          <motion.div 
            className="flex items-center gap-3 mb-6"
            whileHover={{ x: 10 }}
            transition={{ type: "spring", stiffness: 300 }}
          >
            <motion.div 
              className="p-2 bg-gradient-to-r from-blue-200 to-purple-200 rounded-xl"
              whileHover={{ rotate: 5, scale: 1.1 }}
              transition={{ type: "spring", stiffness: 300 }}
            >
              <Target className="w-5 h-5 text-blue-600" />
            </motion.div>
            <h2 className="text-2xl font-bold text-gray-800">
              {section.title}
            </h2>
          </motion.div>
          <ActivitiesList
            type={section.filter}
            displayMode="carousel"
            inputActivities={activities}
            useInputActivities={true}
          />
        </motion.div>
      ))}
    </motion.main>
  );
};

export default PracticeDashboard;
