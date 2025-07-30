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
  const { theme, setTheme } = useTheme();

  return (
    <TooltipProvider>
      <aside className={`${className}`}>
        <div className="mx-5 mb-1 p-1 flex flex-row items-center justify-around bg-background rounded-lg shadow-md shadow-primary/50 dark:shadow-none">
          {/* Home */}
          <Tooltip delayDuration={300}>
            <TooltipTrigger asChild>
              <Link to="/dashboard">
                <span className="sr-only">Dashboard</span>
                <House className="size-6" />
              </Link>
            </TooltipTrigger>
            <TooltipContent side="right">Dashboard</TooltipContent>
          </Tooltip>
          <Tooltip delayDuration={300}>
            <TooltipTrigger asChild>
              <Link to="/practice">
                <span className="sr-only">Practice</span>
                <Target className="size-6" />
              </Link>
            </TooltipTrigger>
            <TooltipContent side="right">Practice</TooltipContent>
          </Tooltip>
          <Tooltip delayDuration={300}>
            <TooltipTrigger asChild>
              <Link to="progress">
                <span className="sr-only">Progress</span>
                <Route className="size-6" />
              </Link>
            </TooltipTrigger>
            <TooltipContent side="right">Progress</TooltipContent>
          </Tooltip>
          <Tooltip delayDuration={300}>
            <TooltipTrigger asChild>
              <Link to="/settings">
                <span className="sr-only">Settings</span>
                <Settings className="size-6" />
              </Link>
            </TooltipTrigger>
            <TooltipContent side="right">Settings</TooltipContent>
          </Tooltip>
          {/* Avatar Dropdown */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="iconLg">
                <span className="sr-only">Account</span>
                <Avatar className="w-8 h-8 mx-auto rounded-md">
                  <AvatarImage src="" alt={user?.username} />
                  <AvatarFallback>
                    {nameToInitials(user?.full_name ?? "")}
                  </AvatarFallback>
                </Avatar>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent
              className="w-(--radix-dropdown-menu-trigger-width) min-w-56 rounded-lg"
              side="right"
              align="end"
              sideOffset={4}
            >
              <DropdownMenuLabel className="p-0 font-normal">
                <div className="flex items-center gap-2 px-1 py-1.5 text-left text-sm">
                  <Avatar className="h-8 w-8 rounded-lg">
                    <AvatarImage
                      src={""}
                      alt={user?.full_name ?? "Not logged in"}
                    />
                    <AvatarFallback className="rounded-lg">
                      {nameToInitials(user?.full_name ?? "")}
                    </AvatarFallback>
                  </Avatar>
                  <div className="grid flex-1 text-left text-sm leading-tight">
                    <span className="truncate font-medium">
                      {user?.full_name ?? "Not logged in"}
                    </span>
                    <span className="truncate text-xs">
                      {user?.email ?? "Not logged in"}
                    </span>
                  </div>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuGroup>
                <DropdownMenuItem asChild>
                  <Link to="/settings#account">
                    <BadgeCheck size={20} />
                    Account
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuItem asChild>
                  <Link to="/settings#notifications">
                    <Bell size={20} />
                    Notifications
                  </Link>
                </DropdownMenuItem>
              </DropdownMenuGroup>
              <DropdownMenuSeparator />
              <DropdownMenuItem asChild>
                <Link to="/help">
                  <CircleQuestionMark size={20} />
                  Help
                </Link>
              </DropdownMenuItem>
              {/*
                            <DropdownMenuItem asChild>
                              <DropdownMenu>
                                <DropdownMenuTrigger asChild>
                                  <div>
                                    <div className="relative w-5 inline-block">
                                      <Sun
                                        className="absolute scale-100 rotate-0 transition-all dark:scale-0 dark:-rotate-90"
                                        size={20}
                                      />
                                      <Moon
                                        className="absolute scale-0 rotate-90 transition-all dark:scale-100 dark:rotate-0"
                                        size={20}
                                      />
                                    </div>
                                    {theme.charAt(0).toUpperCase() + theme.slice(1)}
                                  </div>
                                </DropdownMenuTrigger>
                                <DropdownMenuContent align="end">
                                  <DropdownMenuItem onClick={() => setTheme("light")}>
                                    Light
                                  </DropdownMenuItem>
                                  <DropdownMenuItem onClick={() => setTheme("dark")}>
                                    Dark
                                  </DropdownMenuItem>
                                  <DropdownMenuItem onClick={() => setTheme("system")}>
                                    System
                                  </DropdownMenuItem>
                                </DropdownMenuContent>
                              </DropdownMenu>
                            </DropdownMenuItem>
              */}
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={logout}>
                <LogOut size={20} />
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
