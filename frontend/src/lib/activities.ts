import { format, isToday, isYesterday } from "date-fns";

// Each activity keeps the same pastel everywhere it appears, picked by
// `id % 9` in this order (see the Word Wiz design system, Colour).
const PASTELS = [
  "pastel-blue",
  "pastel-mint",
  "pastel-peach",
  "pastel-purple",
  "pastel-pink",
  "pastel-lavender",
  "pastel-yellow",
  "pastel-coral",
  "pastel-teal",
] as const;

export function activityPastel(id: number) {
  const name = PASTELS[Math.abs(id) % PASTELS.length];
  return {
    background: `var(--${name})`,
    foreground: `var(--${name}-foreground)`,
  };
}

const TYPE_LABELS: Record<string, string> = {
  unlimited: "Free practice",
  story: "Story",
  "choice-story": "Choice story",
  "phonics-pattern": "Phonics path",
};

export function activityTypeLabel(type: string | undefined) {
  if (!type) return "Practice";
  return TYPE_LABELS[type] ?? type.charAt(0).toUpperCase() + type.slice(1);
}

// The API stores UTC but serialises it without a zone ("2026-10-06T02:40:19"),
// which `new Date` would read as local time and shift by the UTC offset.
export function parseServerDate(value: string) {
  const hasZone = /(Z|[+-]\d{2}:?\d{2})$/.test(value);
  return new Date(hasZone ? value : `${value}Z`);
}

export function friendlyDate(value: string) {
  const date = parseServerDate(value);
  if (isToday(date)) return "Today";
  if (isYesterday(date)) return "Yesterday";
  return format(date, "MMM d");
}

export interface Activity {
  id: number;
  title: string;
  description: string;
  emoji_icon: string;
  activity_type: string;
  activity_settings: Record<string, unknown>;
}

// mulberry32: a small seeded generator, so everyone sees the same picks on
// a given day and the picks change at midnight.
const seededRandom = (seed: number) => {
  let t = seed + 0x6d2b79f5;
  t = Math.imul(t ^ (t >>> 15), t | 1);
  t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
};

const CHOICE_STORY_SEED_OFFSET = 1000;

// Today's three picks: the first free-practice activity, then one story and
// one choice story chosen by the date.
export function pickDailyActivities(activities: Activity[], now = new Date()) {
  const daySeed =
    now.getFullYear() * 10000 + (now.getMonth() + 1) * 100 + now.getDate();
  const ofType = (type: string) =>
    activities.filter((a) => a.activity_type === type);
  const pickOne = (list: Activity[], seed: number) =>
    list.length > 0
      ? list[Math.floor(seededRandom(seed) * list.length)]
      : undefined;

  return [
    ofType("unlimited")[0],
    pickOne(ofType("story"), daySeed),
    pickOne(ofType("choice-story"), daySeed + CHOICE_STORY_SEED_OFFSET),
  ].filter((a): a is Activity => a !== undefined);
}
