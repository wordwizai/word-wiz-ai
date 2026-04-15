/**
 * StreakFreezeWidget
 * Shows available streak freezes with a "Use Freeze" button.
 * Displayed in Dashboard and as a login-day prompt when streak is at risk.
 */
import { useContext, useState } from "react";
import { AuthContext } from "@/contexts/AuthContext";
import { useStreakFreeze } from "@/api";
import { Button } from "@/components/ui/button";
import { Snowflake, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

interface StreakFreezeWidgetProps {
  freezesAvailable: number;
  /** Called after a successful freeze use so parent can refresh state */
  onUsed?: (newCount: number) => void;
  /** Compact inline display vs full card */
  compact?: boolean;
}

export default function StreakFreezeWidget({
  freezesAvailable,
  onUsed,
  compact = false,
}: StreakFreezeWidgetProps) {
  const { token } = useContext(AuthContext);
  const [using, setUsing] = useState(false);
  const [count, setCount] = useState(freezesAvailable);

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

  if (compact) {
    return (
      <div className="flex items-center gap-2 text-sm">
        {Array.from({ length: 3 }).map((_, i) => (
          <Snowflake
            key={i}
            className={cn(
              "w-4 h-4 transition-colors",
              i < count ? "text-blue-400" : "text-muted-foreground/30"
            )}
          />
        ))}
        <span className="text-muted-foreground text-xs">{count}/3 freezes</span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-3 rounded-xl bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 p-3">
      <div className="flex gap-1">
        {Array.from({ length: 3 }).map((_, i) => (
          <Snowflake
            key={i}
            className={cn(
              "w-5 h-5 transition-colors",
              i < count ? "text-blue-400" : "text-muted-foreground/30"
            )}
          />
        ))}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-semibold text-foreground">Streak Freezes</p>
        <p className="text-xs text-muted-foreground">{count} of 3 available</p>
      </div>
      {count > 0 && (
        <Button
          size="sm"
          variant="outline"
          className="text-blue-600 border-blue-300 hover:bg-blue-50 text-xs h-8 px-3"
          onClick={handleUse}
          disabled={using}
        >
          {using ? <Loader2 className="w-3 h-3 animate-spin" /> : "Use"}
        </Button>
      )}
    </div>
  );
}
