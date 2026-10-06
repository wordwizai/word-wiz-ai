// Accuracy chips use the pastel pairs because those have dark-mode values.
// Tailwind's green-100/green-800 stay light on a dark page.
export const ACCURACY_TONE = {
  good: "bg-pastel-mint text-pastel-mint-foreground",
  fair: "bg-pastel-yellow text-pastel-yellow-foreground",
  low: "bg-pastel-coral text-pastel-coral-foreground",
  none: "bg-muted text-muted-foreground",
} as const;

export type AccuracyTone = keyof typeof ACCURACY_TONE;

// average_per is a phoneme error rate, so 0.1 is 90% accurate. A rate of 0
// means no readings yet rather than a perfect score.
export function perTone(per: number): AccuracyTone {
  if (per <= 0) return "none";
  if (per < 0.1) return "good";
  if (per < 0.2) return "fair";
  return "low";
}

export function perAccuracyLabel(per: number) {
  return per > 0 ? `${((1 - per) * 100).toFixed(1)}%` : "N/A";
}
