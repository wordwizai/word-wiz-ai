import { Link, useLocation } from "react-router-dom";
import { Button } from "./ui/button";
import { Separator } from "./ui/separator";
import {
  BadgeCheck,
  Bell,
  CircleQuestionMark,
  House,
  LogOut,
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
  const { user, logout } = useContext<AuthContextType>(AuthContext);
  const { theme, setTheme } = useTheme();
  const location = useLocation();
  const [isExpanded, setIsExpanded] = useState(true);

  const isActive = (path: string) =>
    location.pathname === path || location.pathname.startsWith(path + "/");

  const navItemClass = (path: string, expanded: boolean) =>
    `${expanded ? "w-full justify-start" : "w-12 h-12"} rounded-lg transition-colors ${
      isActive(path)
        ? "bg-primary/10 text-primary font-medium"
        : "text-foreground hover:bg-muted"
    }`;

  const iconClass = (path: string, expanded: boolean) =>
    `w-5 h-5 ${expanded ? "mr-3" : ""} ${
      isActive(path) ? "text-primary" : "text-muted-foreground"
    }`;

  return (
    <TooltipProvider>
      <aside
        className={`${
          isExpanded ? "w-64" : "w-20"
        } flex flex-col bg-sidebar p-3 space-y-4 border-r border-border transition-all duration-300 ${className}`}
      >
        {/* Logo/Brand and Toggle */}
        <div className="flex items-center justify-between px-1 py-1">
          {isExpanded && (
            <Link
              to="/dashboard"
              className="flex items-center gap-3 flex-1 min-w-0"
            >
              <div className="w-9 h-9 flex-shrink-0 bg-primary/10 rounded-lg flex items-center justify-center">
                <img src={wordWizIcon} alt="Word Wiz" className="w-7 h-7" />
              </div>
              <span className="text-base font-semibold text-foreground">
                Word Wiz <span className="text-primary">AI</span>
              </span>
            </Link>
          )}
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setIsExpanded(!isExpanded)}
            className={`w-9 h-9 flex-shrink-0 rounded-lg hover:bg-muted transition-colors ${
              !isExpanded ? "mx-auto" : ""
            }`}
          >
            {isExpanded ? (
              <PanelLeftClose className="w-4 h-4 text-muted-foreground" />
            ) : (
              <PanelLeft className="w-4 h-4 text-muted-foreground" />
            )}
          </Button>
        </div>

        {/* Navigation Items */}
        <div
          className={`flex flex-col space-y-0.5 ${
            isExpanded ? "items-stretch" : "items-center"
          }`}
        >
          {[
            { path: "/dashboard", icon: House, label: "Dashboard" },
            { path: "/practice", icon: Target, label: "Practice" },
            { path: "/progress", icon: BarChart3, label: "Progress" },
            { path: "/classes", icon: Users, label: "Classes" },
          ].map(({ path, icon: Icon, label }) => (
            <Tooltip key={path} delayDuration={300}>
              <TooltipTrigger asChild>
                <Link to={path}>
                  <Button
                    variant="ghost"
                    className={navItemClass(path, isExpanded)}
                  >
                    <Icon className={iconClass(path, isExpanded)} />
                    {isExpanded && <span>{label}</span>}
                    {!isExpanded && <span className="sr-only">{label}</span>}
                  </Button>
                </Link>
              </TooltipTrigger>
              {!isExpanded && (
                <TooltipContent side="right" className="bg-popover border border-border text-foreground">
                  <p>{label}</p>
                </TooltipContent>
              )}
            </Tooltip>
          ))}
        </div>

        {/* Bottom Buttons */}
        <div className="mt-auto space-y-0.5">
          <Separator className="mb-2" />

          {/* Theme Toggle */}
          <Tooltip delayDuration={300}>
            <TooltipTrigger asChild>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="ghost"
                    className={`${
                      isExpanded ? "w-full justify-start" : "w-12 h-12"
                    } rounded-lg hover:bg-muted transition-colors relative text-foreground`}
                  >
                    <Sun
                      className={`w-5 h-5 scale-100 rotate-0 transition-all dark:scale-0 dark:-rotate-90 text-muted-foreground ${
                        isExpanded ? "mr-3" : ""
                      }`}
                    />
                    <Moon
                      className={`w-5 h-5 absolute scale-0 rotate-90 transition-all dark:scale-100 dark:rotate-0 text-muted-foreground ${
                        isExpanded ? "left-3" : "left-1/2 -translate-x-1/2"
                      }`}
                    />
                    {isExpanded && <span className="font-medium">Theme</span>}
                    {!isExpanded && <span className="sr-only">Toggle theme</span>}
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent
                  align="end"
                  className="w-32 rounded-lg border border-border bg-popover shadow-md"
                >
                  <DropdownMenuItem onClick={() => setTheme("light")} className="rounded-md cursor-pointer">Light</DropdownMenuItem>
                  <DropdownMenuItem onClick={() => setTheme("dark")} className="rounded-md cursor-pointer">Dark</DropdownMenuItem>
                  <DropdownMenuItem onClick={() => setTheme("system")} className="rounded-md cursor-pointer">System</DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </TooltipTrigger>
            {!isExpanded && (
              <TooltipContent side="right" className="bg-popover border border-border text-foreground">
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
                  className={navItemClass("/settings", isExpanded)}
                >
                  <Settings className={iconClass("/settings", isExpanded)} />
                  {isExpanded && <span>Settings</span>}
                  {!isExpanded && <span className="sr-only">Settings</span>}
                </Button>
              </Link>
            </TooltipTrigger>
            {!isExpanded && (
              <TooltipContent side="right" className="bg-popover border border-border text-foreground">
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
                } rounded-lg hover:bg-muted transition-colors text-foreground`}
              >
                <CircleQuestionMark
                  className={`w-5 h-5 text-muted-foreground ${isExpanded ? "mr-3" : ""}`}
                />
                {isExpanded && <span className="font-medium">Help</span>}
                {!isExpanded && <span className="sr-only">Help</span>}
              </Button>
            </TooltipTrigger>
            {!isExpanded && (
              <TooltipContent side="right" className="bg-popover border border-border text-foreground">
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
                } rounded-lg hover:bg-muted transition-colors ${
                  isExpanded ? "p-2" : "p-0"
                }`}
              >
                <Avatar className="w-8 h-8 rounded-lg border border-border">
                  <AvatarImage src="" alt={user?.username} />
                  <AvatarFallback className="bg-primary/10 text-primary font-semibold rounded-lg text-xs">
                    {nameToInitials(user?.full_name ?? "")}
                  </AvatarFallback>
                </Avatar>
                {isExpanded && (
                  <div className="ml-2 text-left overflow-hidden flex-1">
                    <div className="text-sm font-medium text-foreground truncate">
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
              className="w-64 rounded-xl border border-border bg-popover shadow-md"
              side="right"
              align="end"
              sideOffset={4}
            >
              <DropdownMenuLabel className="p-0 font-normal">
                <div className="flex items-center gap-3 px-3 py-3">
                  <Avatar className="h-9 w-9 rounded-lg border border-border">
                    <AvatarImage src="" alt={user?.full_name ?? "Not logged in"} />
                    <AvatarFallback className="bg-primary/10 text-primary font-semibold rounded-lg text-xs">
                      {nameToInitials(user?.full_name ?? "")}
                    </AvatarFallback>
                  </Avatar>
                  <div className="grid flex-1 text-sm leading-tight">
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
                <DropdownMenuItem asChild className="rounded-md cursor-pointer">
                  <Link to="/settings#account" className="flex items-center gap-3">
                    <BadgeCheck size={16} className="text-muted-foreground" />
                    <span>Account</span>
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuItem asChild className="rounded-md cursor-pointer">
                  <Link to="/settings#notifications" className="flex items-center gap-3">
                    <Bell size={16} className="text-muted-foreground" />
                    <span>Notifications</span>
                  </Link>
                </DropdownMenuItem>
              </DropdownMenuGroup>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={logout}
                className="rounded-md cursor-pointer text-destructive focus:text-destructive"
              >
                <LogOut size={16} />
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
