import { AnimatePresence, motion } from "framer-motion";
import { WordBadge } from "./WordBadge";

interface WordBadgeRowProps {
  showHighlightedWords: boolean;
  analysisData?: {
    pronunciation_dataframe: {
      type: Record<number, string>;
      per: Record<number, number | null>;
      ground_truth_word: Record<number, string | null>;
      predicted_word: Record<number, string | null>;
      graphemes?: Record<number, string[]>;
      grapheme_errors?: Record<number, Record<number, any>>;
    };
  } | null;
  wordArray: string[];
}

const WordBadgeRow = ({
  showHighlightedWords,
  analysisData,
  wordArray,
}: WordBadgeRowProps & {}) => {
  const formatWord = (word: string | null | undefined) => {
    // Handle null/undefined values (e.g., insertions/deletions)
    if (!word) return "";
    // Format the word to remove any special characters or spaces
    return word.replace(/[^a-zA-Z]/g, "").toLowerCase();
  };

  // Build a map of ground truth words to their indices (handling duplicates)
  const buildWordIndexMap = () => {
    const wordIndexMap: Map<string, number[]> = new Map();

    if (!analysisData?.pronunciation_dataframe.ground_truth_word) {
      return wordIndexMap;
    }

    // The dataframe is converted to dict format: {0: value1, 1: value2, ...}
    const groundTruthWords = analysisData.pronunciation_dataframe
      .ground_truth_word as any;

    // Convert object to array of [index, value] pairs
    Object.entries(groundTruthWords).forEach(([idx, word]) => {
      if (word === null) return; // Skip null (deletions)

      const formattedWord = formatWord(word as string);
      const index = parseInt(idx);

      if (!wordIndexMap.has(formattedWord)) {
        wordIndexMap.set(formattedWord, []);
      }
      wordIndexMap.get(formattedWord)!.push(index);
    });

    return wordIndexMap;
  };

  // Build display array including insertions
  const buildDisplayArray = () => {
    if (!analysisData) {
      // No analysis data, just show the original words
      return wordArray.map((word, idx) => ({
        word,
        originalIdx: idx,
        analysisIdx: null,
        per: null,
        isInsertion: false,
        isDeletion: false,
      }));
    }

    const wordIndexMap = buildWordIndexMap();
    const usedIndices = new Set<number>();
    const displayArray: Array<{
      word: string;
      originalIdx: number;
      analysisIdx: number | null;
      per: number | null;
      isInsertion: boolean;
      isDeletion: boolean;
    }> = [];

    // First, map ground truth words to their analysis data
    wordArray.forEach((word, idx) => {
      const formattedWord = formatWord(word);
      const availableIndices = wordIndexMap.get(formattedWord) || [];

      // Find the first unused index for this word
      const analysisIdx = availableIndices.find((i) => !usedIndices.has(i));

      if (analysisIdx !== undefined) {
        usedIndices.add(analysisIdx);
        const errorType =
          analysisData.pronunciation_dataframe.type[analysisIdx];
        displayArray.push({
          word,
          originalIdx: idx,
          analysisIdx,
          per: analysisData.pronunciation_dataframe.per[analysisIdx] ?? null,
          isInsertion: false,
          isDeletion: errorType === "deletion", // Word was not spoken
        });
      } else {
        // Word not found in analysis (shouldn't happen normally)
        displayArray.push({
          word,
          originalIdx: idx,
          analysisIdx: null,
          per: null,
          isInsertion: false,
          isDeletion: false,
        });
      }
    });

    // Now add any insertion words (extra words spoken)
    if (analysisData.pronunciation_dataframe.type) {
      Object.entries(analysisData.pronunciation_dataframe.type).forEach(
        ([idxStr, type]) => {
          if (type === "insertion") {
            const idx = parseInt(idxStr);
            const insertedWord =
              analysisData.pronunciation_dataframe.predicted_word[idx];
            if (insertedWord) {
              displayArray.push({
                word: insertedWord,
                originalIdx: -1, // Special marker for insertions
                analysisIdx: idx,
                per: null, // Insertions don't have PER
                isInsertion: true,
                isDeletion: false,
              });
            }
          }
        }
      );
    }

    // Sort by analysisIdx to position insertions where they were actually spoken
    displayArray.sort((a, b) => {
      const aIdx = a.analysisIdx ?? Infinity;
      const bIdx = b.analysisIdx ?? Infinity;
      return aIdx - bIdx;
    });

    return displayArray;
  };

  const displayArray = buildDisplayArray();

  return (
    <motion.div
      className="flex flex-row items-center justify-center gap-2 md:gap-4 flex-wrap w-full md:max-w-2/3"
      layout
    >
      <AnimatePresence>
        {displayArray.map((item, displayIdx) => {
          return (
            <WordBadge
              word={item.word}
              idx={item.originalIdx >= 0 ? item.originalIdx : displayIdx}
              showHighlighted={
                showHighlightedWords && !item.isInsertion && !item.isDeletion
              }
              analysisPer={item.per ?? undefined}
              isInsertion={item.isInsertion}
              isDeletion={item.isDeletion}
              graphemes={
                item.analysisIdx !== null
                  ? analysisData?.pronunciation_dataframe.graphemes?.[item.analysisIdx]
                  : undefined
              }
              graphemeErrors={
                item.analysisIdx !== null
                  ? analysisData?.pronunciation_dataframe.grapheme_errors?.[item.analysisIdx]
                  : undefined
              }
              key={`${item.word}-${item.analysisIdx ?? displayIdx}`}
            />
          );
        })}
      </AnimatePresence>
    </motion.div>
  );
};

export default WordBadgeRow;
