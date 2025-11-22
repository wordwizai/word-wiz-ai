import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  XAxis,
} from "recharts";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
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
import { TrendingUp, Target } from "lucide-react";

const SentencePersChart = ({
  className = "",
}: {
  className?: string; // additional class names for styling
}) => {
  const [chartData, setChartData] = useState<
    { date: Date; per: number; avg5: number | null }[]
  >([]);
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
      fetchChartData().catch((error) => {
        console.error("Error fetching chart data:", error);
      });
    }
  }, [token]);

  const chartConfig = {
    per: {
      label: "Error rate",
      color: "--var(--chart-3)",
    },
  } satisfies ChartConfig;

  return (
    <Card
      className={
        "w-full h-48 sm:h-56 md:h-64 flex flex-col space-y-0 gap-0 px-0 rounded-2xl border-2 border-border bg-card shadow-sm " +
        className
      }
      style={{ minHeight: 0 }}
    >
      <CardHeader className="flex-shrink-0 p-3 sm:p-4">
        <div className="flex items-center gap-3">
          <TrendingUp className="w-5 h-5 text-primary" />
          <div>
            <h3 className="text-lg font-bold text-foreground">
              Error Rate Progress
            </h3>
            <p className="text-xs sm:text-sm text-muted-foreground">
              Track your improvement over time.
            </p>
          </div>
        </div>
      </CardHeader>
      <CardContent className="flex-1 min-h-0 relative pt-0 px-2 sm:px-4 flex flex-col justify-end">
        <ChartContainer
          config={chartConfig}
          className="h-full w-full min-h-0"
          style={{ minHeight: "120px" }}
        >
          <AreaChart
            accessibilityLayer
            data={chartData}
            height={undefined}
            width={undefined}
            style={{ height: "100%", width: "100%", minHeight: "120px" }}
          >
            <defs>
              <linearGradient id="perGradient" x1="0" y1="0" x2="0" y2="1">
                <stop
                  offset="5%"
                  stopColor="var(--chart-2)"
                  stopOpacity={0.8}
                />
                <stop offset="95%" stopColor="var(--chart-2)" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="avg5Gradient" x1="0" y1="0" x2="0" y2="1">
                <stop
                  offset="5%"
                  stopColor="var(--chart-3)"
                  stopOpacity={0.8}
                />
                <stop offset="95%" stopColor="var(--chart-3)" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid
              vertical={false}
              strokeDasharray="3 3"
              stroke="rgba(139, 92, 246, 0.1)"
            />
            <XAxis
              dataKey="date"
              tickLine={false}
              axisLine={false}
              tickMargin={8}
              tick={{ fill: "rgba(139, 92, 246, 0.7)", fontSize: 10 }}
              tickFormatter={(date) =>
                typeof date === "string"
                  ? date
                  : date instanceof Date
                  ? date.toLocaleDateString(undefined, {
                      month: "short",
                      day: "numeric",
                    })
                  : ""
              }
            />
            <ChartTooltip
              cursor={false}
              content={<ChartTooltipContent indicator="line" />}
            />
            <Area
              dataKey="per"
              type="natural"
              stroke="var(--chart-2)"
              strokeWidth={3}
              fill="url(#perGradient)"
              name="Raw PER"
              connectNulls={false}
              dot={{ fill: "var(--chart-2)", strokeWidth: 2, r: 4 }}
              isAnimationActive={true}
            />
            <Area
              dataKey="avg5"
              type="natural"
              stroke="var(--chart-3)"
              strokeWidth={3}
              fill="url(#avg5Gradient)"
              name="Average (5) "
              connectNulls={false}
              dot={{ fill: "var(--chart-3)", strokeWidth: 2, r: 4 }}
              isAnimationActive={true}
            />
          </AreaChart>
        </ChartContainer>
      </CardContent>
    </Card>
  );
};

export default SentencePersChart;
