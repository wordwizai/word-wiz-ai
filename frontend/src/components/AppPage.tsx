import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

// Shared frame for the signed-in pages. One width, one gutter, one rhythm,
// so moving between Dashboard, Practice, Progress, Classes and Settings
// never shifts the content edge.
export const AppPage = ({
  children,
  className,
  width = "default",
}: {
  children: ReactNode;
  className?: string;
  width?: "default" | "narrow";
}) => (
  <main
    className={cn(
      "mx-auto w-full px-4 pt-6 pb-10 sm:px-8 sm:pt-10 space-y-10",
      width === "narrow" ? "max-w-3xl" : "max-w-6xl",
      className
    )}
  >
    {children}
  </main>
);

export const PageHeader = ({
  title,
  description,
  actions,
}: {
  title: ReactNode;
  description?: ReactNode;
  actions?: ReactNode;
}) => (
  <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
    <div className="min-w-0 space-y-1.5">
      <h1 className="text-3xl md:text-4xl font-bold tracking-tight text-foreground">
        {title}
      </h1>
      {description && (
        <p className="text-base text-muted-foreground max-w-prose">
          {description}
        </p>
      )}
    </div>
    {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
  </header>
);

export const SectionHeader = ({
  title,
  action,
  id,
}: {
  title: ReactNode;
  action?: ReactNode;
  id?: string;
}) => (
  <div className="mb-4 flex items-baseline justify-between gap-4">
    <h2 id={id} className="text-xl font-semibold text-foreground">
      {title}
    </h2>
    {action}
  </div>
);
