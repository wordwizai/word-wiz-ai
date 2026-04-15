/**
 * LevelUpScreen
 * Celebratory modal shown when the user levels up mid-session.
 * Auto-dismisses after 4 s.
 */
import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Zap, X } from "lucide-react";

interface LevelUpScreenProps {
  level: number;
  levelName: string;
  onClose: () => void;
}

export default function LevelUpScreen({
  level,
  levelName,
  onClose,
}: LevelUpScreenProps) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const t1 = setTimeout(() => setVisible(true), 50);
    const t2 = setTimeout(() => {
      setVisible(false);
      setTimeout(onClose, 300);
    }, 4500);
    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
    };
  }, [onClose]);

  return (
    <div
      className={cn(
        "fixed inset-0 z-[9998] flex items-center justify-center transition-all duration-300",
        visible ? "opacity-100" : "opacity-0"
      )}
    >
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" />

      <div
        className={cn(
          "pointer-events-auto relative flex flex-col items-center gap-5 rounded-3xl p-10 shadow-2xl max-w-sm w-full mx-4",
          "bg-gradient-to-br from-primary via-primary/90 to-purple-600 text-white",
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

        {/* Level badge */}
        <div className="relative">
          <div className="absolute inset-0 rounded-full bg-white/30 blur-2xl animate-ping" />
          <div className="relative w-24 h-24 rounded-full bg-white/20 border-4 border-white/50 flex items-center justify-center">
            <span className="text-4xl font-black">{level}</span>
          </div>
        </div>

        <div className="text-center space-y-1.5">
          <p className="text-xs font-bold uppercase tracking-widest text-white/70">
            Level Up!
          </p>
          <h2 className="text-3xl font-black">{levelName}</h2>
          <p className="text-sm text-white/80">
            You're on a roll — keep reading! 🎉
          </p>
        </div>

        <div className="flex items-center gap-2 bg-white/20 rounded-full px-5 py-2 text-sm font-bold">
          <Zap className="w-4 h-4 text-yellow-300" />
          Level {level} reached
        </div>
      </div>
    </div>
  );
}
