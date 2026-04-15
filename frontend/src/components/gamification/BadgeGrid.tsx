/**
 * BadgeGrid
 * Renders all badges — earned ones in full colour, locked ones grayscale.
 * Used on the Achievements page and in the ProgressDashboard.
 */
import { type BadgeWithStatus, type AchievementRarity } from "@/api";
import DynamicIcon from "@/components/DynamicIcon";
import { cn } from "@/lib/utils";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Lock } from "lucide-react";

const rarityConfig: Record<
  AchievementRarity,
  { bg: string; border: string; label: string }
> = {
  common: {
    bg: "bg-slate-100 dark:bg-slate-800",
    border: "border-slate-200 dark:border-slate-700",
    label: "text-slate-600 dark:text-slate-400",
  },
  rare: {
    bg: "bg-blue-50 dark:bg-blue-900/30",
    border: "border-blue-200 dark:border-blue-700",
    label: "text-blue-600 dark:text-blue-400",
  },
  epic: {
    bg: "bg-purple-50 dark:bg-purple-900/30",
    border: "border-purple-200 dark:border-purple-700",
    label: "text-purple-600 dark:text-purple-400",
  },
  legendary: {
    bg: "bg-amber-50 dark:bg-amber-900/30",
    border: "border-amber-200 dark:border-amber-600",
    label: "text-amber-600 dark:text-amber-400",
  },
};

interface BadgeGridProps {
  badges: BadgeWithStatus[];
  /** If true, show only earned badges */
  earnedOnly?: boolean;
}

export default function BadgeGrid({
  badges,
  earnedOnly = false,
}: BadgeGridProps) {
  const displayed = earnedOnly ? badges.filter((b) => b.earned) : badges;

  if (displayed.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground text-sm">
        No badges yet — keep practicing!
      </div>
    );
  }

  return (
    <TooltipProvider>
      <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 gap-3">
        {displayed.map((badge) => {
          const cfg = rarityConfig[badge.rarity];
          return (
            <Tooltip key={badge.key}>
              <TooltipTrigger asChild>
                <div
                  className={cn(
                    "relative flex flex-col items-center gap-1.5 p-3 rounded-2xl border-2 cursor-default transition-all duration-200",
                    cfg.bg,
                    cfg.border,
                    badge.earned
                      ? "shadow-sm hover:shadow-md hover:-translate-y-0.5"
                      : "opacity-40 grayscale"
                  )}
                >
                  {!badge.earned && (
                    <Lock className="absolute top-1.5 right-1.5 w-3 h-3 text-muted-foreground" />
                  )}
                  <div
                    className={cn(
                      "w-10 h-10 rounded-xl flex items-center justify-center",
                      badge.earned
                        ? "bg-white/70 dark:bg-black/20"
                        : "bg-white/40 dark:bg-black/10"
                    )}
                  >
                    <DynamicIcon
                      name={badge.icon_name}
                      className={cn(
                        "w-5 h-5",
                        badge.earned ? cfg.label : "text-muted-foreground"
                      )}
                      fallback="Star"
                    />
                  </div>
                  <span className="text-[10px] font-semibold text-center leading-tight text-foreground line-clamp-2">
                    {badge.name}
                  </span>
                  <span
                    className={cn(
                      "text-[9px] font-medium uppercase tracking-wide",
                      cfg.label
                    )}
                  >
                    {badge.rarity}
                  </span>
                </div>
              </TooltipTrigger>
              <TooltipContent side="top" className="max-w-52 text-center">
                <p className="font-semibold">{badge.name}</p>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {badge.description}
                </p>
                <p className="text-xs text-yellow-500 mt-0.5">
                  +{badge.xp_reward} XP
                </p>
                {badge.earned && badge.earned_at && (
                  <p className="text-xs text-muted-foreground mt-0.5">
                    Earned {new Date(badge.earned_at).toLocaleDateString()}
                  </p>
                )}
              </TooltipContent>
            </Tooltip>
          );
        })}
      </div>
    </TooltipProvider>
  );
}
