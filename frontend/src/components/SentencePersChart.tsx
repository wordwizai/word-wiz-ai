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
  const [chartData, setChartData] = useState([]);
  const { token } = useContext(AuthContext);

  useEffect(() => {
    const fetchChartData = async () => {
      if (!token) return;
      const response = await getSentencePers(token);
      console.log("Fetched chart data:", response);
      const processedData = response.map((item: any) => ({
        ...item,
        date: new Date(item.date),
      }));

      setChartData(processedData);
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
    <Card className="h-64 w-full space-y-0 gap-0">
      <CardHeader>
        <CardTitle>Progress</CardTitle>
      </CardHeader>
      <CardContent className="h-full w-full pt-0">
        <ChartContainer config={chartConfig} className="h-full w-full p-8">
          <AreaChart accessibilityLayer data={chartData} height={220}>
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
            <Area dataKey="per" type="natural" fillOpacity={0.4} />
          </AreaChart>
        </ChartContainer>
      </CardContent>
    </Card>
  );
};

export default SentencePersChart;
