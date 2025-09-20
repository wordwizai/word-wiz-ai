import { FeedbackAnimatedText } from "@/components/FeedbackAnimatedText";
import { Card } from "@/components/ui/card";

interface FeedbackDisplayProps {
  feedback: string | null;
}

const FeedbackDisplay = ({ feedback }: FeedbackDisplayProps) => {
  if (!feedback) return null;
  
  return (
    <Card className="w-full max-w-4xl mx-auto p-6 rounded-3xl bg-gradient-to-br from-white to-green-50/50 border-2 border-green-100/50 shadow-xl backdrop-blur-sm">
      <FeedbackAnimatedText feedback={feedback} />
    </Card>
  );
};

export default FeedbackDisplay;

