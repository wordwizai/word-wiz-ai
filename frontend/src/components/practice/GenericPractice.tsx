import { type Session } from "@/api";
import BasePractice from "@/components/practice/BasePractice";
import ChoiceStoryBasePractice from "@/components/practice/ChoiceStoryBasePractice";
import PracticeStage from "@/components/practice/PracticeStage";
import { LocalProcessingAlert } from "@/components/LocalProcessingAlert";
import { getPracticeConfig } from "@/config/practiceTypes";
import PatternFinish from "@/components/practice/PatternFinish";
import { lineLabel } from "@/lib/phonics";

interface GenericPracticeProps {
  session: Session;
  activityType: string;
}

// Picks the session logic for the activity type; every type renders the
// same PracticeStage so the screen looks and works the same everywhere.
const GenericPractice = ({ session, activityType }: GenericPracticeProps) => {
  const config = getPracticeConfig(activityType);

  if (config.basePracticeComponent === "ChoiceStoryBasePractice") {
    return (
      <ChoiceStoryBasePractice
        session={session}
        renderContent={(props) => (
          <>
            <LocalProcessingAlert />
            <PracticeStage
              {...props}
              session={session}
              choices={{
                visible:
                  config.features.hasSentenceOptions && props.showSentenceOptions,
                options: props.sentenceOptions,
                onChoose: props.displayNextSentence,
              }}
            />
          </>
        )}
      />
    );
  }

  return (
    <BasePractice
      session={session}
      renderContent={(props) =>
        props.finished && props.sessionResult ? (
          <PatternFinish session={session} result={props.sessionResult} />
        ) : (
          <>
            <LocalProcessingAlert />
            <PracticeStage
              {...props}
              session={session}
              // Pattern sessions show the pattern and "Line 3 of 7".
              title={session.pattern_name ?? undefined}
              subtitle={
                props.lineInfo
                  ? lineLabel(props.lineInfo.index, props.lineInfo.count)
                  : undefined
              }
              next={{
                visible: config.features.hasNextButton && props.showNextButton,
                onNext: props.displayNextSentence,
              }}
            />
          </>
        )
      }
    />
  );
};

export default GenericPractice;
