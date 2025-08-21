import { Button } from "@/components/ui/button";
import { Home } from "lucide-react";

const UnderConstructionPage = () => {
  return (
    <main className="flex h-screen w-full items-center justify-center">
      <div className="text-center">
        <h1 className="text-4xl font-bold mb-4">Under Construction</h1>
        <p className="text-lg">
          This website is currently under construction and will be available
          soon.
          <br />
          Our backend is still under development, but we are working hard to get
          it ready for you as soon as possible.
        </p>
        <Button asChild>
          <a href="/" className="mt-8">
            <Home />
            Back to Home
          </a>
        </Button>
      </div>
    </main>
  );
};

export default UnderConstructionPage;
