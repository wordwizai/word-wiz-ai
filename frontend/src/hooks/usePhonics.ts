import { useContext, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AuthContext } from "@/contexts/AuthContext";
import {
  getMyAssignments,
  getPhonicsPath,
  startPatternSession,
  type PhonicsPath,
  type StudentAssignment,
} from "@/api";
import { showErrorToast } from "@/utils/errorHandling";

export function usePhonicsPath() {
  const { token } = useContext(AuthContext);
  const [path, setPath] = useState<PhonicsPath | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    getPhonicsPath(token)
      .then((data) => {
        if (!cancelled) setPath(data);
      })
      .catch((error: unknown) => {
        console.error("Failed to fetch phonics path:", error);
        if (!cancelled) setFailed(true);
      });
    return () => {
      cancelled = true;
    };
  }, [token]);

  return { path, failed };
}

// A failed request leaves the list empty: most children have no teacher, so
// a missing "From your teacher" section isn't worth an error.
export function useMyAssignments() {
  const { token } = useContext(AuthContext);
  const [assignments, setAssignments] = useState<StudentAssignment[] | null>(null);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    getMyAssignments(token)
      .then((data) => {
        if (!cancelled) setAssignments(data);
      })
      .catch((error: unknown) => {
        console.error("Failed to fetch assignments:", error);
        if (!cancelled) setAssignments([]);
      });
    return () => {
      cancelled = true;
    };
  }, [token]);

  return { assignments };
}

// Like useStartActivity: the tapped pattern shows a pending state and the
// rest are locked until the session exists.
export function useStartPattern() {
  const { token } = useContext(AuthContext);
  const navigate = useNavigate();
  const [startingSlug, setStartingSlug] = useState<string | null>(null);
  // State updates land on the next render, so a second tap in the same tick
  // would still see null. The ref closes that window.
  const inFlight = useRef(false);

  const start = async (slug: string) => {
    if (inFlight.current) return;
    inFlight.current = true;
    setStartingSlug(slug);
    try {
      const session = await startPatternSession(token ?? "", slug);
      navigate(`/practice/${session.id}`);
    } catch (error) {
      console.error("Failed to start pattern:", error);
      showErrorToast("Couldn't start that practice. Please try again.");
    } finally {
      inFlight.current = false;
      setStartingSlug(null);
    }
  };

  return { start, startingSlug };
}
