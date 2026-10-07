import { useContext, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AuthContext } from "@/contexts/AuthContext";
import { createSession, getActivities } from "@/api";
import { showErrorToast } from "@/utils/errorHandling";
import type { Activity } from "@/lib/activities";

export function useActivities() {
  const { token } = useContext(AuthContext);
  const [activities, setActivities] = useState<Activity[] | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    getActivities(token)
      .then((data: Activity[]) => {
        if (!cancelled) setActivities(data);
      })
      .catch((error: unknown) => {
        console.error("Failed to fetch activities:", error);
        if (!cancelled) {
          setActivities([]);
          setFailed(true);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [token]);

  return { activities, loading: activities === null, failed };
}

// Creating a session is a network round trip, so the card that was tapped
// shows a pending state and the rest are locked until it resolves.
export function useStartActivity() {
  const { token } = useContext(AuthContext);
  const navigate = useNavigate();
  const [startingId, setStartingId] = useState<number | null>(null);

  const start = async (activityId: number) => {
    if (startingId !== null) return;
    setStartingId(activityId);
    try {
      const session = await createSession(token ?? "", activityId);
      navigate(`/practice/${session.id}`);
    } catch (error) {
      console.error("Failed to start activity:", error);
      showErrorToast("Couldn't start that activity. Please try again.");
      setStartingId(null);
    }
  };

  return { start, startingId };
}
