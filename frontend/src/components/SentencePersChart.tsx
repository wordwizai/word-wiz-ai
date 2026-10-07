import {
  Area,
  AreaChart,
  CartesianGrid,
  XAxis,
  YAxis,
} from "recharts";
import {
  Card,
  CardContent,
  CardHeader,
} from "./ui/card";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "./ui/chart";
import { useContext, useEffect, useState } from "react";
import { AuthContext } from "@/contexts/AuthContext";
import { getSentencePers } from "@/api";
import { Skeleton } from "./ui/skeleton";
import { Button } from "./ui/button";
import { Link } from "react-router-dom";
import { parseServerDate } from "@/lib/activities";

const AVG_COLOR = "oklch(0.6 0.118 184.704)";

const percent = (value: number) => `${Math.round(value * 100)}%`;
const dayLabel = (date: Date) =>
  date.toLocaleDateString(undefined, { month: "short", day: "numeric" });

type ChartPoint = { i: number; date: Date; per: number; avg5: number | null };

const SentencePersChart = ({
  className = "",
}: {
  className?: string; // additional class names for styling
}) => {
  const [chartData, setChartData] = useState<ChartPoint[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [failed, setFailed] = useState(false);
  const { token } = useContext(AuthContext);

  useEffect(() => {
    const fetchChartData = async () => {
      if (!token) return;
      const response = await getSentencePers(token);
      const processed = response.map(
        (item: { date: string; per: number }, i: number) => ({
          i,
          date: parseServerDate(item.date),
          per: item.per,
        })
      );
      // Calculate rolling average over groups of 5
      const withAvg5: ChartPoint[] = processed.map(
        (
          item: Omit<ChartPoint, "avg5">,
          idx: number,
          arr: Omit<ChartPoint, "avg5">[]
        ) => {
          const start = Math.max(0, idx - 4);
          const window = arr.slice(start, idx + 1);
          const avg =
            window.reduce((sum: number, v) => sum + v.per, 0) / window.length;
          return { ...item, avg5: avg };
        }
      );

      setChartData(withAvg5);
    };
    if (token) {
      fetchChartData()
        .catch((error) => {
          console.error("Error fetching chart data:", error);
          setFailed(true);
        })
        .finally(() => setLoaded(true));
    }
  }, [token]);

  // Brand purple for the raw series, teal for the average. Checked with the
  // dataviz palette validator against both card surfaces (light and dark).
  const chartConfig = {
    per: { label: "Error rate", color: "var(--primary)" },
    avg5: { label: "Average of last 5", color: AVG_COLOR },
  } satisfies ChartConfig;

  // The x axis is reading order, with one tick on each day's first reading.
  // A tick per reading printed the same date over and over on busy days.
  const dayTicks = chartData
    .filter(
      (point, idx) =>
        idx === 0 ||
        point.date.toDateString() !== chartData[idx - 1].date.toDateString()
    )
    .map((point) => point.i);

  return (
    <Card
      className={
        "w-full gap-0 rounded-2xl py-0 shadow-xs " + className
      }
    >
      <CardHeader className="flex flex-col gap-1 px-5 pt-5 pb-0 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-sm text-muted-foreground">
          Share of sounds read wrong in each sentence. Lower is better.
        </p>
        {chartData.length > 0 && (
          <div className="flex items-center gap-4 text-xs text-muted-foreground">
            <span className="inline-flex items-center gap-1.5">
              <span className="size-2.5 rounded-full bg-primary" />
              Each sentence
            </span>
            <span className="inline-flex items-center gap-1.5">
              <span className="size-2.5 rounded-full" style={{ backgroundColor: AVG_COLOR }} />
              Average of last 5
            </span>
          </div>
        )}
      </CardHeader>
      <CardContent className="px-2 pt-4 pb-4 sm:px-4">
        {!loaded ? (
          <Skeleton className="h-56 w-full rounded-xl" />
        ) : failed ? (
          <div className="flex h-56 flex-col items-center justify-center gap-1 text-center">
            <p className="font-medium text-foreground">
              Couldn't load your readings
            </p>
            <p className="max-w-md text-sm text-balance text-muted-foreground">
              They're still saved. Check your connection and refresh the page.
            </p>
          </div>
        ) : chartData.length === 0 ? (
          <div className="flex h-56 flex-col items-center justify-center gap-1 text-center">
            <p className="font-medium text-foreground">No readings yet</p>
            <p className="max-w-md text-sm text-balance text-muted-foreground">
              Read a few sentences in any activity and this chart fills in.
            </p>
            <Button asChild size="sm" className="mt-3 rounded-xl">
              <Link to="/practice">Start reading</Link>
            </Button>
          </div>
        ) : (
          <ChartContainer config={chartConfig} className="h-56 w-full">
            <AreaChart accessibilityLayer data={chartData}>
              <defs>
                <linearGradient id="perGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="var(--primary)" stopOpacity={0.25} />
                  <stop offset="95%" stopColor="var(--primary)" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid vertical={false} stroke="var(--border)" />
              <XAxis
                dataKey="i"
                type="number"
                domain={["dataMin", "dataMax"]}
                ticks={dayTicks}
                padding={{ left: 16, right: 24 }}
                tickLine={false}
                axisLine={false}
                tickMargin={8}
                minTickGap={40}
                tick={{ fill: "var(--muted-foreground)", fontSize: 12 }}
                tickFormatter={(i: number) =>
                  chartData[i] ? dayLabel(chartData[i].date) : ""
                }
              />
              <YAxis
                width={44}
                domain={[0, "auto"]}
                tickCount={4}
                tickLine={false}
                axisLine={false}
                tick={{ fill: "var(--muted-foreground)", fontSize: 12 }}
                tickFormatter={percent}
              />
              <ChartTooltip
                cursor={false}
                content={
                  <ChartTooltipContent
                    indicator="line"
                    labelFormatter={(_, payload) => {
                      const date = payload?.[0]?.payload?.date;
                      return date instanceof Date
                        ? date.toLocaleString(undefined, {
                            month: "short",
                            day: "numeric",
                            hour: "numeric",
                            minute: "2-digit",
                          })
                        : null;
                    }}
                    // The default row hides a value of 0, which is a
                    // perfect sentence, and prints fractions like 0.333.
                    formatter={(value, name, item) => (
                      <>
                        <span
                          className="w-1 shrink-0 self-stretch rounded-[2px]"
                          style={{ backgroundColor: item.color }}
                        />
                        <span className="flex flex-1 items-center justify-between gap-4 leading-none">
                          <span className="text-muted-foreground">
                            {chartConfig[name as keyof typeof chartConfig]
                              ?.label ?? name}
                          </span>
                          <span className="font-mono font-medium text-foreground tabular-nums">
                            {percent(Number(value))}
                          </span>
                        </span>
                      </>
                    )}
                  />
                }
              />
              <Area
                dataKey="per"
                type="monotone"
                stroke="var(--primary)"
                strokeWidth={2}
                fill="url(#perGradient)"
                connectNulls={false}
                dot={{ fill: "var(--primary)", r: 4, strokeWidth: 2, stroke: "var(--card)" }}
              />
              <Area
                dataKey="avg5"
                type="monotone"
                stroke={AVG_COLOR}
                strokeWidth={2}
                fill="none"
                connectNulls={false}
                dot={false}
              />
            </AreaChart>
          </ChartContainer>
        )}
      </CardContent>
    </Card>
  );
};

export default SentencePersChart;
