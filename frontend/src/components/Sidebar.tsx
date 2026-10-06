import { useContext, useState, type ComponentType } from "react";
import { Link, useLocation } from "react-router-dom";
import {
  LogOut,
  Monitor,
  Moon,
  PanelLeftClose,
  PanelLeftOpen,
  Settings,
  Sun,
  UserRound,
} from "lucide-react";
import { Button } from "./ui/button";
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
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "./ui/dropdown-menu";
import { AuthContext, type AuthContextType } from "@/contexts/AuthContext";
import { useTheme } from "@/contexts/ThemeContext";
import { cn, nameToInitials } from "@/lib/utils";
import { wordWizIcon } from "@/assets";
import { APP_NAV } from "@/config/appNav";

type IconType = ComponentType<{ className?: string }>;

const THEME_LABELS = { light: "Light", dark: "Dark", system: "System" };
const COLLAPSED_KEY = "sidebar-collapsed";

const readCollapsed = () => {
  try {
    return localStorage.getItem(COLLAPSED_KEY) === "1";
  } catch {
    return false;
  }
};

// Shared row styling, so links, the theme menu and the account menu all
// line up on the same 44px grid.
const rowClass = (collapsed: boolean, active = false) =>
  cn(
    "flex h-11 items-center gap-3 rounded-xl text-sm font-medium transition-colors outline-none",
    "focus-visible:ring-[3px] focus-visible:ring-ring/50",
    collapsed ? "mx-auto w-11 justify-center" : "w-full px-3",
    active
      ? "bg-sidebar-accent text-sidebar-accent-foreground"
      : "text-muted-foreground hover:bg-muted hover:text-foreground"
  );

const WithTooltip = ({
  label,
  show,
  children,
}: {
  label: string;
  show: boolean;
  children: React.ReactElement;
}) =>
  show ? (
    <Tooltip delayDuration={200}>
      <TooltipTrigger asChild>{children}</TooltipTrigger>
      <TooltipContent side="right">{label}</TooltipContent>
    </Tooltip>
  ) : (
    children
  );

const NavLink = ({
  to,
  label,
  icon: Icon,
  collapsed,
  active,
}: {
  to: string;
  label: string;
  icon: IconType;
  collapsed: boolean;
  active: boolean;
}) => (
  <WithTooltip label={label} show={collapsed}>
    <Link
      to={to}
      aria-current={active ? "page" : undefined}
      className={rowClass(collapsed, active)}
    >
      <Icon
        className={cn("size-5 shrink-0", active && "text-primary dark:text-current")}
      />
      {collapsed ? <span className="sr-only">{label}</span> : label}
    </Link>
  </WithTooltip>
);

const Sidebar = ({ className }: { className?: string }) => {
  const { user, logout } = useContext<AuthContextType>(AuthContext);
  const { theme, setTheme } = useTheme();
  const { pathname } = useLocation();
  const [collapsed, setCollapsed] = useState(readCollapsed);

  const toggleCollapsed = () => {
    setCollapsed((prev) => {
      try {
        localStorage.setItem(COLLAPSED_KEY, prev ? "0" : "1");
      } catch {
        // Private mode or blocked storage: the toggle still works this visit.
      }
      return !prev;
    });
  };

  const isActive = (path: string) =>
    pathname === path || pathname.startsWith(path + "/");

  const ThemeIcon = theme === "dark" ? Moon : theme === "light" ? Sun : Monitor;

  return (
    <TooltipProvider>
      <aside
        className={cn(
          "flex h-full flex-col border-r border-sidebar-border bg-sidebar p-3 transition-[width] duration-200",
          collapsed ? "w-[76px]" : "w-64",
          className
        )}
      >
        <div
          className={cn(
            "mb-6 flex h-12 items-center",
            collapsed ? "justify-center" : "justify-between pl-2"
          )}
        >
          {!collapsed && (
            <Link
              to="/dashboard"
              className="flex min-w-0 items-center gap-2.5 rounded-lg outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50"
            >
              <img src={wordWizIcon} alt="" className="size-9 shrink-0" />
              <span className="truncate text-base font-semibold text-foreground">
                Word Wiz AI
              </span>
            </Link>
          )}
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleCollapsed}
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            className="shrink-0 rounded-xl text-muted-foreground hover:text-foreground"
          >
            {collapsed ? (
              <PanelLeftOpen className="size-5" />
            ) : (
              <PanelLeftClose className="size-5" />
            )}
          </Button>
        </div>

        <nav aria-label="Main" className="flex flex-col gap-1">
          {APP_NAV.map((item) => (
            <NavLink
              key={item.to}
              {...item}
              collapsed={collapsed}
              active={isActive(item.to)}
            />
          ))}
        </nav>

        <div className="mt-auto flex flex-col gap-1 border-t border-sidebar-border pt-3">
          <NavLink
            to="/settings"
            label="Settings"
            icon={Settings}
            collapsed={collapsed}
            active={isActive("/settings")}
          />

          <DropdownMenu>
            <WithTooltip label="Theme" show={collapsed}>
              <DropdownMenuTrigger className={rowClass(collapsed)}>
                <ThemeIcon className="size-5 shrink-0" />
                {collapsed ? (
                  <span className="sr-only">Theme</span>
                ) : (
                  <>
                    Theme
                    <span className="ml-auto text-xs font-normal">
                      {THEME_LABELS[theme]}
                    </span>
                  </>
                )}
              </DropdownMenuTrigger>
            </WithTooltip>
            <DropdownMenuContent side="right" align="end" className="w-40">
              <DropdownMenuRadioGroup
                value={theme}
                onValueChange={(value) =>
                  setTheme(value as keyof typeof THEME_LABELS)
                }
              >
                {Object.entries(THEME_LABELS).map(([value, label]) => (
                  <DropdownMenuRadioItem key={value} value={value}>
                    {label}
                  </DropdownMenuRadioItem>
                ))}
              </DropdownMenuRadioGroup>
            </DropdownMenuContent>
          </DropdownMenu>

          <DropdownMenu>
            <DropdownMenuTrigger
              className={cn(
                rowClass(collapsed),
                "mt-1 h-14 text-left",
                collapsed ? "w-14" : "px-2"
              )}
            >
              <span className="flex size-9 shrink-0 items-center justify-center rounded-full bg-primary/10 text-sm font-semibold text-primary">
                {nameToInitials(user?.full_name ?? "") || (
                  <UserRound className="size-4" />
                )}
              </span>
              {collapsed ? (
                <span className="sr-only">Account</span>
              ) : (
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-sm font-medium text-foreground">
                    {user?.full_name ?? "Account"}
                  </span>
                  <span className="block truncate text-xs font-normal">
                    {user?.email ?? ""}
                  </span>
                </span>
              )}
            </DropdownMenuTrigger>
            <DropdownMenuContent side="right" align="end" className="w-56">
              <DropdownMenuLabel className="truncate font-normal text-muted-foreground">
                {user?.email ?? "Signed in"}
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

export default Sidebar;
