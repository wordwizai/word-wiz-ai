import type { PhonemeOp } from "@/components/practice/types";

// eng_to_ipa and the TIMIT model both write these vowels as two symbols
// ("cake" is k e ɪ k), and the backend scores them that way. A child hears
// one sound, so the tiles show one.
const DIPHTHONGS = new Set(["eɪ", "aɪ", "oʊ", "aʊ", "ɔɪ"]);

const soundOf = (op: PhonemeOp) =>
  (op.type === "insertion" ? op.actual : op.expected) ?? "";

const join = (a: string | null, b: string | null) =>
  a === null && b === null ? null : (a ?? "") + (b ?? "");

// Join each split diphthong into one op. When its two halves disagree, half
// the vowel was wrong, so the joined sound counts as a different sound. An
// added sound never joins an expected one.
export function mergeDiphthongs(ops: PhonemeOp[]): PhonemeOp[] {
  const merged: PhonemeOp[] = [];
  for (let i = 0; i < ops.length; i++) {
    const first = ops[i];
    const second = ops[i + 1];
    if (
      second &&
      (first.type === "insertion") === (second.type === "insertion") &&
      DIPHTHONGS.has(soundOf(first) + soundOf(second))
    ) {
      merged.push({
        type: first.type === second.type ? first.type : "substitution",
        expected: join(first.expected, second.expected),
        actual: join(first.actual, second.actual),
      });
      i++;
    } else {
      merged.push(first);
    }
  }
  return merged;
}
