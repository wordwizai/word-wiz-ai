import { useContext, useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowRight, ChevronRight, Flame } from "lucide-react";
import { AuthContext } from "@/contexts/AuthContext";
import { getSessions, getUserStatistics } from "@/api";
import { AppPage, PageHeader, SectionHeader } from "@/components/AppPage";
import ActivitiesList from "@/components/ActivitiesList";
import DynamicIcon from "@/components/DynamicIcon";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useActivities, useStartActivity } from "@/hooks/useActivities";
import {
  activityPastel,
  activityTypeLabel,
  friendlyDate,
  pickDailyActivities,
} from "@/lib/activities";

interface DashboardSession {
  id: number;
  created_at: string;
  is_completed: boolean;
  activity: {
    id: number;
    title: string;
    activity_type: string;
    emoji_icon: string;
  };
}

const RECENT_LIMIT = 4;

const greeting = () => {
  const hour = new Date().getHours();
  if (hour < 12) return "Good morning";
  if (hour < 18) return "Good afternoon";
  return "Good evening";
};

const Dashboard = () => {
  const { user, token } = useContext(AuthContext);
  const navigate = useNavigate();
  const { activities } = useActivities();
  const { start, startingId } = useStartActivity();

  const [sessions, setSessions] = useState<DashboardSession[] | null>(null);
  const [streak, setStreak] = useState(0);

  useEffect(() => {
    if (!token) return;
    getSessions(token)
      .then((data: DashboardSession[]) =>
        setSessions(
          [...data].sort(
            (a, b) =>
              new Date(b.created_at).getTime() -
                new Date(a.created_at).getTime() || b.id - a.id
          )
        )
      )
      .catch((error: unknown) => {
        console.error("Error fetching sessions:", error);
        setSessions([]);
      });
    getUserStatistics(token)
      .then((stats) => setStreak(stats.current_streak))
      .catch((error: unknown) =>
        console.error("Error fetching statistics:", error)
      );
  }, [token]);

  const firstName = user?.full_name?.trim().split(/\s+/)[0];
  const dailyPicks = useMemo(
    () => (activities ? pickDailyActivities(activities) : null),
    [activities]
  );

  // The session to resume is the newest one that isn't finished. Finished
  // sessions can't be reopened (PracticeRouter bounces them), so in the
  // recent list they start a fresh session of the same activity instead.
  const resumable = sessions?.find((s) => !s.is_completed) ?? null;
  const recent = (sessions ?? [])
    .filter((s) => s.id !== resumable?.id)
    .slice(0, RECENT_LIMIT);

  const openSession = (session: DashboardSession) => {
    if (session.is_completed) start(session.activity.id);
    else navigate(`/practice/${session.id}`);
  };

  return (
    <AppPage>
      <PageHeader
        title={firstName ? `${greeting()}, ${firstName}` : "Welcome back"}
        actions={
          streak > 0 && (
            <p className="inline-flex items-center gap-2 rounded-full border bg-card px-4 py-2 text-sm font-medium text-foreground shadow-xs">
              <Flame className="size-4 text-pastel-coral-foreground" />
              {streak}-day streak
            </p>
          )
        }
      />

      {sessions === null ? (
        <Skeleton className="h-40 rounded-3xl" />
      ) : (
        resumable && (
          <ContinueCard
            session={resumable}
            onContinue={() => navigate(`/practice/${resumable.id}`)}
          />
        )
      )}

      <section aria-labelledby="picks-heading">
        <SectionHeader
          id="picks-heading"
          title="Today's picks"
          action={
            <Link
              to="/practice"
              className="inline-flex min-h-11 items-center gap-1 text-sm font-semibold text-primary hover:underline underline-offset-4"
            >
              All activities
              <ChevronRight className="size-4" />
            </Link>
          }
        />
        <ActivitiesList activities={dailyPicks} />
      </section>

      {recent.length > 0 && (
        <section aria-labelledby="recent-heading">
          <SectionHeader id="recent-heading" title="Recent" />
          <ul className="divide-y overflow-hidden rounded-2xl border bg-card shadow-xs">
            {recent.map((session) => (
              <li key={session.id}>
                <RecentRow
                  session={session}
                  isStarting={startingId === session.activity.id}
                  disabled={startingId !== null}
                  onOpen={() => openSession(session)}
                />
              </li>
            ))}
          </ul>
        </section>
      )}
    </AppPage>
  );
};

