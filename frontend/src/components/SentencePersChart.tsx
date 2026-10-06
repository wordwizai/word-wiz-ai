import {
  Area,
  AreaChart,
  CartesianGrid,
  XAxis,
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

const AVG_COLOR = "oklch(0.6 0.118 184.704)";

const SentencePersChart = ({
  className = "",
}: {
  className?: string; // additional class names for styling
}) => {
  const [chartData, setChartData] = useState<
    { date: Date; per: number; avg5: number | null }[]
  >([]);
  const [loaded, setLoaded] = useState(false);
  const { token } = useContext(AuthContext);

  useEffect(() => {
    const fetchChartData = async () => {
      if (!token) return;
      const response = await getSentencePers(token);
      const processed = response.map((item: { date: string; per: number }) => ({
        date: new Date(item.date),
        per: item.per,
      }));
      // Calculate rolling average over groups of 5
      const withAvg5 = processed.map(
        (
          item: { date: Date; per: number },
          idx: number,
          arr: { date: Date; per: number }[]
        ) => {
          const start = Math.max(0, idx - 4);
          const window = arr.slice(start, idx + 1);
          const avg =
            window.reduce(
              (sum: number, v: { date: Date; per: number }) => sum + v.per,
              0
            ) / window.length;
          return { ...item, avg5: avg };
        }
      );

      setChartData(withAvg5);
    };
    if (token) {
      fetchChartData()
        .catch((error) => {
          console.error("Error fetching chart data:", error);
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
        ) : chartData.length === 0 ? (
          <div className="flex h-56 flex-col items-center justify-center gap-1 text-center">
            <p className="font-medium text-foreground">No readings yet</p>
            <p className="max-w-md text-sm text-balance text-muted-foreground">
              Read a few sentences in any activity and this chart fills in.
            </p>
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
                dataKey="date"
                tickLine={false}
                axisLine={false}
                tickMargin={8}
                minTickGap={56}
                tick={{ fill: "var(--muted-foreground)", fontSize: 12 }}
                tickFormatter={(date) =>
                  date instanceof Date
                    ? date.toLocaleDateString(undefined, {
                        month: "short",
                        day: "numeric",
                      })
                    : String(date)
                }
              />
              <ChartTooltip
                cursor={false}
                content={<ChartTooltipContent indicator="line" />}
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
