import { Button } from "@/components/ui/button";
import {
  Card,
  CardHeader,
  CardContent,
  CardFooter,
} from "@/components/ui/card";
import { Calendar } from "@/components/ui/calendar";
import { useContext } from "react";
import { AuthContext } from "@/contexts/AuthContext";
import ActivitiesList from "@/components/ActivitiesList";

const Dashboard = () => {
  const { user } = useContext(AuthContext);

  const userName = user?.full_name || "Guest";
  const motivational = "Keep pushing forward!";
  const progress = 45;
  const activities = ["Activity 1", "Activity 2", "Activity 3"];

  return (
    <main className="flex-1 p-6 bg-background space-y-8 overflow-auto">
      {/* Main content */}
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold">Hi, {userName}</h1>
        <p className="text-muted-foreground">{motivational}</p>
      </div>

      {/* Progress */}
      <Card className="bg-green-100 dark:bg-green-600/20 transition-colors">
        <CardHeader>
          <h2 className="text-lg font-semibold text-primary">
            Progress: {progress}%
          </h2>
        </CardHeader>
        <CardContent>
          <div className="h-6 w-full bg-gray-200 dark:bg-gray-700/60 rounded overflow-hidden">
            <div
              className="h-full bg-gray-700"
              style={{ width: `${progress}%` }}
            />
          </div>
        </CardContent>
      </Card>

      <div className="flex space-x-6">
        {/* Activities */}
        <ActivitiesList numberOfActivities={3} />

        {/* Practice Calendar / Sidebar */}
        <div className="space-y-4">
          <Card className="bg-orange-100 dark:bg-orange-600/20 transition-colors">
            <CardHeader>
              <h3 className="text-base font-medium">Practice Sessions</h3>
            </CardHeader>
            <CardContent>
              <Calendar mode="single" className="rounded-lg border" />
            </CardContent>
          </Card>
          <Card className="bg-blue-100 dark:bg-blue-600/20 transition-colors">
            <CardHeader>
              <h3 className="text-base font-medium">Something Else</h3>
            </CardHeader>
            <CardContent>
              <p>Put something here</p>
            </CardContent>
          </Card>
        </div>
      </div>
    </main>
  );
};

export default Dashboard;
