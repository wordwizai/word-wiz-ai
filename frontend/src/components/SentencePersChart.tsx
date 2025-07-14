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

const SentencePersChart = () => {
  const [chartData, setChartData] = useState<
    { date: Date; per: number; avg5: number | null }[]
  >([]);
  const { token } = useContext(AuthContext);

  useEffect(() => {
    const fetchChartData = async () => {
      if (!token) return;
      const response = await getSentencePers(token);
      console.log("Fetched chart data:", response);

      const processed = response.map((item: any) => ({
        date: new Date(item.date),
        per: item.per,
      }));
      // Calculate rolling average over groups of 5
      const withAvg5 = processed.map((item, idx, arr) => {
        const start = Math.max(0, idx - 4);
        const window = arr.slice(start, idx + 1);
        const avg = window.reduce((sum, v) => sum + v.per, 0) / window.length;
        return { ...item, avg5: avg };
      });

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
    <Card className="h-64 w-full space-y-0 gap-0 px-0">
      <CardHeader>
        <CardTitle>Error Rate Progress</CardTitle>
      </CardHeader>
      <CardContent className="h-full w-full pt-0 px-2">
        <ChartContainer config={chartConfig} className="h-full w-full">
          <AreaChart accessibilityLayer data={chartData} height={220}>
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
            <CartesianGrid vertical={false} />
            <XAxis
              dataKey="date"
              tickLine={false}
              axisLine={false}
              tickMargin={8}
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
              fill="url(#perGradient)"
              name="Raw PER"
            />
            <Area
              dataKey="avg5"
              type="natural"
              stroke="var(--chart-3)"
              fill="url(#avg5Gradient)"
              name="Average (5) "
              connectNulls={false}
              dot={false}
              isAnimationActive={false}
            />
          </AreaChart>
        </ChartContainer>
      </CardContent>
    </Card>
  );
};

export default SentencePersChart;
