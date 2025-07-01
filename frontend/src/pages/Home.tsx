import { Button } from "@/components/ui/button";
import {
  Card,
  CardHeader,
  CardContent,
  CardFooter,
} from "@/components/ui/card";
import { Calendar } from "@/components/ui/calendar";
import { CircleQuestionMark, House, Settings, Target } from "lucide-react";
import { Link } from "react-router-dom";

const Home = () => {
  const userName = "Bruce";
  const motivational = "Keep pushing forward!";
  const progress = 45;
  const activities = ["Activity 1", "Activity 2", "Activity 3"];

  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <aside className="w-16 flex flex-col items-center bg-background p-4 space-y-4">
        <Button variant="ghost" size="icon">
          <Link to="/">
            <House />
          </Link>
        </Button>
        <Button variant="ghost" size="icon">
          <Target />
        </Button>
        <div className="mt-auto space-y-2">
          <Button variant="ghost" size="icon">
            <Settings />
          </Button>
          <Button variant="ghost" size="icon">
            <CircleQuestionMark />
          </Button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 p-6 bg-background space-y-8 overflow-auto">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold">Hi, {userName}</h1>
          <p className="text-muted-foreground">{motivational}</p>
        </div>

        {/* Progress */}
        <Card className="bg-pastel-mint">
          <CardHeader>
            <h2 className="text-lg font-semibold">Progress: {progress}%</h2>
          </CardHeader>
          <CardContent>
            <div className="h-6 w-full bg-muted rounded overflow-hidden">
              <div
                className="h-full bg-primary transition-all"
                style={{ width: `${progress}%` }}
              />
            </div>
          </CardContent>
        </Card>

        <div className="flex space-x-6">
          {/* Activities */}
          <div className="flex-1 grid grid-cols-1 md:grid-cols-3 gap-4">
            {activities.map((a, idx) => (
              <Card key={idx} className="bg-pastel-pink">
                <CardHeader>
                  <h3 className="text-base font-medium">{a}</h3>
                </CardHeader>
                <CardContent>
                  <p>Details about {a}...</p>
                </CardContent>
                <CardFooter>
                  <Button size="sm">Start</Button>
                </CardFooter>
              </Card>
            ))}
          </div>

          {/* Practice Calendar / Sidebar */}
          <div className="space-y-4">
            <Card className="bg-pastel-peach">
              <CardHeader>
                <h3 className="text-base font-medium">Practice Sessions</h3>
              </CardHeader>
              <CardContent>
                <Calendar mode="single" className="rounded-lg border" />
              </CardContent>
            </Card>
            <Card className="bg-pastel-blue">
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
    </div>
  );
};

export default Home;
