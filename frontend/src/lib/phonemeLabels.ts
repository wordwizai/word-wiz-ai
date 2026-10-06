// How to show an IPA phoneme to a parent: the letters that usually spell it
// and a short word that has it. Matches the letter names the backend uses in
// spoken feedback (_IPA_TO_DISPLAY in core/phoneme_feedback_formatter.py),
// including the bare vowels the wav2vec2-TIMIT model emits. The one
// exception is bare "i": eng_to_ipa and the TIMIT model both use it for the
// long e in "see" (ARPAbet iy), so it is long e here, not short i.
const LABELS: Record<string, { letters: string; example: string }> = {
  θ: { letters: "th", example: "thin" },
  ð: { letters: "th", example: "this" },
  ʃ: { letters: "sh", example: "ship" },
  ʒ: { letters: "zh", example: "measure" },
  tʃ: { letters: "ch", example: "chip" },
  ʧ: { letters: "ch", example: "chip" },
  dʒ: { letters: "j", example: "jump" },
  ʤ: { letters: "j", example: "jump" },
  ŋ: { letters: "ng", example: "sing" },
  j: { letters: "y", example: "yes" },
  ɹ: { letters: "r", example: "red" },
  r: { letters: "r", example: "red" },
  æ: { letters: "short a", example: "cat" },
  a: { letters: "short a", example: "cat" },
  ɑ: { letters: "ah", example: "father" },
  ɑː: { letters: "ah", example: "father" },
  ə: { letters: "uh", example: "about" },
  ɚ: { letters: "er", example: "her" },
  ɝ: { letters: "er", example: "her" },
  ɛ: { letters: "short e", example: "bed" },
  e: { letters: "short e", example: "bed" },
  ɪ: { letters: "short i", example: "sit" },
  i: { letters: "long e", example: "see" },
  iː: { letters: "long e", example: "see" },
  ɔ: { letters: "aw", example: "saw" },
  ɔː: { letters: "aw", example: "saw" },
  ʊ: { letters: "short oo", example: "book" },
  u: { letters: "long oo", example: "moon" },
  uː: { letters: "long oo", example: "moon" },
  ʌ: { letters: "short u", example: "cup" },
  o: { letters: "long o", example: "go" },
  oʊ: { letters: "long o", example: "go" },
  aɪ: { letters: "long i", example: "kite" },
  aʊ: { letters: "ow", example: "cow" },
  eɪ: { letters: "long a", example: "cake" },
  ɔɪ: { letters: "oy", example: "boy" },
  p: { letters: "p", example: "pig" },
  b: { letters: "b", example: "bat" },
  t: { letters: "t", example: "top" },
  d: { letters: "d", example: "dog" },
  k: { letters: "k", example: "kite" },
  g: { letters: "g", example: "go" },
  ɡ: { letters: "g", example: "go" },
  f: { letters: "f", example: "fish" },
  v: { letters: "v", example: "van" },
  s: { letters: "s", example: "sun" },
  z: { letters: "z", example: "zip" },
  h: { letters: "h", example: "hat" },
  m: { letters: "m", example: "map" },
  n: { letters: "n", example: "net" },
  l: { letters: "l", example: "lip" },
  w: { letters: "w", example: "wet" },
};

export function phonemeLabel(ipa: string) {
  return LABELS[ipa] ?? null;
}

const MACRONS: Record<string, string> = { a: "ā", e: "ē", i: "ī", o: "ō" };

// A label short enough for a sound tile. "short a" becomes "a", "long a"
// becomes "ā" (the mark phonics lessons use) and "long oo" stays "oo".
// IPA with no label shows as itself.
export function phonemeTileLabel(ipa: string) {
  const letters = LABELS[ipa]?.letters;
  if (!letters) return ipa;
  if (letters.startsWith("short ")) return letters.slice("short ".length);
  if (letters.startsWith("long ")) {
    const vowel = letters.slice("long ".length);
    return MACRONS[vowel] ?? vowel;
  }
  return letters;
}
