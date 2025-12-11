import { Link, useLocation } from "react-router-dom";
import { Button } from "./ui/button";
import {
  BadgeCheck,
  Bell,
  CircleQuestionMark,
  House,
  LogOut,
  Route,
  Settings,
  Target,
  BarChart3,
  Sun,
  Moon,
  PanelLeftClose,
  PanelLeft,
  Users,
} from "lucide-react";
import { Avatar, AvatarFallback, AvatarImage } from "./ui/avatar";
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
import { useContext, useState } from "react";
import { AuthContext } from "@/contexts/AuthContext";
import type { AuthContextType } from "@/contexts/AuthContext";
import { useTheme } from "@/contexts/ThemeContext";
import { nameToInitials } from "@/lib/utils";
import { wordWizIcon } from "@/assets";

interface SidebarProps {
  className?: string;
}

const Sidebar = ({ className }: SidebarProps) => {
  // get the user
  const { user, logout } = useContext<AuthContextType>(AuthContext);
  const { theme, setTheme } = useTheme();
  const location = useLocation();
  const [isExpanded, setIsExpanded] = useState(true);

  // Helper to check if route is active
  const isActive = (path: string) => {
    return (
      location.pathname === path || location.pathname.startsWith(path + "/")
    );
  };

  return (
    <TooltipProvider>
      <aside
        className={`${
          isExpanded ? "w-64" : "w-20"
        } flex flex-col bg-sidebar p-4 space-y-6 border-r-2 border-border transition-all duration-300 ${className}`}
      >
        {/* Logo/Brand and Toggle */}
        <div className="flex items-center justify-between mb-4">
          {isExpanded && (
            <Link
              to="/dashboard"
              className="flex items-center gap-3 flex-1 min-w-0"
            >
              <div className="w-12 h-12 flex-shrink-0 bg-gradient-to-br from-primary/60 to-purple-300 rounded-2xl flex items-center justify-center shadow-md hover:shadow-lg transition-shadow">
                <img src={wordWizIcon} alt="Word Wiz" className="w-10 h-10" />
              </div>
              <span className="text-lg font-bold text-foreground">
                Word Wiz <span className="text-primary">AI</span>
              </span>
            </Link>
          )}
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setIsExpanded(!isExpanded)}
            className={`w-12 h-12 flex-shrink-0 rounded-xl hover:bg-primary/10 transition-colors ${
              !isExpanded ? "mx-auto" : ""
            }`}
          >
            {isExpanded ? (
              <PanelLeftClose className="w-5 h-5 text-foreground" />
            ) : (
              <PanelLeft className="w-5 h-5 text-foreground" />
            )}
          </Button>
        </div>

        {/* Navigation Items */}
        <div
          className={`flex flex-col space-y-4 ${
            isExpanded ? "items-stretch" : "items-center"
          }`}
        >
          <Tooltip delayDuration={300}>
            <TooltipTrigger asChild>
              <Link to="/dashboard">
                <Button
                  variant="ghost"
                  className={`${
                    isExpanded ? "w-full justify-start" : "w-12 h-12"
                  } rounded-xl hover:bg-purple-100/50 transition-colors ${
                    isActive("/dashboard")
                      ? "bg-purple-100/70 border-2 border-purple-300"
                      : ""
                  }`}
                >
                  <House
                    className={`w-5 h-5 text-purple-600 ${
                      isExpanded ? "mr-3" : ""
                    }`}
                  />
                  {isExpanded && (
                    <span className="font-medium text-foreground">
                      Dashboard
                    </span>
                  )}
                  {!isExpanded && <span className="sr-only">Dashboard</span>}
                </Button>
              </Link>
            </TooltipTrigger>
            {!isExpanded && (
              <TooltipContent
                side="right"
                className="bg-card border-2 border-border text-foreground"
              >
                <p>Dashboard</p>
              </TooltipContent>
            )}
          </Tooltip>

          <Tooltip delayDuration={300}>
            <TooltipTrigger asChild>
              <Link to="/practice">
                <Button
                  variant="ghost"
                  className={`${
                    isExpanded ? "w-full justify-start" : "w-12 h-12"
                  } rounded-xl hover:bg-blue-100/50 transition-colors ${
                    isActive("/practice")
                      ? "bg-blue-100/70 border-2 border-blue-300"
                      : ""
                  }`}
                >
                  <Target
                    className={`w-5 h-5 text-blue-600 ${
                      isExpanded ? "mr-3" : ""
                    }`}
                  />
                  {isExpanded && (
                    <span className="font-medium text-foreground">
                      Practice
                    </span>
                  )}
                  {!isExpanded && <span className="sr-only">Practice</span>}
                </Button>
              </Link>
            </TooltipTrigger>
            {!isExpanded && (
              <TooltipContent
                side="right"
                className="bg-card border-2 border-border text-foreground"
              >
                <p>Practice</p>
              </TooltipContent>
            )}
          </Tooltip>

          <Tooltip delayDuration={300}>
            <TooltipTrigger asChild>
              <Link to="/progress">
                <Button
                  variant="ghost"
                  className={`${
                    isExpanded ? "w-full justify-start" : "w-12 h-12"
                  } rounded-xl hover:bg-green-100/50 transition-colors ${
                    isActive("/progress")
                      ? "bg-green-100/70 border-2 border-green-300"
                      : ""
                  }`}
                >
                  <BarChart3
                    className={`w-5 h-5 text-green-600 ${
                      isExpanded ? "mr-3" : ""
                    }`}
                  />
                  {isExpanded && (
                    <span className="font-medium text-foreground">
                      Progress
                    </span>
                  )}
                  {!isExpanded && <span className="sr-only">Progress</span>}
                </Button>
              </Link>
            </TooltipTrigger>
            {!isExpanded && (
              <TooltipContent
                side="right"
                className="bg-card border-2 border-border text-foreground"
              >
                <p>Progress</p>
              </TooltipContent>
            )}
          </Tooltip>

          <Tooltip delayDuration={300}>
            <TooltipTrigger asChild>
              <Link to="/classes">
                <Button
                  variant="ghost"
                  className={`${
                    isExpanded ? "w-full justify-start" : "w-12 h-12"
                  } rounded-xl hover:bg-orange-100/50 transition-colors ${
                    isActive("/classes")
                      ? "bg-orange-100/70 border-2 border-orange-300"
                      : ""
                  }`}
                >
                  <Users
                    className={`w-5 h-5 text-orange-600 ${
                      isExpanded ? "mr-3" : ""
                    }`}
                  />
                  {isExpanded && (
                    <span className="font-medium text-foreground">
                      Classes
                    </span>
                  )}
                  {!isExpanded && <span className="sr-only">Classes</span>}
                </Button>
              </Link>
            </TooltipTrigger>
            {!isExpanded && (
              <TooltipContent
                side="right"
                className="bg-card border-2 border-border text-foreground"
              >
                <p>Classes</p>
              </TooltipContent>
            )}
          </Tooltip>
        </div>

        {/* Bottom Buttons */}
        <div className="mt-auto">
          {/* Theme Toggle */}
          <Tooltip delayDuration={300}>
            <TooltipTrigger asChild>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="ghost"
                    className={`${
                      isExpanded ? "w-full justify-start" : "w-12 h-12"
                    } rounded-xl hover:bg-amber-100/50 transition-colors relative`}
                  >
                    <Sun
                      className={`w-5 h-5 scale-100 rotate-0 transition-all dark:scale-0 dark:-rotate-90 text-amber-600 ${
                        isExpanded ? "mr-3" : ""
                      }`}
                    />
                    <Moon
                      className={`w-5 h-5 absolute scale-0 rotate-90 transition-all dark:scale-100 dark:rotate-0 text-amber-600 ${
                        isExpanded ? "left-3" : "left-1/2 -translate-x-1/2"
                      }`}
                    />
                    {isExpanded && (
                      <span className="font-medium text-foreground">Theme</span>
                    )}
                    {!isExpanded && (
                      <span className="sr-only">Toggle theme</span>
                    )}
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent
                  align="end"
                  className="w-32 rounded-xl border-2 border-border bg-card shadow-lg"
                >
                  <DropdownMenuItem
                    onClick={() => setTheme("light")}
                    className="rounded-lg mx-2 hover:bg-secondary"
                  >
                    Light
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    onClick={() => setTheme("dark")}
                    className="rounded-lg mx-2 hover:bg-secondary"
                  >
                    Dark
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    onClick={() => setTheme("system")}
                    className="rounded-lg mx-2 hover:bg-secondary"
                  >
                    System
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </TooltipTrigger>
            {!isExpanded && (
              <TooltipContent
                side="right"
                className="bg-card border-2 border-border text-foreground"
              >
                <p>Theme</p>
              </TooltipContent>
            )}
          </Tooltip>

          {/* Settings */}
          <Tooltip delayDuration={300}>
            <TooltipTrigger asChild>
              <Link to="/settings">
                <Button
                  variant="ghost"
                  className={`${
                    isExpanded ? "w-full justify-start" : "w-12 h-12"
                  } rounded-xl hover:bg-purple-100/50 transition-colors ${
                    isActive("/settings")
                      ? "bg-purple-100/70 border-2 border-purple-300"
                      : ""
                  }`}
                >
                  <Settings
                    className={`w-5 h-5 text-purple-600 ${
                      isExpanded ? "mr-3" : ""
                    }`}
                  />
                  {isExpanded && (
                    <span className="font-medium text-foreground">
                      Settings
                    </span>
                  )}
                  {!isExpanded && <span className="sr-only">Settings</span>}
                </Button>
              </Link>
            </TooltipTrigger>
            {!isExpanded && (
              <TooltipContent
                side="right"
                className="bg-card border-2 border-border text-foreground"
              >
                <p>Settings</p>
              </TooltipContent>
            )}
          </Tooltip>

          <Tooltip delayDuration={300}>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                className={`${
                  isExpanded ? "w-full justify-start" : "w-12 h-12"
                } rounded-xl hover:bg-purple-100/50 transition-colors`}
              >
                <CircleQuestionMark
                  className={`w-5 h-5 text-purple-600 ${
                    isExpanded ? "mr-3" : ""
                  }`}
                />
                {isExpanded && (
                  <span className="font-medium text-foreground">Help</span>
                )}
                {!isExpanded && <span className="sr-only">Help</span>}
              </Button>
            </TooltipTrigger>
            {!isExpanded && (
              <TooltipContent
                side="right"
                className="bg-card border-2 border-border text-foreground"
              >
                <p>Help</p>
              </TooltipContent>
            )}
          </Tooltip>

          {/* Avatar Dropdown */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                className={`${
                  isExpanded ? "w-full justify-start" : "w-12 h-12"
                } rounded-xl hover:bg-purple-100/50 transition-colors ${
                  isExpanded ? "p-2" : "p-0"
                }`}
              >
                <Avatar className="w-10 h-10 border-2 border-primary rounded-xl">
                  <AvatarImage src="" alt={user?.username} />
                  <AvatarFallback className="bg-primary/10 text-primary font-bold rounded-xl">
                    {nameToInitials(user?.full_name ?? "")}
                  </AvatarFallback>
                </Avatar>
                {isExpanded && (
                  <div className="ml-3 text-left overflow-hidden flex-1">
                    <div className="text-sm font-semibold text-foreground truncate">
                      {user?.full_name ?? "Guest"}
                    </div>
                    <div className="text-xs text-muted-foreground truncate">
                      {user?.email ?? ""}
                    </div>
                  </div>
                )}
                {!isExpanded && <span className="sr-only">Account</span>}
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent
              className="w-64 rounded-xl border-2 border-border bg-card shadow-lg"
              side="right"
              align="end"
              sideOffset={4}
            >
              <DropdownMenuLabel className="p-0 font-normal">
                <div className="flex items-center gap-3 px-3 py-3 text-left">
                  <Avatar className="h-10 w-10 border-2 border-primary rounded-xl">
                    <AvatarImage
                      src={""}
                      alt={user?.full_name ?? "Not logged in"}
                    />
                    <AvatarFallback className="bg-primary/10 text-primary font-bold rounded-xl">
                      {nameToInitials(user?.full_name ?? "")}
                    </AvatarFallback>
                  </Avatar>
                  <div className="grid flex-1 text-left text-sm leading-tight">
                    <span className="truncate font-semibold text-foreground">
                      {user?.full_name ?? "Not logged in"}
                    </span>
                    <span className="truncate text-xs text-muted-foreground">
                      {user?.email ?? "Not logged in"}
                    </span>
                  </div>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuGroup>
                <DropdownMenuItem
                  asChild
                  className="rounded-lg mx-2 hover:bg-secondary"
                >
                  <Link
                    to="/settings#account"
                    className="flex items-center gap-3"
                  >
                    <BadgeCheck size={18} className="text-primary" />
                    <span>Account</span>
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuItem
                  asChild
                  className="rounded-lg mx-2 hover:bg-secondary"
                >
                  <Link
                    to="/settings#notifications"
                    className="flex items-center gap-3"
                  >
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

export default Sidebar;
