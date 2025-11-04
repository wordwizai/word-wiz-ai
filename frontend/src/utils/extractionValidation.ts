/**
 * Validation utilities for client-side extraction (phonemes and words).
 *
 * Provides robust validation to ensure extracted data is reliable before
 * sending to the backend. Helps catch edge cases like:
 * - Empty or malformed extractions
 * - Mismatched word/phoneme counts
 * - Unusual ratios that indicate transcription errors
 * - Silent or noisy audio
 */

export interface ValidationResult {
  isValid: boolean;
  error?: string;
  warning?: string;
}

/**
 * Validate extracted phonemes format and content.
 */
export function validatePhonemes(
  phonemes: string[][] | null
): ValidationResult {
  if (!phonemes) {
    return { isValid: false, error: "Phonemes is null" };
  }

  if (!Array.isArray(phonemes)) {
    return { isValid: false, error: "Phonemes must be an array" };
  }

  if (phonemes.length === 0) {
    return { isValid: false, error: "Phonemes array is empty" };
  }

  // Check each word's phonemes
  for (let i = 0; i < phonemes.length; i++) {
    const wordPhonemes = phonemes[i];

    if (!Array.isArray(wordPhonemes)) {
      return {
        isValid: false,
        error: `Word ${i} phonemes is not an array`,
      };
    }

    if (wordPhonemes.length === 0) {
      return {
        isValid: false,
        error: `Word ${i} has no phonemes`,
      };
    }

    // Check each phoneme is a string
    for (let j = 0; j < wordPhonemes.length; j++) {
      const phoneme = wordPhonemes[j];

      if (typeof phoneme !== "string") {
        return {
          isValid: false,
          error: `Word ${i}, phoneme ${j} is not a string`,
        };
      }

      if (phoneme.length === 0) {
        return {
          isValid: false,
          error: `Word ${i}, phoneme ${j} is empty`,
        };
      }
    }
  }

  return { isValid: true };
}

/**
 * Validate extracted words format and content.
 */
export function validateWords(words: string[] | null): ValidationResult {
  if (!words) {
    return { isValid: false, error: "Words is null" };
  }

  if (!Array.isArray(words)) {
    return { isValid: false, error: "Words must be an array" };
  }

  if (words.length === 0) {
    return { isValid: false, error: "Words array is empty" };
  }

  // Check each word
  for (let i = 0; i < words.length; i++) {
    const word = words[i];

    if (typeof word !== "string") {
      return {
        isValid: false,
        error: `Word ${i} is not a string`,
      };
    }

    if (word.length === 0) {
      return {
        isValid: false,
        error: `Word ${i} is empty`,
      };
    }

    // Check for suspicious patterns
    if (word.length > 50) {
      return {
        isValid: false,
        error: `Word ${i} is suspiciously long (${word.length} chars)`,
      };
    }
  }

  return { isValid: true };
}

/**
 * Validate alignment between words and phonemes.
 */
export function validateAlignment(
  words: string[] | null,
  phonemes: string[][] | null
): ValidationResult {
  // First validate each individually
  const wordsResult = validateWords(words);
  if (!wordsResult.isValid) {
    return wordsResult;
  }

  const phonemesResult = validatePhonemes(phonemes);
  if (!phonemesResult.isValid) {
    return phonemesResult;
  }

  // Check counts match
  if (words!.length !== phonemes!.length) {
    return {
      isValid: false,
      error: `Word count (${words!.length}) doesn't match phoneme count (${
        phonemes!.length
      })`,
    };
  }

  // Check for unusual ratios (potential transcription errors)
  const totalWordChars = words!.join("").length;
  const totalPhonemes = phonemes!.flat().length;
  const ratio = totalWordChars / totalPhonemes;

  if (ratio < 0.3 || ratio > 3.0) {
    return {
      isValid: false,
      error: `Unusual word/phoneme ratio: ${ratio.toFixed(
        2
      )} (expected 0.3-3.0)`,
      warning: "This may indicate a transcription error",
    };
  }

  // All good!
  return { isValid: true };
}

/**
 * Validate extraction results comprehensively.
 * Use this as a final check before sending to backend.
 */
export function validateExtraction(
  words: string[] | null,
  phonemes: string[][] | null
): ValidationResult {
  // If both null, that's OK (server will extract)
  if (!words && !phonemes) {
    return { isValid: true, warning: "No client extraction available" };
  }

  // If only one is null, validate the other
  if (!words) {
    return validatePhonemes(phonemes);
  }

  if (!phonemes) {
    return validateWords(words);
  }

  // Both present - validate alignment
  return validateAlignment(words, phonemes);
}

/**
 * Check if audio might be silent or too noisy.
 * Returns true if audio seems problematic.
 */
export function detectProblematicAudio(
  words: string[] | null,
  phonemes: string[][] | null
): { isSilent: boolean; isTooNoisy: boolean; message?: string } {
  // If we have no extractions, might be silent
  if (!words || words.length === 0) {
    return {
      isSilent: true,
      isTooNoisy: false,
      message: "Audio may be silent or too quiet",
    };
  }

  // If we have very few phonemes compared to words, might be noisy
  if (phonemes) {
    const avgPhonemesPerWord =
      phonemes.flat().length / Math.max(phonemes.length, 1);
    if (avgPhonemesPerWord < 1.5) {
      return {
        isSilent: false,
        isTooNoisy: true,
        message: "Audio may be too noisy or unclear",
      };
    }
  }

  return { isSilent: false, isTooNoisy: false };
}

/**
 * Get a user-friendly error message for validation failures.
 */
export function getValidationErrorMessage(result: ValidationResult): string {
  if (result.isValid) {
    return result.warning || "Validation passed";
  }

  return result.error || "Validation failed";
}
