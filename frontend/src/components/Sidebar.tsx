import { Link } from "react-router-dom";
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
import { useContext } from "react";
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

  return (
    <TooltipProvider>
      <aside
        className={`w-20 flex flex-col items-center bg-sidebar p-4 space-y-6 border-r-2 border-border ${className}`}
      >
        {/* Logo/Brand */}
        <div className="relative mb-4">
          <a
            href="./"
            className="w-12 h-12 bg-gradient-to-br from-primary/60 to-purple-300 rounded-2xl flex items-center justify-center shadow-md hover:shadow-lg transition-shadow"
          >
            <img src={wordWizIcon} alt="Word Wiz" className="w-10 h-10" />
          </a>
        </div>

        {/* Navigation Items */}
        <div className="flex flex-col items-center space-y-4">
          <Tooltip delayDuration={300}>
            <TooltipTrigger asChild>
              <Link to="/dashboard">
                <Button
                  variant="ghost"
                  size="icon"
                  className="w-12 h-12 rounded-xl hover:bg-purple-100/50 transition-colors"
                >
                  <span className="sr-only">Dashboard</span>
                  <House className="w-5 h-5 text-purple-600" />
                </Button>
              </Link>
            </TooltipTrigger>
            <TooltipContent
              side="right"
              className="bg-card border-2 border-border text-foreground"
            >
              <p>Dashboard</p>
            </TooltipContent>
          </Tooltip>

          <Tooltip delayDuration={300}>
            <TooltipTrigger asChild>
              <Link to="/practice">
                <Button
                  variant="ghost"
                  size="icon"
                  className="w-12 h-12 rounded-xl hover:bg-blue-100/50 transition-colors"
                >
                  <span className="sr-only">Practice</span>
                  <Target className="w-5 h-5 text-blue-600" />
                </Button>
              </Link>
            </TooltipTrigger>
            <TooltipContent
              side="right"
              className="bg-card border-2 border-border text-foreground"
            >
              <p>Practice</p>
            </TooltipContent>
          </Tooltip>

          <Tooltip delayDuration={300}>
            <TooltipTrigger asChild>
              <Link to="progress">
                <Button
                  variant="ghost"
                  size="icon"
                  className="w-12 h-12 rounded-xl hover:bg-green-100/50 transition-colors"
                >
                  <span className="sr-only">Progress</span>
                  <BarChart3 className="w-5 h-5 text-green-600" />
                </Button>
              </Link>
            </TooltipTrigger>
            <TooltipContent
              side="right"
              className="bg-card border-2 border-border text-foreground"
            >
              <p>Progress</p>
            </TooltipContent>
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
                    size="icon"
                    className="w-12 h-12 rounded-xl hover:bg-amber-100/50 transition-colors mb-0"
                  >
                    <Sun className="w-5 h-5 scale-100 rotate-0 transition-all dark:scale-0 dark:-rotate-90 text-amber-600" />
                    <Moon className="absolute w-5 h-5 scale-0 rotate-90 transition-all dark:scale-100 dark:rotate-0 text-amber-600" />
                    <span className="sr-only">Toggle theme</span>
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
            <TooltipContent
              side="right"
              className="bg-card border-2 border-border text-foreground"
            >
              <p>Theme</p>
            </TooltipContent>
          </Tooltip>

          {/* Settings */}
          <Tooltip delayDuration={300}>
            <TooltipTrigger asChild>
              <Link to="/settings">
                <Button
                  variant="ghost"
                  size="icon"
                  className="w-12 h-12 rounded-xl hover:bg-purple-100/50 transition-colors"
                >
                  <span className="sr-only">Settings</span>
                  <Settings className="w-5 h-5 text-purple-600" />
                </Button>
              </Link>
            </TooltipTrigger>
            <TooltipContent
              side="right"
              className="bg-card border-2 border-border text-foreground"
            >
              <p>Settings</p>
            </TooltipContent>
          </Tooltip>

          <Tooltip delayDuration={300}>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="w-12 h-12 rounded-xl hover:bg-purple-100/50 transition-colors"
              >
                <span className="sr-only">Help</span>
                <CircleQuestionMark className="w-5 h-5 text-purple-600" />
              </Button>
            </TooltipTrigger>
            <TooltipContent
              side="right"
              className="bg-card border-2 border-border text-foreground"
            >
              <p>Help</p>
            </TooltipContent>
          </Tooltip>

          {/* Avatar Dropdown */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                className="w-12 h-12 rounded-xl hover:bg-purple-100/50 transition-colors p-0"
              >
                <span className="sr-only">Account</span>
                <Avatar className="w-10 h-10 border-2 border-primary rounded-xl">
                  <AvatarImage src="" alt={user?.username} />
                  <AvatarFallback className="bg-primary/10 text-primary font-bold rounded-xl">
                    {nameToInitials(user?.full_name ?? "")}
                  </AvatarFallback>
                </Avatar>
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
