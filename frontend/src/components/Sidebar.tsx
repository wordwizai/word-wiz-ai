import { Link } from "react-router-dom";
import { Button } from "./ui/button";
import {
  BadgeCheck,
  Bell,
  CircleQuestionMark,
  House,
  LogOut,
  MessageSquareMore,
  Route,
  Settings,
  Target,
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
import { nameToInitials } from "@/lib/utils";
import { ModeToggle } from "./ModeToggle";

const Sidebar = () => {
  // get the user
  const { user, logout } = useContext<AuthContextType>(AuthContext);

  return (
    <TooltipProvider>
      <aside className="w-16 flex flex-col items-center bg-background p-4 space-y-4">
        {/* Home */}
        <Tooltip delayDuration={300}>
          <TooltipTrigger asChild>
            <Link to="/dashboard">
              <Button variant="ghost" size="iconLg">
                <span className="sr-only">Dashboard</span>
                <House className="size-5" />
              </Button>
            </Link>
          </TooltipTrigger>
          <TooltipContent side="right">Dashboard</TooltipContent>
        </Tooltip>
        <Tooltip delayDuration={300}>
          <TooltipTrigger asChild>
            <Link to="/practice">
              <Button variant="ghost" size="iconLg">
                <span className="sr-only">Practice</span>
                <Target className="size-5" />
              </Button>
            </Link>
          </TooltipTrigger>
          <TooltipContent side="right">Practice</TooltipContent>
        </Tooltip>
        <Tooltip delayDuration={300}>
          <TooltipTrigger asChild>
            <Link to="progress">
              <Button variant="ghost" size="iconLg">
                <span className="sr-only">Progress</span>
                <Route className="size-5" />
              </Button>
            </Link>
          </TooltipTrigger>
          <TooltipContent side="right">Progress</TooltipContent>
        </Tooltip>
        {/* Bottom Buttons */}
        <div className="mt-auto space-y-2">
          {/* Theme Toggle */}
          <Tooltip delayDuration={300}>
            <TooltipTrigger asChild>
              <ModeToggle />
            </TooltipTrigger>
            <TooltipContent side="right">Theme toggle</TooltipContent>
          </Tooltip>

          {/* Settings */}
          <Tooltip delayDuration={300}>
            <TooltipTrigger asChild>
              <Link to="/settings">
                <Button variant="ghost" size="iconLg">
                  <span className="sr-only">Settings</span>
                  <Settings className="size-5" />
                </Button>
              </Link>
            </TooltipTrigger>
            <TooltipContent side="right">Settings</TooltipContent>
          </Tooltip>
          <Tooltip delayDuration={300}>
            <TooltipTrigger asChild>
              <Button variant="ghost" size="iconLg">
                <span className="sr-only">Help</span>
                <CircleQuestionMark className="size-5" />
              </Button>
            </TooltipTrigger>
            <TooltipContent side="right">Help</TooltipContent>
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
              {/* <DropdownMenuSeparator /> */}
              {/* <DropdownMenuGroup> */}
              {/*   <DropdownMenuItem> */}
              {/*     <Sparkles size={20} /> */}
              {/* Upgrade to Pro */}
              {/*   </DropdownMenuItem> */}
              {/* </DropdownMenuGroup> */}
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

export default Sidebar;
