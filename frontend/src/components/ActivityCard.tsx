import { ArrowRight, Loader2 } from "lucide-react";
import DynamicIcon from "./DynamicIcon";
import {
  activityPastel,
  activityTypeLabel,
  type Activity,
} from "@/lib/activities";
import { cn } from "@/lib/utils";

interface ActivityCardProps {
  activity: Activity;
  onStart: (activityId: number) => void;
  isStarting?: boolean;
  disabled?: boolean;
}

// The whole card is the button: one tap target, sized for small hands.
// Its pastel comes from the activity id, so a story keeps its colour on
// every screen it shows up on.
const ActivityCard = ({
  activity,
  onStart,
  isStarting = false,
  disabled = false,
}: ActivityCardProps) => {
  const pastel = activityPastel(activity.id);

  return (
    <button
      type="button"
      onClick={() => onStart(activity.id)}
      disabled={disabled}
      aria-busy={isStarting}
      aria-label={`Start ${activity.title}`}
      className={cn(
        "group flex h-full w-full flex-col rounded-2xl p-5 text-left",
        "shadow-sm ring-1 ring-inset ring-black/5 dark:ring-white/10",
        "transition-all duration-200 outline-none",
        "hover:-translate-y-0.5 hover:shadow-lg active:translate-y-0 active:scale-[0.99]",
        "focus-visible:ring-[3px] focus-visible:ring-ring/60",
        "disabled:cursor-default disabled:hover:translate-y-0 disabled:hover:shadow-sm",
        disabled && !isStarting && "opacity-60"
      )}
      style={{ backgroundColor: pastel.background }}
    >
      <span
        className="flex size-10 items-center justify-center rounded-xl bg-white/60 dark:bg-black/20"
        style={{ color: pastel.foreground }}
      >
        <DynamicIcon
          name={activity.emoji_icon}
          className="size-5"
          fallback="BookOpen"
        />
      </span>

      <span className="mt-4 text-xs font-medium text-foreground/70">
        {activityTypeLabel(activity.activity_type)}
      </span>
      <span
        className="mt-0.5 text-lg font-semibold leading-snug"
        style={{ color: pastel.foreground }}
      >
        {activity.title}
      </span>
      <span className="mt-2 line-clamp-2 text-sm leading-relaxed text-foreground/70">
        {activity.description}
      </span>

      <span
        className="mt-auto inline-flex items-center gap-1.5 pt-5 text-sm font-semibold"
        style={{ color: pastel.foreground }}
      >
        {isStarting ? (
          <>
            <Loader2 className="size-4 animate-spin" />
            Starting…
          </>
        ) : (
          <>
            Start
            <ArrowRight className="size-4 transition-transform duration-200 group-hover:translate-x-0.5" />
          </>
        )}
      </span>
    </button>
  );
};

export default ActivityCard;
