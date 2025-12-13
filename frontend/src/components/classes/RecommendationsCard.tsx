import { Lightbulb } from "lucide-react";

interface RecommendationsCardProps {
  recommendations: string[];
}

const RecommendationsCard = ({ recommendations }: RecommendationsCardProps) => {
  if (recommendations.length === 0) {
    return (
      <div className="text-center text-muted-foreground py-8">
        <Lightbulb className="w-12 h-12 mx-auto mb-2 opacity-50" />
        <p>No recommendations available</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {recommendations.map((recommendation, index) => (
        <div
          key={index}
          className="bg-blue-50 dark:bg-blue-950 rounded-lg p-4 border-l-4 border-blue-500"
        >
          <p className="text-sm text-foreground">{recommendation}</p>
        </div>
      ))}
    </div>
  );
};

export default RecommendationsCard;
