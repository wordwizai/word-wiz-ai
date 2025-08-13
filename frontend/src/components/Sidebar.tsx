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
        className={`w-20 flex flex-col items-center bg-gradient-to-b from-background via-background to-accent/10 p-4 space-y-6 border-r-2 border-purple-100/50 ${className}`}
      >
        {/* Logo/Brand */}
        <div className="relative mb-4">
          <div className="w-12 h-12 bg-gradient-to-br from-primary/60 to-purple-300 rounded-2xl flex items-center justify-center shadow-lg">
            <img src={wordWizIcon} alt="Word Wiz" className="w-10 h-10" />
          </div>
        </div>

        {/* Navigation Items */}
        <div className="flex flex-col items-center space-y-4">
          <Tooltip delayDuration={300}>
            <TooltipTrigger asChild>
              <Link to="/dashboard">
                <Button
                  variant="ghost"
                  size="iconLg"
                  className="w-12 h-12 rounded-2xl hover:bg-purple-100/50 hover:shadow-md transition-all duration-200 group"
                >
                  <span className="sr-only">Dashboard</span>
                  <House className="size-5 text-purple-600 group-hover:scale-110 transition-transform duration-200" />
                </Button>
              </Link>
            </TooltipTrigger>
            <TooltipContent
              side="right"
              className="bg-white border-2 border-purple-200 text-purple-800"
            >
              <div className="flex items-center gap-2">Dashboard</div>
            </TooltipContent>
          </Tooltip>

          <Tooltip delayDuration={300}>
            <TooltipTrigger asChild>
              <Link to="/practice">
                <Button
                  variant="ghost"
                  size="iconLg"
                  className="w-12 h-12 rounded-2xl hover:bg-blue-100/50 hover:shadow-md transition-all duration-200 group"
                >
                  <span className="sr-only">Practice</span>
                  <Target className="size-5 text-blue-600 group-hover:scale-110 transition-transform duration-200" />
                </Button>
              </Link>
            </TooltipTrigger>
            <TooltipContent
              side="right"
              className="bg-white border-2 border-blue-200 text-blue-800"
            >
              <div className="flex items-center gap-2">
                <Target className="w-3 h-3" />
                Practice
              </div>
            </TooltipContent>
          </Tooltip>

          <Tooltip delayDuration={300}>
            <TooltipTrigger asChild>
              <Link to="progress">
                <Button
                  variant="ghost"
                  size="iconLg"
                  className="w-12 h-12 rounded-2xl hover:bg-green-100/50 hover:shadow-md transition-all duration-200 group"
                >
                  <span className="sr-only">Progress</span>
                  <BarChart3 className="size-5 text-green-600 group-hover:scale-110 transition-transform duration-200" />
                </Button>
              </Link>
            </TooltipTrigger>
            <TooltipContent
              side="right"
              className="bg-white border-2 border-green-200 text-green-800"
            >
              <div className="flex items-center gap-2">
                <BarChart3 className="w-3 h-3" />
                Progress
              </div>
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
                    size="iconLg"
                    className="w-12 h-12 rounded-2xl transition-all duration-200 mb-0"
                  >
                    <Sun className="size-5 scale-100 rotate-0 transition-all dark:scale-0 dark:-rotate-90 text-primary" />
                    <Moon className="absolute size-5 scale-0 rotate-90 transition-all dark:scale-100 dark:rotate-0 text-primary" />
                    <span className="sr-only">Toggle theme</span>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent
                  align="end"
                  className="w-32 rounded-2xl border-2 border-gray-200 bg-white/95 shadow-xl"
                >
                  <DropdownMenuItem
                    onClick={() => setTheme("light")}
                    className="hover:bg-gray-50 rounded-lg mx-2 text-black"
                  >
                    Light
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    onClick={() => setTheme("dark")}
                    className="hover:bg-gray-50 rounded-lg mx-2 text-black"
                  >
                    Dark
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    onClick={() => setTheme("system")}
                    className="hover:bg-gray-50 rounded-lg mx-2 text-black"
                  >
                    System
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </TooltipTrigger>
            <TooltipContent
              side="right"
              className="bg-white border-2 border-gray-200 text-gray-800"
            >
              Theme toggle
            </TooltipContent>
          </Tooltip>

          {/* Settings */}
          <Tooltip delayDuration={300}>
            <TooltipTrigger asChild>
              <Link to="/settings">
                <Button
                  variant="ghost"
                  size="iconLg"
                  className="w-12 h-12 rounded-2xl hover:bg-primary/10 hover:shadow-md transition-all duration-200 group"
                >
                  <span className="sr-only">Settings</span>
                  <Settings className="size-5 text-primary group-hover:scale-110 transition-transform duration-200" />
                </Button>
              </Link>
            </TooltipTrigger>
            <TooltipContent
              side="right"
              className="bg-white border-2 border-primary/20 text-primary"
            >
              <div className="flex items-center gap-2">Settings</div>
            </TooltipContent>
          </Tooltip>

          <Tooltip delayDuration={300}>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="iconLg"
                className="w-12 h-12 rounded-2xl hover:bg-primary/10 hover:shadow-md transition-all duration-200 group"
              >
                <span className="sr-only">Help</span>
                <CircleQuestionMark className="size-5 text-primary group-hover:scale-110 transition-transform duration-200" />
              </Button>
            </TooltipTrigger>
            <TooltipContent
              side="right"
              className="bg-white border-2 border-primary/20 text-primary"
            >
              <div className="flex items-center gap-2">Help</div>
            </TooltipContent>
          </Tooltip>

          {/* Avatar Dropdown */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="iconLg"
                className="w-12 h-12 rounded-2xl hover:bg-purple-100/50 hover:shadow-md transition-all duration-200 group"
              >
                <span className="sr-only">Account</span>
                <Avatar className="w-8 h-8 mx-auto rounded-xl group-hover:scale-110 transition-transform duration-200">
                  <AvatarImage src="" alt={user?.username} />
                  <AvatarFallback className="bg-gradient-to-br from-purple-400 to-pink-500 text-white font-semibold">
                    {nameToInitials(user?.full_name ?? "")}
                  </AvatarFallback>
                </Avatar>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent
              className="w-64 rounded-2xl border-2 border-purple-200 bg-white/95 shadow-xl"
              side="right"
              align="end"
              sideOffset={4}
            >
              <DropdownMenuLabel className="p-0 font-normal">
                <div className="flex items-center gap-3 px-3 py-3 text-left">
                  <Avatar className="h-10 w-10 rounded-xl">
                    <AvatarImage
                      src={""}
                      alt={user?.full_name ?? "Not logged in"}
                    />
                    <AvatarFallback className="rounded-xl bg-gradient-to-br from-purple-400 to-pink-500 text-white font-semibold">
                      {nameToInitials(user?.full_name ?? "")}
                    </AvatarFallback>
                  </Avatar>
                  <div className="grid flex-1 text-left text-sm leading-tight">
                    <span className="truncate font-semibold text-gray-800">
                      {user?.full_name ?? "Not logged in"}
                    </span>
                    <span className="truncate text-xs text-gray-600">
                      {user?.email ?? "Not logged in"}
                    </span>
                  </div>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator className="bg-purple-200/50" />
              <DropdownMenuGroup>
                <DropdownMenuItem
                  asChild
                  className="hover:bg-purple-50 rounded-lg mx-2"
                >
                  <Link
                    to="/settings#account"
                    className="flex items-center gap-3"
                  >
                    <BadgeCheck size={18} className="text-purple-600" />
                    <span className="text-gray-700">Account</span>
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuItem
                  asChild
                  className="hover:bg-purple-50 rounded-lg mx-2"
                >
                  <Link
                    to="/settings#notifications"
                    className="flex items-center gap-3"
                  >
                    <Bell size={18} className="text-purple-600" />
                    <span className="text-gray-700">Notifications</span>
                  </Link>
                </DropdownMenuItem>
              </DropdownMenuGroup>
              <DropdownMenuSeparator className="bg-purple-200/50" />
              <DropdownMenuItem
                onClick={logout}
                className="hover:bg-red-50 rounded-lg mx-2"
              >
                <LogOut size={18} className="text-red-600" />
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
