import { AlertTriangle, HelpCircle } from "lucide-react";
import { type PhonemeInsight } from "@/api";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface PhonemeInsightsCardProps {
  insights: PhonemeInsight[];
}

const PhonemeInsightsCard = ({ insights }: PhonemeInsightsCardProps) => {
  const getDifficultyColor = (level?: number) => {
    if (!level) return "bg-gray-200";
    if (level <= 2) return "bg-green-200";
    if (level === 3) return "bg-yellow-200";
    return "bg-orange-200";
  };

  const getDifficultyLabel = (level?: number) => {
    if (!level) return "Unknown";
    if (level <= 2) return "Easy";
    if (level === 3) return "Medium";
    return "Hard";
  };

  if (insights.length === 0) {
    return (
      <div className="text-center text-muted-foreground py-8">
        <AlertTriangle className="w-12 h-12 mx-auto mb-2 opacity-50" />
        <p>No phoneme errors detected</p>
        <p className="text-sm mt-1">This student is doing great!</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {insights.slice(0, 5).map((insight, index) => (
        <div
          key={insight.phoneme}
          className="bg-muted rounded-lg p-4 border-l-4 border-orange-500"
        >
          <div className="flex items-start justify-between mb-2">
            <div className="flex items-center gap-3">
              <div className="text-3xl font-mono font-bold text-foreground">
                /{insight.phoneme}/
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-foreground">
                    {insight.error_count}{" "}
                    {insight.error_count === 1 ? "error" : "errors"}
                  </span>
                  <span
                    className={`text-xs px-2 py-0.5 rounded ${getDifficultyColor(
                      insight.difficulty_level
                    )}`}
                  >
                    {getDifficultyLabel(insight.difficulty_level)}
                  </span>
                </div>
                {index === 0 && (
                  <span className="text-xs text-orange-600 font-medium">
                    🎯 Primary Focus
                  </span>
                )}
              </div>
            </div>

            {insight.description && (
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger>
                    <HelpCircle className="w-4 h-4 text-muted-foreground" />
                  </TooltipTrigger>
                  <TooltipContent className="max-w-xs">
                    <p className="text-sm">{insight.description}</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            )}
          </div>

          {insight.description && (
            <p className="text-sm text-muted-foreground mt-2">
              💡 {insight.description}
            </p>
          )}
        </div>
      ))}
    </div>
  );
};

export default PhonemeInsightsCard;
