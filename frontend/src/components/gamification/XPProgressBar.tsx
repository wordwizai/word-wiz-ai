/**
 * XPProgressBar
 * Shows the user's current level, XP into the level, and a progress bar.
 * Used in the sidebar / dashboard header.
 */
import { useContext, useEffect, useState } from "react";
import { AuthContext } from "@/contexts/AuthContext";
import { getMyGamification, type UserGamification } from "@/api";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { Zap } from "lucide-react";

interface XPProgressBarProps {
  /** Collapsed = icon-only mode (sidebar is narrow) */
  collapsed?: boolean;
  /** Externally supplied data (e.g. from Dashboard state) */
  data?: UserGamification | null;
  /** Called when data is freshly fetched, so parent can share state */
  onData?: (data: UserGamification) => void;
}

export default function XPProgressBar({
  collapsed = false,
  data: externalData,
  onData,
}: XPProgressBarProps) {
  const { token } = useContext(AuthContext);
  const [gamification, setGamification] = useState<UserGamification | null>(
    externalData ?? null
  );
  const [loading, setLoading] = useState(!externalData);

  useEffect(() => {
    if (externalData) {
      setGamification(externalData);
      setLoading(false);
      return;
    }
    if (!token) return;
    getMyGamification(token)
      .then((d) => {
        setGamification(d);
        onData?.(d);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [token, externalData]);

  if (loading) {
    return collapsed ? (
      <Skeleton className="w-8 h-8 rounded-full" />
    ) : (
      <div className="space-y-1.5 px-1">
        <Skeleton className="h-3 w-24 rounded" />
        <Skeleton className="h-2 w-full rounded" />
      </div>
    );
  }

  if (!gamification) return null;

  const { level, level_name, xp_into_level, xp_needed_for_next, total_xp } =
    gamification;
  const pct =
    xp_needed_for_next > 0
      ? Math.round((xp_into_level / xp_needed_for_next) * 100)
      : 100;

  if (collapsed) {
    return (
      <div
        className="flex flex-col items-center gap-0.5"
        title={`Level ${level} — ${total_xp} XP`}
      >
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary/80 to-purple-400 flex items-center justify-center text-white text-xs font-bold shadow-sm">
          {level}
        </div>
      </div>
    );
  }

  return (
    <div className="px-1 space-y-1">
      <div className="flex items-center justify-between text-xs">
        <span className="font-semibold text-foreground flex items-center gap-1">
          <Zap className="w-3 h-3 text-yellow-500" />
          Lv {level} · {level_name}
        </span>
        <span className="text-muted-foreground tabular-nums">
          {xp_needed_for_next > 0
            ? `${xp_into_level}/${xp_needed_for_next}`
            : "MAX"}
        </span>
      </div>
      <Progress value={pct} className="h-2 rounded-full" />
    </div>
  );
}
