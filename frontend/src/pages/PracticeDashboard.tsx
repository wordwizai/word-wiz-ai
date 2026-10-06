import { AppPage, PageHeader, SectionHeader } from "@/components/AppPage";
import ActivitiesList from "@/components/ActivitiesList";
import { useActivities } from "@/hooks/useActivities";

// Every activity is visible at once, grouped by kind. A carousel hid most
// of them behind arrows, and there are few enough to show in a grid.
const SECTIONS = [
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
  {
    type: "unlimited",
    title: "Free practice",
    description: "New sentences that keep coming, aimed at the sounds your child misses.",
  },
];

const PracticeDashboard = () => {
  const { activities } = useActivities();

  return (
    <AppPage>
      <PageHeader
        title="Practice"
        description="Pick a story or free practice. Every activity listens to your child read and points out the sounds to work on."
      />

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
