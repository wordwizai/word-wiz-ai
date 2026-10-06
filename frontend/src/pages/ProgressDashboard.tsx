import { useContext, useEffect, useState } from "react";
import { AuthContext } from "@/contexts/AuthContext";
import { getUserStatistics, type UserStatistics } from "@/api";
import { AppPage, PageHeader, SectionHeader } from "@/components/AppPage";
import SoundErrorsCard from "@/components/SoundErrorsCard";
import SentencePersChart from "@/components/SentencePersChart";
import { Skeleton } from "@/components/ui/skeleton";

const days = (n: number) => `${n} ${n === 1 ? "day" : "days"}`;

const ProgressDashboard = () => {
  const { token } = useContext(AuthContext);
  const [stats, setStats] = useState<UserStatistics | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    if (!token) return;
    getUserStatistics(token)
      .then(setStats)
      .catch((error: unknown) => {
        console.error("Error fetching statistics:", error);
        setFailed(true);
      });
  }, [token]);

  // Only numbers the backend actually measures. Accuracy and improvement
  // tiles used to show fixed placeholder values, so they are gone until
  // there is real data behind them.
  const tiles = [
    { label: "Sessions", value: stats?.total_sessions.toLocaleString() },
    { label: "Words read", value: stats?.words_read.toLocaleString() },
    { label: "Current streak", value: stats && days(stats.current_streak) },
    { label: "Best streak", value: stats && days(stats.longest_streak) },
  ];

  return (
    <AppPage title="Progress">
      <PageHeader
        title="Progress"
        description="How reading is going, and which sounds still need practice."
      />

      <section aria-label="Totals">
        <dl className="grid grid-cols-2 gap-px overflow-hidden rounded-2xl border bg-border shadow-xs lg:grid-cols-4">
          {tiles.map((tile) => (
            <div key={tile.label} className="bg-card px-5 py-5">
              <dt className="text-sm text-muted-foreground">{tile.label}</dt>
              <dd className="mt-1 text-3xl font-semibold tracking-tight text-foreground tabular-nums">
                {tile.value ??
                  (failed ? (
                    <span className="text-base font-normal text-muted-foreground">
                      Unavailable
                    </span>
                  ) : (
                    <Skeleton className="mt-1 h-8 w-16" />
                  ))}
              </dd>
            </div>
          ))}
        </dl>
      </section>

      <section aria-labelledby="error-rate-heading">
        <SectionHeader id="error-rate-heading" title="Error rate over time" />
        <SentencePersChart />
      </section>

      <section aria-labelledby="sounds-heading">
        <SectionHeader id="sounds-heading" title="Sounds to work on" />
        <p className="-mt-2 mb-4 text-sm text-muted-foreground">
          The sounds missed most often in the last 10 readings.
        </p>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <SoundErrorsCard errorType="substitution" />
          <SoundErrorsCard errorType="deletion" />
          <SoundErrorsCard errorType="insertion" />
        </div>
      </section>
    </AppPage>
  );
};

export default ProgressDashboard;
