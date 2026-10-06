import { Link, useLocation } from "react-router-dom";
import { Button } from "./ui/button";
import { LogOut, Settings, UserRound } from "lucide-react";
import { useContext } from "react";
import { AuthContext } from "@/contexts/AuthContext";
import type { AuthContextType } from "@/contexts/AuthContext";
import { nameToInitials } from "@/lib/utils";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "./ui/tooltip";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "./ui/dropdown-menu";
import { Avatar, AvatarFallback, AvatarImage } from "./ui/avatar";
import { APP_NAV } from "@/config/appNav";

interface MobileNavProps {
  className?: string;
}

// Same destinations as the desktop sidebar, plus Settings, which the
// sidebar keeps in its footer.
const navItems = [
  ...APP_NAV.map(({ to, icon, label }) => ({ path: to, icon, label })),
  { path: "/settings", icon: Settings, label: "Settings" },
];

const MobileNav = ({ className }: MobileNavProps) => {
  const { user, logout } = useContext<AuthContextType>(AuthContext);
  const location = useLocation();

  const isActive = (path: string) =>
    location.pathname === path || location.pathname.startsWith(path + "/");

  return (
    <TooltipProvider>
      <aside
        className={`${className} fixed inset-x-0 bottom-0 flex justify-center z-50`}
        style={{ paddingBottom: "max(1rem, env(safe-area-inset-bottom))" }}
      >
        {/* Liquid glass pill */}
        <div className="glass-nav flex items-center gap-0.5 px-2 py-1.5 rounded-full">
          {navItems.map(({ path, icon: Icon, label }) => {
            const active = isActive(path);
            return (
              <Tooltip key={path} delayDuration={300}>
                <TooltipTrigger asChild>
                  <Link
                    to={path}
                    className="relative flex items-center justify-center w-11 h-11 rounded-full transition-all duration-200 active:scale-90"
                    aria-label={label}
                  >
                    {active && (
                      <span className="glass-nav-item-active absolute inset-0 rounded-full transition-all duration-200" />
                    )}
                    <Icon
                      className={`relative z-10 transition-all duration-200 ${
                        active
                          ? "glass-nav-icon-active"
                          : "glass-nav-icon-inactive"
                      }`}
                      style={{
                        width: "1.2rem",
                        height: "1.2rem",
                        strokeWidth: active ? 2.2 : 1.8,
                      }}
                    />
                  </Link>
                </TooltipTrigger>
                <TooltipContent side="top">{label}</TooltipContent>
              </Tooltip>
            );
          })}

          {/* Divider */}
          <div
            className="glass-nav-divider mx-1 self-stretch"
            style={{ width: "1px" }}
          />

          {/* Avatar Dropdown */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                className="w-11 h-11 rounded-full p-0 transition-all duration-200 active:scale-90 hover:bg-transparent focus-visible:ring-0"
              >
                <span className="sr-only">Account</span>
                <Avatar className="w-8 h-8 rounded-full ring-2 ring-primary/20">
                  <AvatarImage src="" alt={user?.username} />
                  <AvatarFallback className="rounded-full bg-primary/10 text-primary font-bold text-xs">
                    {nameToInitials(user?.full_name ?? "")}
                  </AvatarFallback>
                </Avatar>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent
              className="w-60"
              side="top"
              align="end"
              sideOffset={10}
            >
              <DropdownMenuLabel className="p-0 font-normal">
                <div className="flex items-center gap-3 px-3 py-3 text-left">
                  <Avatar className="h-10 w-10 rounded-xl">
                    <AvatarImage
                      src=""
                      alt={user?.full_name ?? "Not logged in"}
                    />
                    <AvatarFallback className="rounded-xl bg-primary/10 text-primary font-bold">
                      {nameToInitials(user?.full_name ?? "")}
                    </AvatarFallback>
                  </Avatar>
                  <div className="grid flex-1 text-left text-sm leading-tight">
                    <span className="truncate font-semibold text-foreground">
                      {user?.full_name ?? "Not logged in"}
                    </span>
                    <span className="truncate text-xs text-muted-foreground">
                      {user?.email ?? ""}
                    </span>
                  </div>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem asChild>
                <Link to="/settings#account">
                  <UserRound />
                  Account
                </Link>
              </DropdownMenuItem>
              <DropdownMenuItem onClick={logout} variant="destructive">
                <LogOut />
                Log out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </aside>
    </TooltipProvider>
  );
};

export default MobileNav;
