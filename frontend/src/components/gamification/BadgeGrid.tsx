/**
 * BadgeGrid
 * Renders all badges — earned ones in full colour, locked ones muted/greyscale.
 * Consistent with the app's pastel card style.
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
  { card: string; iconBg: string; iconColor: string; pill: string; pillText: string }
> = {
  common: {
    card: "bg-slate-50 border-slate-200/80",
    iconBg: "bg-slate-100",
    iconColor: "text-slate-500",
    pill: "bg-slate-100",
    pillText: "text-slate-500",
  },
  rare: {
    card: "bg-blue-50 border-blue-200/80",
    iconBg: "bg-blue-100",
    iconColor: "text-blue-500",
    pill: "bg-blue-100",
    pillText: "text-blue-500",
  },
  epic: {
    card: "bg-purple-50 border-purple-200/80",
    iconBg: "bg-purple-100",
    iconColor: "text-purple-500",
    pill: "bg-purple-100",
    pillText: "text-purple-500",
  },
  legendary: {
    card: "bg-amber-50 border-amber-200/80",
    iconBg: "bg-amber-100",
    iconColor: "text-amber-500",
    pill: "bg-amber-100",
    pillText: "text-amber-600",
  },
};

interface BadgeGridProps {
  badges: BadgeWithStatus[];
  earnedOnly?: boolean;
}

export default function BadgeGrid({ badges, earnedOnly = false }: BadgeGridProps) {
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
                    "relative flex flex-col items-center gap-2 p-3 rounded-2xl border-2 cursor-default select-none transition-all duration-200",
                    badge.earned
                      ? cn(cfg.card, "shadow-sm hover:shadow-md hover:-translate-y-0.5")
                      : "bg-muted/30 border-border/50 opacity-40 grayscale"
                  )}
                >
                  {/* Lock indicator */}
                  {!badge.earned && (
                    <Lock className="absolute top-1.5 right-1.5 w-3 h-3 text-muted-foreground/60" />
                  )}

                  {/* Icon */}
                  <div
                    className={cn(
                      "w-11 h-11 rounded-xl flex items-center justify-center",
                      badge.earned ? cfg.iconBg : "bg-muted/50"
                    )}
                  >
                    <DynamicIcon
                      name={badge.icon_name}
                      className={cn(
                        "w-5 h-5",
                        badge.earned ? cfg.iconColor : "text-muted-foreground"
                      )}
                      fallback="Star"
                    />
                  </div>

                  {/* Name */}
                  <span className="text-[10px] font-semibold text-center leading-tight text-foreground line-clamp-2 w-full">
                    {badge.name}
                  </span>

                  {/* Rarity pill */}
                  <span
                    className={cn(
                      "text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded-full",
                      badge.earned ? cn(cfg.pill, cfg.pillText) : "bg-muted text-muted-foreground"
                    )}
                  >
                    {badge.rarity}
                  </span>
                </div>
              </TooltipTrigger>

              <TooltipContent side="top" className="max-w-52 text-center">
                <p className="font-semibold text-white">{badge.name}</p>
                <p className="text-xs text-white/80 mt-0.5">{badge.description}</p>
                <p className="text-xs text-yellow-400 mt-0.5">+{badge.xp_reward} XP</p>
                {badge.earned && badge.earned_at && (
                  <p className="text-xs text-white/60 mt-0.5">
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
