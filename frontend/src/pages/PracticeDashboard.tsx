import { getActivities } from "@/api";
import ActivitiesList from "@/components/ActivitiesList";
import { AuthContext } from "@/contexts/AuthContext";
import { Target } from "lucide-react";
import { useContext, useEffect, useState } from "react";
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
    <main className="flex-1 p-4 sm:p-6 bg-background space-y-6 overflow-auto w-full max-w-full">
      {/* Page header */}
      <div className="pb-5 border-b border-border flex items-center gap-3">
        <div className="p-2 bg-primary/10 rounded-lg">
          <Target className="w-5 h-5 text-primary" />
        </div>
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-foreground">
            Practice
          </h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            Choose your practice activities and start learning
          </p>
        </div>
      </div>

      {/* Content */}
      {sections.map((section, idx) => (
        <div key={idx} className="space-y-4 w-full px-4 sm:px-12">
          <h2 className="text-lg font-semibold text-foreground">
            {section.title}
          </h2>
          <ActivitiesList
            type={section.filter}
            displayMode="carousel"
            inputActivities={activities}
            useInputActivities={true}
          />
        </div>
      ))}
    </main>
  );
};

export default PracticeDashboard;
