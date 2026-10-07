import { AppPage, PageHeader } from "@/components/AppPage";
import PhonicsPathView from "@/components/phonics/PhonicsPathView";
import { Skeleton } from "@/components/ui/skeleton";
import { usePhonicsPath, useStartPattern } from "@/hooks/usePhonics";

const PhonicsPathPage = () => {
  const { path, failed } = usePhonicsPath();
  const { start, startingSlug } = useStartPattern();

  return (
    <AppPage title="Phonics path" width="narrow">
      <PageHeader
        title="Phonics path"
        description="The sounds in the order schools teach them, from short a word families to vowel teams. Each pattern is a short set of words and sentences to read out loud."
      />
      {failed ? (
        <div className="rounded-2xl border border-dashed px-6 py-10 text-center">
          <p className="font-medium text-foreground">Couldn't load the phonics path</p>
          <p className="mt-1 text-sm text-muted-foreground">
            Check your connection and refresh the page.
          </p>
        </div>
      ) : path ? (
        <PhonicsPathView
          path={path}
          audience="student"
          onStart={start}
          startingSlug={startingSlug}
        />
      ) : (
        <div className="space-y-3">
          {Array.from({ length: 6 }, (_, i) => (
            <Skeleton key={i} className="h-16 rounded-2xl" />
          ))}
        </div>
      )}
    </AppPage>
  );
};

export default PhonicsPathPage;
