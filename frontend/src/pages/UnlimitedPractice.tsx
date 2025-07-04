import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Mic, Home } from "lucide-react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Link } from "react-router-dom";

const UnlimitedPractice = () => {
  const [currentSentence] = useState(
    "The quick brown fox jumped over the lazy dog",
  );
  const wordArray = currentSentence.split(" ");

  return (
    <div className="min-h-screen px-4 py-4 flex flex-col items-center gap-6">
      {/* Header */}
      <div className="w-full flex justify-between items-center">
        <Link to="/dashboard">
          <Button variant="ghost" className="text-muted-foreground group">
            <Home className="size-5" />
            <span className="opacity-0 translate-x-[-16px] transition-all duration-200 group-hover:opacity-100 group-hover:translate-x-0">
              Home
            </span>
          </Button>
        </Link>
        <h1 className="scroll-m-20 text-3xl font-semibold tracking-tight first:mt-0">
          Unlimited Practice
        </h1>
        <div className="w-16" />
      </div>
      {/* Main Content */}
      <div className="w-full flex flex-col items-center justify-center gap-6 flex-1">
        <div className="flex flex-row items-center justify-center gap-4 w-full flex-wrap max-w-2/3">
          {wordArray.map((word, idx) => {
            return (
              <Badge
                key={idx}
                variant="outline"
                className={`rounded-xl px-4 py-2 text-4xl font-medium`}
              >
                {word}
              </Badge>
            );
          })}
        </div>
        {/* Avatar Mic Character */}
        <div className="flex justify-center">
          <Button
            className="w-24 h-24 not-hover:animate-pulse shadow-inner transition-colors rounded-full hover:bg-fuchsia-200"
            variant="secondary"
          >
            <Mic className="size-10 text-purple-700" />
          </Button>
        </div>
      </div>
    </div>
  );
};

export default UnlimitedPractice;
