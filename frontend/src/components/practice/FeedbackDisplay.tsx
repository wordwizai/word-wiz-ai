import { FeedbackAnimatedText } from "@/components/FeedbackAnimatedText";

interface FeedbackDisplayProps {
  feedback: string | null;
}

const FeedbackDisplay = ({ feedback }: FeedbackDisplayProps) => {
  return <FeedbackAnimatedText feedback={feedback} />;
};

export default FeedbackDisplay;

