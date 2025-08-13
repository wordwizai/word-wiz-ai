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
    <div className="w-full flex flex-col items-center justify-center gap-6 flex-1">
      {/* Word Row */}
      <WordBadgeRow
        showHighlightedWords={showHighlightedWords}
        wordArray={wordArray}
        analysisData={analysisData}
      />
    </div>
  );
};

export default SentenceDisplay;

