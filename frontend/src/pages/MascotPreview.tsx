import { useState } from "react";
import Mascot, { type MascotMood } from "@/components/mascot/Mascot";
import { Button } from "@/components/ui/button";

// Dev-only page for checking and tuning the mascot's moods at the sizes the
// app uses. App.tsx only routes it in development builds.
const MOODS: MascotMood[] = [
  "still",
  "idle",
  "talking",
  "listening",
  "celebrating",
];

export default function MascotPreview() {
  // Celebrating plays once, so remount it to watch it again.
  const [hops, setHops] = useState(0);

  return (
    <main className="min-h-screen bg-background p-6 sm:p-10">
      <div className="mb-8 flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-2xl font-semibold text-foreground">Mascot moods</h1>
        <Button onClick={() => setHops((n) => n + 1)} className="rounded-xl">
          Celebrate again
        </Button>
      </div>

      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-5">
        {MOODS.map((mood) => (
          <section
            key={mood === "celebrating" ? `celebrating-${hops}` : mood}
            className="flex flex-col items-center gap-6 rounded-3xl bg-card p-6 pt-20 ring-1 ring-border"
          >
            <Mascot mood={mood} className="h-36 w-40" />
            <div className="flex items-end gap-4">
              <Mascot mood={mood} className="size-8" />
              <Mascot mood={mood} className="size-9" />
              <Mascot mood={mood} className="size-16" />
            </div>
            <p className="text-sm font-medium text-foreground">{mood}</p>
          </section>
        ))}
      </div>
    </main>
  );
}
