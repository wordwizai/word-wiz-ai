import { Link, useLocation } from "react-router-dom";
import { Button } from "./ui/button";
import {
  BadgeCheck,
  BarChart3,
  Bell,
  House,
  LogOut,
  Settings,
  Target,
} from "lucide-react";
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
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "./ui/dropdown-menu";
import { Avatar, AvatarFallback, AvatarImage } from "./ui/avatar";

interface MobileNavProps {
  className?: string;
}

const MobileNav = ({ className }: MobileNavProps) => {
  const { user, logout } = useContext<AuthContextType>(AuthContext);
  const location = useLocation();

  const isActive = (path: string) =>
    location.pathname === path || location.pathname.startsWith(path + "/");

  const navLinkClass = (path: string) =>
    `p-2.5 rounded-xl transition-colors ${
      isActive(path)
        ? "bg-primary/10 text-primary"
        : "text-muted-foreground hover:bg-muted hover:text-foreground"
    }`;

  return (
    <TooltipProvider>
      <aside className={`${className}`}>
        <div className="mx-3 sm:mx-5 mb-2 px-2 py-1.5 flex flex-row items-center justify-around bg-card border-t border-border rounded-t-2xl shadow-lg">
          {/* Home */}
          <Tooltip delayDuration={300}>
            <TooltipTrigger asChild>
              <Link to="/dashboard" className={navLinkClass("/dashboard")}>
                <span className="sr-only">Dashboard</span>
                <House className="size-6" />
              </Link>
            </TooltipTrigger>
            <TooltipContent side="top">Dashboard</TooltipContent>
          </Tooltip>

          <Tooltip delayDuration={300}>
            <TooltipTrigger asChild>
              <Link to="/practice" className={navLinkClass("/practice")}>
                <span className="sr-only">Practice</span>
                <Target className="size-6" />
              </Link>
            </TooltipTrigger>
            <TooltipContent side="top">Practice</TooltipContent>
          </Tooltip>

          <Tooltip delayDuration={300}>
            <TooltipTrigger asChild>
              <Link to="/progress" className={navLinkClass("/progress")}>
                <span className="sr-only">Progress</span>
                <BarChart3 className="size-6" />
              </Link>
            </TooltipTrigger>
            <TooltipContent side="top">Progress</TooltipContent>
          </Tooltip>

          <Tooltip delayDuration={300}>
            <TooltipTrigger asChild>
              <Link to="/settings" className={navLinkClass("/settings")}>
                <span className="sr-only">Settings</span>
                <Settings className="size-6" />
              </Link>
            </TooltipTrigger>
            <TooltipContent side="top">Settings</TooltipContent>
          </Tooltip>

          {/* Avatar Dropdown */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                className="w-10 h-10 rounded-xl hover:bg-muted transition-colors p-0"
              >
                <span className="sr-only">Account</span>
                <Avatar className="w-8 h-8 rounded-xl">
                  <AvatarImage src="" alt={user?.username} />
                  <AvatarFallback className="bg-primary/10 text-primary font-bold rounded-xl text-xs">
                    {nameToInitials(user?.full_name ?? "")}
                  </AvatarFallback>
                </Avatar>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent
              className="w-64 rounded-xl border-2 border-border bg-card shadow-lg"
              side="top"
              align="end"
              sideOffset={8}
            >
              <DropdownMenuLabel className="p-0 font-normal">
                <div className="flex items-center gap-3 px-3 py-3 text-left">
                  <Avatar className="h-10 w-10 rounded-xl">
                    <AvatarImage src="" alt={user?.full_name ?? "Not logged in"} />
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
              <DropdownMenuGroup>
                <DropdownMenuItem asChild className="rounded-lg mx-2 hover:bg-secondary">
                  <Link to="/settings#account" className="flex items-center gap-3">
                    <BadgeCheck size={18} className="text-primary" />
                    <span>Account</span>
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuItem asChild className="rounded-lg mx-2 hover:bg-secondary">
                  <Link to="/settings#notifications" className="flex items-center gap-3">
                    <Bell size={18} className="text-primary" />
                    <span>Notifications</span>
                  </Link>
                </DropdownMenuItem>
              </DropdownMenuGroup>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={logout}
                className="rounded-lg mx-2 hover:bg-destructive/10"
              >
                <LogOut size={18} className="text-destructive" />
                <span>Log out</span>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </aside>
    </TooltipProvider>
  );
};

export default MobileNav;
