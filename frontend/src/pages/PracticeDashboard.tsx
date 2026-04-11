import { getActivities } from "@/api";
import ActivitiesList from "@/components/ActivitiesList";
import { AuthContext } from "@/contexts/AuthContext";
import { Target, BookOpen, Sparkles } from "lucide-react";
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
      {/* Hero Header */}
      <div className="relative rounded-2xl overflow-hidden bg-gradient-to-br from-blue-500/10 via-primary/5 to-accent/10 border border-blue-500/20 p-6">
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-10 -right-10 w-40 h-40 bg-blue-500/10 rounded-full blur-3xl" />
          <div className="absolute -bottom-10 -left-10 w-40 h-40 bg-primary/10 rounded-full blur-3xl" />
          <BookOpen className="absolute top-4 right-16 w-8 h-8 text-blue-500/10 rotate-12" />
          <Target className="absolute bottom-6 right-8 w-6 h-6 text-primary/10 -rotate-12" />
          <Sparkles className="absolute top-8 left-1/3 w-5 h-5 text-accent/10 rotate-45" />
        </div>
        <div className="relative z-10 flex items-center gap-5">
          <div className="hidden sm:flex shrink-0">
            <div className="relative w-16 h-16">
              <div className="absolute inset-0 bg-gradient-to-br from-blue-500/20 to-primary/20 rounded-2xl rotate-6" />
              <div className="absolute inset-0 bg-gradient-to-tl from-primary/20 to-blue-500/20 rounded-2xl -rotate-6" />
              <div className="absolute inset-0 flex items-center justify-center">
                <Target className="w-8 h-8 text-primary" />
              </div>
            </div>
          </div>
          <div>
            <p className="text-xs text-muted-foreground font-medium uppercase tracking-wide mb-1">
              Activities
            </p>
            <h1 className="text-2xl md:text-3xl font-bold bg-gradient-to-r from-primary via-blue-600 to-accent bg-clip-text text-transparent">
              Practice Dashboard
            </h1>
            <p className="text-sm text-muted-foreground mt-1">
              Choose your practice activities and start learning!
            </p>
          </div>
        </div>
      </div>

      {/* Content */}
      {sections.map((section, idx) => (
        <div key={idx} className="space-y-4 w-full px-4 sm:px-12">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary/10 rounded-xl">
              <BookOpen className="w-5 h-5 text-primary" />
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
