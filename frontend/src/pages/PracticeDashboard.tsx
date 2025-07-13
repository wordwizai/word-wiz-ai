import ActivitiesList from "@/components/ActivitiesList";
import { Target } from "lucide-react";

const PracticeDashboard = () => {
  const sections = [
    {
      title: "Unlimited Practice",
      filter: "unlimited",
    },
  ];

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
          <ActivitiesList type={section.filter} displayMode="carousel" />
        </div>
      ))}
    </main>
  );
};

export default PracticeDashboard;
