/**
 * StreakFreezeWidget
 * Shows available streak freezes with a "Use Freeze" button.
 * When empty, explains how to earn more rather than showing dead grey icons.
 */
import { useContext, useEffect, useState } from "react";
import { AuthContext } from "@/contexts/AuthContext";
import { useStreakFreeze } from "@/api";
import { Button } from "@/components/ui/button";
import { Snowflake, Loader2, Info } from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface StreakFreezeWidgetProps {
  freezesAvailable: number;
  /** Called after a successful freeze use so parent can refresh state */
  onUsed?: (newCount: number) => void;
  /** Compact inline display (used inside other cards) */
  compact?: boolean;
}

export default function StreakFreezeWidget({
  freezesAvailable,
  onUsed,
  compact = false,
}: StreakFreezeWidgetProps) {
  const { token } = useContext(AuthContext);
  const [using, setUsing] = useState(false);
  // Sync with parent prop — fixes the stale-state bug where the widget
  // wouldn't update when the parent refreshed gamification data.
  const [count, setCount] = useState(freezesAvailable);
  useEffect(() => {
    setCount(freezesAvailable);
  }, [freezesAvailable]);

  const handleUse = async () => {
    if (!token || count <= 0) return;
    setUsing(true);
    try {
      const result = await useStreakFreeze(token);
      setCount(result.streak_freezes_remaining);
      onUsed?.(result.streak_freezes_remaining);
      toast.success("❄️ Streak freeze used!", {
        description: "Your streak is safe for today.",
      });
    } catch {
      toast.error("Couldn't use streak freeze", {
        description: "Please try again.",
      });
    } finally {
      setUsing(false);
    }
  };

  const earnHint = "Practice 7 days in a row to earn a freeze (max 3).";

  // ── Compact mode: just snowflake dots + count, no card chrome ──
  if (compact) {
    return (
      <TooltipProvider>
        <div className="flex items-center gap-1.5">
          {Array.from({ length: 3 }).map((_, i) => (
            <Snowflake
              key={i}
              className={cn(
                "w-4 h-4 transition-colors",
                i < count ? "text-blue-400" : "text-muted-foreground/25"
              )}
            />
          ))}
          <span className="text-xs text-muted-foreground ml-0.5">
            {count}/3
          </span>
          {count === 0 && (
            <Tooltip>
              <TooltipTrigger asChild>
                <Info className="w-3 h-3 text-muted-foreground/50 cursor-help" />
              </TooltipTrigger>
              <TooltipContent side="top" className="max-w-48 text-center text-xs">
                {earnHint}
              </TooltipContent>
            </Tooltip>
          )}
        </div>
      </TooltipProvider>
    );
  }

  // ── Full card mode ──
  return (
    <TooltipProvider>
      <div
        className={cn(
          "flex items-center gap-3 rounded-xl p-3 border transition-colors",
          count > 0
            ? "bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800"
            : "bg-muted/40 border-border"
        )}
      >
        {/* Snowflake indicators */}
        <div className="flex gap-1 shrink-0">
          {Array.from({ length: 3 }).map((_, i) => (
            <Snowflake
              key={i}
              className={cn(
                "w-5 h-5 transition-colors",
                i < count ? "text-blue-400" : "text-muted-foreground/25"
              )}
            />
          ))}
        </div>

        {/* Label + status */}
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-foreground leading-tight">
            Streak Freezes
          </p>
          {count > 0 ? (
            <p className="text-xs text-muted-foreground">
              {count} of 3 available
            </p>
          ) : (
            <p className="text-xs text-muted-foreground leading-snug">
              Earn one by practicing 7&nbsp;days in a&nbsp;row
            </p>
          )}
        </div>

        {/* Action */}
        {count > 0 ? (
          <Button
            size="sm"
            variant="outline"
            className="text-blue-600 border-blue-300 hover:bg-blue-100 dark:hover:bg-blue-900/40 text-xs h-8 px-3 shrink-0"
            onClick={handleUse}
            disabled={using}
          >
            {using ? <Loader2 className="w-3 h-3 animate-spin" /> : "Use"}
          </Button>
        ) : (
          <Tooltip>
            <TooltipTrigger asChild>
              <Info className="w-4 h-4 text-muted-foreground/40 shrink-0 cursor-help" />
            </TooltipTrigger>
            <TooltipContent side="left" className="max-w-52 text-xs text-center">
              {earnHint}
            </TooltipContent>
          </Tooltip>
        )}
      </div>
    </TooltipProvider>
  );
}
