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
    {
      title: "Lesson based",
      filter: "lesson",
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
    <main className="flex-1 p-6 bg-background space-y-8 overflow-auto w-full">
      {/* Header */}
      <div className="space-y-2 mx-auto w-fit text-center">
        <h1 className="text-3xl font-bold">
          <Target className="inline size-7 mr-2 mb-1.5" />
          <span>Practice Dashboard</span>
        </h1>
        <p className="text-muted-foreground">
          Manage your practice sessions and activities.
        </p>
      </div>
      {/* Content */}
      {sections.map((section, idx) => (
        <div key={idx} className="space-y-2 px-10">
          <h2 className="text-xl font-bold">{section.title}</h2>
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
