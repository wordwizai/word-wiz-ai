import WordBadgeRow from "@/components/WordBadgeRow";

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
    <WordBadgeRow
      showHighlightedWords={showHighlightedWords}
      wordArray={wordArray}
      analysisData={analysisData}
    />
  );
};

export default SentenceDisplay;
