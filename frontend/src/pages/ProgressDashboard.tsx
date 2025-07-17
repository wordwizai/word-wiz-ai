import SentencePersChart from "@/components/SentencePersChart";
import { Route } from "lucide-react";

const ProgressDashboard = () => {
  return (
    <main className="flex-1 p-6 bg-background space-y-8 overflow-auto flex flex-col min-h-0">
      <div className="space-y-2 mx-auto w-fit text-center">
        <h1 className="text-3xl font-bold">
          <Route className="inline size-7 mr-2 mb-1.5" />
          <span>Progress Dashboard</span>
        </h1>
        <p className="text-muted-foreground">
          Look at your progress and see how you're doing!
        </p>
      </div>
      <SentencePersChart />
    </main>
  );
};

export default ProgressDashboard;
