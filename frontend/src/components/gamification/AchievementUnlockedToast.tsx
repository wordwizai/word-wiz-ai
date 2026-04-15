/**
 * AchievementUnlockedToast
 * Full-screen celebration overlay that fires when a new badge is earned.
 * Shows for ~3 seconds then auto-dismisses, with a manual close button.
 */
import { useEffect, useState } from "react";
import { type NewlyEarnedBadge, type AchievementRarity } from "@/api";
import DynamicIcon from "@/components/DynamicIcon";
import { cn } from "@/lib/utils";
import { X } from "lucide-react";
import { Button } from "@/components/ui/button";

const rarityGradient: Record<AchievementRarity, string> = {
  common: "from-slate-400 to-slate-600",
  rare: "from-blue-400 to-blue-700",
  epic: "from-purple-400 to-purple-700",
  legendary: "from-amber-400 to-orange-600",
};

interface AchievementUnlockedToastProps {
  badge: NewlyEarnedBadge;
  xpEarned: number;
  onClose: () => void;
}

export default function AchievementUnlockedToast({
  badge,
  xpEarned,
  onClose,
}: AchievementUnlockedToastProps) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    // Mount → animate in
    const t1 = setTimeout(() => setVisible(true), 50);
    // Auto-dismiss after 4 s
    const t2 = setTimeout(() => {
      setVisible(false);
      setTimeout(onClose, 300);
    }, 4000);
    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
    };
  }, [onClose]);

  const gradient = rarityGradient[badge.rarity];

  return (
    <div
      className={cn(
        "fixed inset-0 z-[9999] flex items-center justify-center pointer-events-none transition-all duration-300",
        visible ? "opacity-100" : "opacity-0"
      )}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" />

      {/* Card */}
      <div
        className={cn(
          "pointer-events-auto relative flex flex-col items-center gap-4 rounded-3xl p-8 shadow-2xl max-w-xs w-full mx-4 text-white",
          "bg-gradient-to-br",
          gradient,
          "transition-transform duration-300",
          visible ? "scale-100" : "scale-90"
        )}
      >
        <Button
          variant="ghost"
          size="icon"
          className="absolute top-3 right-3 text-white/70 hover:text-white hover:bg-white/10 w-8 h-8"
          onClick={() => {
            setVisible(false);
            setTimeout(onClose, 300);
          }}
        >
          <X className="w-4 h-4" />
        </Button>

        {/* Sparkle ring */}
        <div className="relative">
          <div className="absolute inset-0 rounded-full bg-white/20 blur-xl animate-pulse" />
          <div className="relative w-20 h-20 rounded-full bg-white/20 border-4 border-white/40 flex items-center justify-center">
            <DynamicIcon
              name={badge.icon_name}
              className="w-9 h-9 text-white"
              fallback="Star"
            />
          </div>
        </div>

        <div className="text-center space-y-1">
          <p className="text-xs font-bold uppercase tracking-widest text-white/70">
            Achievement Unlocked!
          </p>
          <h2 className="text-2xl font-black">{badge.name}</h2>
          <p className="text-sm text-white/80">{badge.description}</p>
        </div>

        <div className="flex items-center gap-2 bg-white/20 rounded-full px-4 py-1.5 text-sm font-bold">
          ⚡ +{badge.xp_reward} XP
        </div>

        <p className="text-xs text-white/60 capitalize">{badge.rarity} badge</p>
      </div>
    </div>
  );
}
