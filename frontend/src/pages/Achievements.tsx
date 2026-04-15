import { useContext, useEffect, useState } from "react";
import { AuthContext } from "@/contexts/AuthContext";
import {
  getMyBadges,
  getMyGamification,
  type BadgeWithStatus,
  type UserGamification,
} from "@/api";
import BadgeGrid from "@/components/gamification/BadgeGrid";
import XPProgressBar from "@/components/gamification/XPProgressBar";
import StreakFreezeWidget from "@/components/gamification/StreakFreezeWidget";
import { Skeleton } from "@/components/ui/skeleton";
import { Trophy, Zap, Filter } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type FilterType = "all" | "earned" | "common" | "rare" | "epic" | "legendary";

const Achievements = () => {
  const { token } = useContext(AuthContext);
  const [badges, setBadges] = useState<BadgeWithStatus[]>([]);
  const [gamification, setGamification] = useState<UserGamification | null>(
    null
  );
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<FilterType>("all");

  useEffect(() => {
    if (!token) return;
    Promise.all([getMyBadges(token), getMyGamification(token)])
      .then(([b, g]) => {
        setBadges(b);
        setGamification(g);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [token]);

  const filtered = badges.filter((b) => {
    if (filter === "earned") return b.earned;
    if (filter === "all") return true;
    return b.rarity === filter;
  });

  const earnedCount = badges.filter((b) => b.earned).length;

  const filterButtons: { label: string; value: FilterType }[] = [
    { label: "All", value: "all" },
    { label: "Earned", value: "earned" },
    { label: "Common", value: "common" },
    { label: "Rare", value: "rare" },
    { label: "Epic", value: "epic" },
    { label: "Legendary", value: "legendary" },
  ];

  return (
    <main className="flex-1 p-4 sm:p-6 bg-background space-y-6 overflow-y-auto flex flex-col min-h-0 h-full">
      {/* Hero */}
      <div className="relative rounded-2xl overflow-hidden bg-gradient-to-br from-amber-500/10 via-primary/5 to-purple-500/10 border border-amber-500/20 p-6">
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-10 -right-10 w-40 h-40 bg-amber-500/10 rounded-full blur-3xl" />
          <Trophy className="absolute top-4 right-16 w-8 h-8 text-amber-500/15 rotate-12" />
          <Zap className="absolute bottom-4 right-8 w-6 h-6 text-primary/10" />
        </div>
        <div className="relative z-10 flex items-center gap-5">
          <div className="hidden sm:flex shrink-0">
            <div className="relative w-16 h-16">
              <div className="absolute inset-0 bg-gradient-to-br from-amber-500/20 to-orange-500/20 rounded-2xl rotate-6" />
              <div className="absolute inset-0 flex items-center justify-center">
                <Trophy className="w-8 h-8 text-amber-600" />
              </div>
            </div>
          </div>
          <div>
            <p className="text-xs text-muted-foreground font-medium uppercase tracking-wide mb-1">
              Achievements
            </p>
            <h1 className="text-2xl md:text-3xl font-bold bg-gradient-to-r from-amber-600 via-primary to-purple-600 bg-clip-text text-transparent">
              Your Badges
            </h1>
            <p className="text-sm text-muted-foreground mt-1">
              {loading
                ? "Loading..."
                : `${earnedCount} of ${badges.length} badges earned`}
            </p>
          </div>
        </div>
      </div>

      {/* XP + Freezes row */}
      {gamification && (
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="flex-1 bg-card rounded-2xl border border-border p-4 space-y-3">
            <div className="flex items-center gap-2 mb-1">
              <div className="w-7 h-7 rounded-full bg-gradient-to-br from-primary/80 to-purple-500 flex items-center justify-center text-white text-xs font-black">
                {gamification.level}
              </div>
              <span className="text-sm font-bold text-foreground">
                {gamification.level_name}
              </span>
              <span className="ml-auto text-xs text-muted-foreground">
                {gamification.total_xp} XP total
              </span>
            </div>
            <XPProgressBar data={gamification} />
          </div>
          <div className="sm:w-72">
            <StreakFreezeWidget
              freezesAvailable={gamification.streak_freezes_available}
              onUsed={(n) =>
                setGamification((g) =>
                  g ? { ...g, streak_freezes_available: n } : g
                )
              }
            />
          </div>
        </div>
      )}

      {/* Filter bar */}
      <div className="flex items-center gap-2 flex-wrap">
        <Filter className="w-4 h-4 text-muted-foreground" />
        {filterButtons.map((fb) => (
          <Button
            key={fb.value}
            variant="outline"
            size="sm"
            className={cn(
              "h-7 text-xs rounded-full px-3",
              filter === fb.value &&
                "bg-primary text-primary-foreground border-primary"
            )}
            onClick={() => setFilter(fb.value)}
          >
            {fb.label}
            {fb.value === "earned" && !loading && (
              <span className="ml-1 text-[10px] opacity-70">
                ({earnedCount})
              </span>
            )}
          </Button>
        ))}
      </div>

      {/* Badge grid */}
      {loading ? (
        <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 gap-3">
          {Array.from({ length: 12 }).map((_, i) => (
            <Skeleton key={i} className="h-24 rounded-2xl" />
          ))}
        </div>
      ) : (
        <BadgeGrid badges={filtered} />
      )}
    </main>
  );
};

export default Achievements;
