import WordBadgeRow from "@/components/WordBadgeRow";
import { Card } from "@/components/ui/card";

interface SentenceDisplayProps {
  wordArray: string[];
  showHighlightedWords: boolean;
  analysisData: {
    pronunciation_dataframe: { per: number[]; ground_truth_word: string[] };
  } | null;
}

const SentenceDisplay = ({
  wordArray,
  showHighlightedWords,
  analysisData,
}: SentenceDisplayProps) => {
  return (
    <Card className="w-full max-w-4xl mx-auto p-6 rounded-3xl bg-gradient-to-br from-white to-purple-50/50 border-2 border-purple-100/50 shadow-xl backdrop-blur-sm">
      <WordBadgeRow
        showHighlightedWords={showHighlightedWords}
        wordArray={wordArray}
        analysisData={analysisData}
      />
    </Card>
  );
};

export default SentenceDisplay;
