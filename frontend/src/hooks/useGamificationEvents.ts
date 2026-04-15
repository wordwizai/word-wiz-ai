/**
 * useGamificationEvents
 * A hook that takes a GamificationUpdate payload (received from the SSE stream)
 * and queues badge toasts + level-up screens.
 *
 * Usage:
 *   const { pendingBadge, pendingLevelUp, dismissBadge, dismissLevelUp } = useGamificationEvents();
 *   // then in the SSE onmessage handler:
 *   if (event.type === "gamification_update") handleUpdate(event.data);
 */
import { useState, useCallback } from "react";
import { type GamificationUpdate, type NewlyEarnedBadge } from "@/api";

export interface GamificationEventState {
  /** Current badge to celebrate, or null */
  pendingBadge: (NewlyEarnedBadge & { xpEarned: number }) | null;
  /** If truthy, show the level-up screen with this data */
  pendingLevelUp: { level: number; levelName: string } | null;
  /** Call when the badge toast is dismissed */
  dismissBadge: () => void;
  /** Call when the level-up screen is dismissed */
  dismissLevelUp: () => void;
  /** Feed a GamificationUpdate into the event queue */
  handleUpdate: (update: GamificationUpdate) => void;
}

export function useGamificationEvents(): GamificationEventState {
  const [badgeQueue, setBadgeQueue] = useState<
    (NewlyEarnedBadge & { xpEarned: number })[]
  >([]);
  const [pendingLevelUp, setPendingLevelUp] = useState<{
    level: number;
    levelName: string;
  } | null>(null);

  const pendingBadge = badgeQueue[0] ?? null;

  const dismissBadge = useCallback(() => {
    setBadgeQueue((q) => q.slice(1));
  }, []);

  const dismissLevelUp = useCallback(() => {
    setPendingLevelUp(null);
  }, []);

  const handleUpdate = useCallback((update: GamificationUpdate) => {
    if (update.leveled_up) {
      setPendingLevelUp({ level: update.level, levelName: update.level_name });
    }
    if (update.newly_earned_badges?.length) {
      setBadgeQueue((q) => [
        ...q,
        ...update.newly_earned_badges.map((b) => ({
          ...b,
          xpEarned: update.xp_earned,
        })),
      ]);
    }
  }, []);

  return {
    pendingBadge,
    pendingLevelUp,
    dismissBadge,
    dismissLevelUp,
    handleUpdate,
  };
}
