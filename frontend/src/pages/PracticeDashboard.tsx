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
    <main className="flex-1 p-6 bg-gradient-to-br from-background to-purple-50/50 space-y-8 overflow-auto w-full">
      {/* Header with enhanced styling */}
      <div className="space-y-2 mx-auto w-fit text-center relative">
        {/* Decorative background */}
        <div className="absolute inset-0 bg-gradient-to-r from-purple-100/30 to-pink-100/30 rounded-3xl blur-xl transform scale-110"></div>
        <div className="relative z-10 py-6">
          <h1 className="text-3xl md:text-4xl font-bold bg-gradient-to-r from-primary via-purple-600 to-pink-600 bg-clip-text text-transparent mb-3">
            <Target className="inline size-8 mr-3 mb-1.5 text-primary" />
            <span>Practice Dashboard</span>
          </h1>
          <p className="text-muted-foreground text-lg">
            Manage your practice sessions and activities.
          </p>
        </div>
      </div>
      {/* Content */}
      {sections.map((section, idx) => (
        <div key={idx} className="space-y-4 px-4 md:px-10 relative">
          {/* Decorative background for each section */}
          <div className="absolute inset-0 bg-gradient-to-r from-blue-100/20 to-cyan-100/20 rounded-3xl blur-xl"></div>
          <div className="relative z-10">
            <div className="flex items-center gap-3 mb-6 justify-center md:justify-start">
              <div className="p-3 bg-gradient-to-r from-blue-200 to-purple-200 rounded-xl shadow-lg">
                <Target className="w-6 h-6 text-blue-600" />
              </div>
              <h2 className="text-2xl md:text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
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
        </div>
      ))}
    </main>
  );
};

export default PracticeDashboard;
