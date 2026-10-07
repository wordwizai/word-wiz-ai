import { Link } from "react-router-dom";
import { ChevronRight } from "lucide-react";
import { AppPage, PageHeader, SectionHeader } from "@/components/AppPage";
import ActivitiesList, {
  ActivitiesLoadError,
} from "@/components/ActivitiesList";
import ContinuePathCard from "@/components/phonics/ContinuePathCard";
import TeacherAssignments from "@/components/phonics/TeacherAssignments";
import { useActivities } from "@/hooks/useActivities";
import { useMyAssignments, usePhonicsPath } from "@/hooks/usePhonics";

// Every activity is visible at once, grouped by kind. A carousel hid most
// of them behind arrows, and there are few enough to show in a grid.
// Free practice goes first. It's a single card, and below the ~40 story
// cards nobody scrolled far enough to find it.
const SECTIONS = [
  {
    type: "unlimited",
    title: "Free practice",
    description: "New sentences that keep coming, aimed at the sounds your child misses.",
  },
  {
    type: "choice-story",
    title: "Choice stories",
    description: "Your child picks what happens next.",
  },
  {
    type: "story",
    title: "Stories",
    description: "Classic tales, read one sentence at a time.",
  },
];

const PracticeDashboard = () => {
  const { activities, failed } = useActivities();
  const { assignments } = useMyAssignments();
  const { path, failed: pathFailed } = usePhonicsPath();

  return (
    <AppPage title="Practice">
      <PageHeader
        title="Practice"
        description="Follow the phonics path one sound at a time, or pick a story or free practice. Every activity listens to your child read and points out the sounds to work on."
      />

      <TeacherAssignments assignments={assignments} />

      {!pathFailed && (
        <section aria-labelledby="phonics-heading">
          <SectionHeader
            id="phonics-heading"
            title="Phonics path"
            action={
              <Link
                to="/practice/phonics"
                className="inline-flex min-h-11 items-center gap-1 text-sm font-semibold text-primary hover:underline underline-offset-4"
              >
                All units
                <ChevronRight className="size-4" />
              </Link>
            }
          />
          <p className="-mt-2 mb-4 text-sm text-muted-foreground">
            One sound at a time, in the order schools teach them.
          </p>
          <ContinuePathCard path={path} />
        </section>
      )}

      {failed && <ActivitiesLoadError />}

      {SECTIONS.map((section) => {
        const items = activities?.filter(
          (a) => a.activity_type === section.type
        );
        if (items && items.length === 0) return null;
        return (
          <section key={section.type} aria-labelledby={`${section.type}-heading`}>
            <SectionHeader id={`${section.type}-heading`} title={section.title} />
            <p className="-mt-2 mb-4 text-sm text-muted-foreground">
              {section.description}
            </p>
            <ActivitiesList activities={items ?? null} />
          </section>
        );
      })}
    </AppPage>
  );
};

export default PracticeDashboard;