const ContinueCard = ({
  session,
  onContinue,
}: {
  session: DashboardSession;
  onContinue: () => void;
}) => {
  const pastel = activityPastel(session.activity.id);

  return (
    <section
      aria-labelledby="continue-heading"
      className="flex flex-col gap-5 rounded-3xl p-5 shadow-sm ring-1 ring-inset ring-black/5 sm:flex-row sm:items-center sm:gap-6 sm:p-8 dark:shadow-black/50 dark:inset-shadow-2xs dark:inset-shadow-white/10"
      style={{ backgroundColor: pastel.background }}
    >
      <div className="flex min-w-0 flex-1 items-center gap-4 sm:gap-6">
        <span
          className="flex size-14 shrink-0 items-center justify-center rounded-2xl bg-white/60 sm:size-20 dark:bg-white/10"
          style={{ color: pastel.foreground }}
        >
          <DynamicIcon
            name={session.activity.emoji_icon}
            className="size-7 sm:size-10"
            fallback="BookOpen"
          />
        </span>

        <div className="min-w-0">
          <p className="text-sm font-medium text-foreground/70">
            Pick up where you left off
          </p>
          <h2
            id="continue-heading"
            className="mt-1 text-xl leading-tight font-bold tracking-tight sm:text-3xl"
            style={{ color: pastel.foreground }}
          >
            {session.activity.title}
          </h2>
          <p className="mt-1 text-sm text-foreground/70">
            {activityTypeLabel(session.activity.activity_type)} ·{" "}
            {friendlyDate(session.created_at)}
          </p>
        </div>
      </div>

      <Button
        size="lg"
        onClick={onContinue}
        className="h-14 w-full shrink-0 rounded-xl px-8 text-base font-semibold sm:w-auto active:scale-[0.98]"
      >
        Keep reading
        <ArrowRight className="size-5" />
      </Button>
    </section>
  );
};

const RecentRow = ({
  session,
  isStarting,
  disabled,
  onOpen,
}: {
  session: DashboardSession;
  isStarting: boolean;
  disabled: boolean;
  onOpen: () => void;
}) => {
  const pastel = activityPastel(session.activity.id);

  return (
    <button
      type="button"
      onClick={onOpen}
      disabled={disabled}
      className="flex min-h-16 w-full items-center gap-4 px-4 py-3 text-left transition-colors outline-none hover:bg-muted/60 focus-visible:bg-muted/60 disabled:cursor-default disabled:hover:bg-transparent sm:px-5"
    >
      <span
        className="flex size-10 shrink-0 items-center justify-center rounded-xl"
        style={{ backgroundColor: pastel.background, color: pastel.foreground }}
      >
        <DynamicIcon
          name={session.activity.emoji_icon}
          className="size-5"
          fallback="BookOpen"
        />
      </span>
      <span className="min-w-0 flex-1">
        <span className="block truncate font-medium text-foreground">
          {session.activity.title}
        </span>
        <span className="block text-sm text-muted-foreground">
          {activityTypeLabel(session.activity.activity_type)} ·{" "}
          {friendlyDate(session.created_at)}
        </span>
      </span>
      <span className="hidden text-sm font-medium text-muted-foreground sm:inline">
        {isStarting ? "Starting…" : session.is_completed ? "Read again" : "Resume"}
      </span>
      <ChevronRight className="size-4 shrink-0 text-muted-foreground" />
    </button>
  );
};

export default Dashboard;
