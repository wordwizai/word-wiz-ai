import { Link } from "react-router-dom";
import { Button } from "./ui/button";
import {
  BadgeCheck,
  Bell,
  CircleQuestionMark,
  CreditCard,
  House,
  LogOut,
  MessageSquareMore,
  Route,
  Settings,
  Sparkles,
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
              <Button variant="ghost" size="icon">
                <span className="sr-only">Home</span>
                <House />
              </Button>
            </Link>
          </TooltipTrigger>
          <TooltipContent side="right">Home</TooltipContent>
        </Tooltip>
        <Tooltip delayDuration={300}>
          <TooltipTrigger asChild>
            <Link to="/practice">
              <Button variant="ghost" size="icon">
                <span className="sr-only">Practice</span>
                <Target />
              </Button>
            </Link>
          </TooltipTrigger>
          <TooltipContent side="right">Practice</TooltipContent>
        </Tooltip>
        <Tooltip delayDuration={300}>
          <TooltipTrigger asChild>
            <Link to="/feedback">
              <Button variant="ghost" size="icon">
                <span className="sr-only">Feedback</span>
                <MessageSquareMore />
              </Button>
            </Link>
          </TooltipTrigger>
          <TooltipContent side="right">Feedback</TooltipContent>
        </Tooltip>
        <Tooltip delayDuration={300}>
          <TooltipTrigger asChild>
            <Link to="progress">
              <Button variant="ghost" size="icon">
                <span className="sr-only">Progress</span>
                <Route />
              </Button>
            </Link>
          </TooltipTrigger>
          <TooltipContent side="right">Progress</TooltipContent>
        </Tooltip>
        {/* Bottom Buttons */}
        <div className="mt-auto space-y-2">
          {/* Settings */}
          <Tooltip delayDuration={300}>
            <TooltipTrigger asChild>
              <Link to="/settings">
                <Button variant="ghost" size="icon">
                  <span className="sr-only">Settings</span>
                  <Settings />
                </Button>
              </Link>
            </TooltipTrigger>
            <TooltipContent side="right">Settings</TooltipContent>
          </Tooltip>
          <Tooltip delayDuration={300}>
            <TooltipTrigger asChild>
              <Button variant="ghost" size="icon">
                <span className="sr-only">Help</span>
                <CircleQuestionMark />
              </Button>
            </TooltipTrigger>
            <TooltipContent side="right">Help</TooltipContent>
          </Tooltip>

          {/* Avatar Dropdown */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon">
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
                <DropdownMenuItem>
                  <Sparkles />
                  Upgrade to Pro
                </DropdownMenuItem>
              </DropdownMenuGroup>
              <DropdownMenuSeparator />
              <DropdownMenuGroup>
                <DropdownMenuItem>
                  <BadgeCheck />
                  Account
                </DropdownMenuItem>
                <DropdownMenuItem>
                  <CreditCard />
                  Billing
                </DropdownMenuItem>
                <DropdownMenuItem>
                  <Bell />
                  Notifications
                </DropdownMenuItem>
              </DropdownMenuGroup>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={logout}>
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

export default Sidebar;
