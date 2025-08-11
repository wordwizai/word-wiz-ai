import { Link, useLocation } from "react-router-dom";
import { Button } from "./ui/button";
import {
  BadgeCheck,
  Bell,
  CircleQuestionMark,
  House,
  LogOut,
  Moon,
  Route,
  Settings,
  Sun,
  Target,
} from "lucide-react";
import { useContext } from "react";
import { motion } from "framer-motion";
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
import { useTheme } from "@/contexts/ThemeContext";

interface MobileNavProps {
  className?: string;
}

const MobileNav = ({ className }: MobileNavProps) => {
  const { user, logout } = useContext<AuthContextType>(AuthContext);

  return (
    <TooltipProvider>
      <aside className={`${className}`}>
        <div className="mx-5 mb-1 p-1 flex flex-row items-center justify-around bg-primary-foreground rounded-lg shadow-md shadow-primary/50 dark:shadow-none">
          {/* Home */}
          <Tooltip delayDuration={300}>
            <TooltipTrigger asChild>
              <Link to="/dashboard">
                <span className="sr-only">Dashboard</span>
                <House className="size-6 stroke-primary" />
              </Link>
            </TooltipTrigger>
            <TooltipContent side="right">Dashboard</TooltipContent>
          </Tooltip>
          <Tooltip delayDuration={300}>
            <TooltipTrigger asChild>
              <Link to="/practice">
                <span className="sr-only">Practice</span>
                <Target className="size-6 stroke-primary" />
              </Link>
            </TooltipTrigger>
            <TooltipContent side="right">Practice</TooltipContent>
          </Tooltip>
          <Tooltip delayDuration={300}>
            <TooltipTrigger asChild>
              <Link to="progress">
                <span className="sr-only">Progress</span>
                <Route className="size-6 stroke-primary" />
              </Link>
            </TooltipTrigger>
            <TooltipContent side="right">Progress</TooltipContent>
          </Tooltip>
          <Tooltip delayDuration={300}>
            <TooltipTrigger asChild>
              <Link to="/settings">
                <span className="sr-only">Settings</span>
                <Settings className="size-6 stroke-primary" />
              </Link>
            </TooltipTrigger>
            <TooltipContent side="right">Settings</TooltipContent>
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
                <DropdownMenuItem asChild className="hover:bg-purple-50 rounded-lg mx-2">
                  <Link to="/settings#account" className="flex items-center gap-3">
                    <BadgeCheck size={18} className="text-purple-600" />
                    <span className="text-gray-700">Account</span>
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuItem asChild className="hover:bg-purple-50 rounded-lg mx-2">
                  <Link to="/settings#notifications" className="flex items-center gap-3">
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

export default MobileNav;
