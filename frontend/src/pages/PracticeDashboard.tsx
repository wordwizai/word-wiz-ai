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
    // {
    //   title: "Unlimited Practice",
    //   filter: "unlimited",
    // },
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
      {/* Header */}
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-primary/10 mb-3">
          <Target className="w-8 h-8 text-primary" />
        </div>
        <h1 className="text-3xl font-bold text-foreground">
          Practice Dashboard
        </h1>
        <p className="text-muted-foreground mt-2">
          Choose your practice activities and start learning!
        </p>
      </div>

      {/* Content */}
      {sections.map((section, idx) => (
        <div key={idx} className="space-y-4 w-full px-4 sm:px-12">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-500/10 rounded-xl">
              <Target className="w-5 h-5 text-blue-600" />
            </div>
            <h2 className="text-xl md:text-2xl font-bold text-foreground">
              {section.title}
            </h2>
          </div>
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
