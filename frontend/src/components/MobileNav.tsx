import { Link, useLocation } from "react-router-dom";
import { House, Target, BarChart3, Users, Settings } from "lucide-react";

interface MobileNavProps {
  className?: string;
}

const navItems = [
  { path: "/dashboard", icon: House, label: "Home" },
  { path: "/practice", icon: Target, label: "Practice" },
  { path: "/progress", icon: BarChart3, label: "Progress" },
  { path: "/classes", icon: Users, label: "Classes" },
  { path: "/settings", icon: Settings, label: "Settings" },
];

const MobileNav = ({ className }: MobileNavProps) => {
  const location = useLocation();

  const isActive = (path: string) =>
    location.pathname === path || location.pathname.startsWith(path + "/");

  return (
    <nav
      className={`bg-card border-t border-border ${className}`}
      style={{ paddingBottom: "env(safe-area-inset-bottom)" }}
    >
      <div className="flex items-stretch h-16">
        {navItems.map(({ path, icon: Icon, label }) => {
          const active = isActive(path);
          return (
            <Link
              key={path}
              to={path}
              className={`flex flex-col items-center justify-center gap-1 flex-1 min-w-0 transition-colors relative ${
                active ? "text-primary" : "text-muted-foreground"
              }`}
            >
              {active && (
                <span className="absolute top-0 inset-x-4 h-0.5 bg-primary rounded-full" />
              )}
              <Icon className="w-5 h-5 shrink-0" />
              <span className="text-[10px] font-medium leading-none">{label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
};

export default MobileNav;
