import { AnimatePresence, motion } from "framer-motion";
import { WordBadge } from "./WordBadge";

interface WordBadgeRowProps {
  showHighlightedWords: boolean;
  analysisData?: {
    pronunciation_dataframe: {
      per: number[];
      ground_truth_word: string[];
    };
  } | null;
  wordArray: string[];
}

const WordBadgeRow = ({
  showHighlightedWords,
  analysisData,
  wordArray,
}: WordBadgeRowProps & {}) => {
  return (
    <motion.div
      className="flex flex-row items-center justify-center gap-4 w-full flex-wrap max-w-2/3"
      layout
    >
      <AnimatePresence>
        {wordArray.map((word, idx) => {
          return (
            <WordBadge
              word={word}
              idx={idx}
              showHighlighted={showHighlightedWords}
              analysisPer={
                analysisData?.pronunciation_dataframe.per[
                  Object.values(
                    analysisData?.pronunciation_dataframe.ground_truth_word ||
                      [],
                  ).indexOf(word)
                ]
              }
              key={word + idx}
            />
          );
        })}
      </AnimatePresence>
    </motion.div>
  );
};

export default WordBadgeRow;
