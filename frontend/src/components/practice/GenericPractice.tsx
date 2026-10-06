import { type Session } from "@/api";
import BasePractice from "@/components/practice/BasePractice";
import ChoiceStoryBasePractice from "@/components/practice/ChoiceStoryBasePractice";
import PracticeStage from "@/components/practice/PracticeStage";
import { LocalProcessingAlert } from "@/components/LocalProcessingAlert";
import { getPracticeConfig } from "@/config/practiceTypes";

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
      renderContent={(props) => (
        <>
          <LocalProcessingAlert />
          <PracticeStage
            {...props}
            session={session}
            next={{
              visible: config.features.hasNextButton && props.showNextButton,
              onNext: props.displayNextSentence,
            }}
          />
        </>
      )}
    />
  );
};

export default GenericPractice;
