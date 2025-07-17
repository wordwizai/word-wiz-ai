import React, { useContext, useEffect, useState } from "react";
import { TrendingUp } from "lucide-react";
import { Pie, PieChart } from "recharts";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";
import { AuthContext } from "@/contexts/AuthContext";
import { getPhonemesPerMistakeType } from "../api";

type ErrorType = "substitution" | "insertion" | "deletion";

interface PhonemeErrorsPieChartProps {
  errorType: ErrorType;
  className?: string; // additional class names for styling
}

interface ErrorData {
  phoneme: string;
  count: number;
}

const getColor = (i: number) => `hsl(${(i * 360) / 8}, 70%, 70%)`; // up to 8 unique colors

const PhonemeErrorsPieChart: React.FC<PhonemeErrorsPieChartProps> = ({
  errorType,
  className = "",
}) => {
  const [data, setData] = useState<ErrorData[]>([]);
  const [loading, setLoading] = useState(true);
  const { token } = useContext(AuthContext);

  useEffect(() => {
    setLoading(true);
    getPhonemesPerMistakeType(token ?? "", errorType)
      .then((res: Record<string, number>) => {
        // Convert {"_phoneme_": count} to [{ phoneme, count }]
        const arr = Object.entries(res).map(([phoneme, count]) => ({
          phoneme,
          count,
        }));
        setData(arr);
        setLoading(false);
      })
      .catch((error) => {
        console.error("Error fetching phoneme errors:", error);
        setData([]);
        setLoading(false);
      });
  }, [errorType, token]);

  // Prepare chart data and config
  const chartData = data.map((d, i) => ({
    ...d,
    fill: getColor(i),
  }));

  // Dynamically build chartConfig for legend/colors
  const dynamicChartConfig = Object.fromEntries(
    chartData.map((d, i) => [
      d.phoneme,
      {
        label: d.phoneme,
        color: getColor(i),
      },
    ]),
  );

  return (
    <Card className={`flex flex-col ${className}`}>
      <CardHeader className="items-center pb-0">
        <CardTitle>
          {errorType.charAt(0).toUpperCase() + errorType.slice(1)} Errors
        </CardTitle>
        <CardDescription>
          Showing {errorType} errors by phoneme over the last 10 entries
        </CardDescription>
      </CardHeader>
      <CardContent className="flex-1 pb-0">
        {loading ? (
          <div>Loading...</div>
        ) : data.length === 0 ? (
          <div>No data</div>
        ) : (
          <ChartContainer
            config={dynamicChartConfig}
            className="mx-auto aspect-square max-h-[250px] px-0"
          >
            <PieChart>
              <ChartTooltip
                content={<ChartTooltipContent nameKey="phoneme" hideLabel />}
              />
              <Pie
                data={chartData}
                dataKey="count"
                labelLine={false}
                isAnimationActive={false}
                label={({ payload, ...props }) => (
                  <text
                    cx={props.cx}
                    cy={props.cy}
                    x={props.x}
                    y={props.y}
                    textAnchor={props.textAnchor}
                    dominantBaseline={props.dominantBaseline}
                    fill="hsla(var(--foreground))"
                  >
                    {payload.phoneme}
                  </text>
                )}
                nameKey="phoneme"
              />
            </PieChart>
          </ChartContainer>
        )}
      </CardContent>
      <CardFooter className="flex-col gap-2 text-sm">
        <div className="flex items-center gap-2 leading-none font-medium">
          Total of {data.reduce((sum, d) => sum + d.count, 0)} errors
        </div>
      </CardFooter>
    </Card>
  );
};

export default PhonemeErrorsPieChart;
