import type { ComponentType } from "react";
import { BarChart3, BookOpen, House, Users } from "lucide-react";

// The signed-in destinations, shared by the desktop sidebar and the
// mobile nav so the two never drift apart.
export const APP_NAV: {
  to: string;
  label: string;
  icon: ComponentType<{ className?: string }>;
}[] = [
  { to: "/dashboard", label: "Dashboard", icon: House },
  { to: "/practice", label: "Practice", icon: BookOpen },
  { to: "/progress", label: "Progress", icon: BarChart3 },
  { to: "/classes", label: "Classes", icon: Users },
];
