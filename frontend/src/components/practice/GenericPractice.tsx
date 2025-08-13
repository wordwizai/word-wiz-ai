import { Button } from "@/components/ui/button";
import { Home } from "lucide-react";
import { Link } from "react-router-dom";
import { RecordAndNextButtons } from "@/components/RecordAndNextButtons";
import { FeedbackAnimatedText } from "@/components/FeedbackAnimatedText";
import { type Session } from "@/api";
import WordBadgeRow from "@/components/WordBadgeRow";
import BasePractice from "@/components/practice/BasePractice";
import ChoiceStoryBasePractice from "@/components/practice/ChoiceStoryBasePractice";
import SentenceDisplay from "@/components/practice/SentenceDisplay";
import FeedbackDisplay from "@/components/practice/FeedbackDisplay";
import {
  getPracticeConfig,
  type PracticeTypeConfig,
} from "@/config/practiceTypes";

interface GenericPracticeProps {
  session: Session;
  activityType: string;
  customContent?: React.ReactNode;
}

const GenericPractice = ({
  session,
  activityType,
  customContent,
}: GenericPracticeProps) => {
  const config = getPracticeConfig(activityType);

  const renderDefaultContent = (props: any) => (
    <div className={config.styling?.containerStyle}>
      <div className="w-full flex flex-row justify-between items-center">
        <Link to="/dashboard">
          <Button variant="ghost" className="text-muted-foreground group">
            <Home className="size-5" />
            <span className="opacity-0 translate-x-[-16px] transition-all duration-200 group-hover:opacity-100 group-hover:translate-x-0 hidden md:inline-block">
              Home
            </span>
          </Button>
        </Link>
        <h1
          className={`scroll-m-20 text-3xl font-semibold tracking-tight first:mt-0 ${config.styling?.headerStyle}`}
        >
          {config.title}
        </h1>
        <div className="w-16 hidden md:inline-block" />
      </div>
      <div className="w-full flex flex-col items-center justify-center gap-6 flex-1">
        <SentenceDisplay
          wordArray={props.wordArray}
          showHighlightedWords={props.showHighlightedWords}
          analysisData={props.analysisData}
        />
        <RecordAndNextButtons
          isRecording={props.isRecording}
          onStartRecording={props.onStartRecording}
          onStopRecording={props.onStopRecording}
          showNextButton={
            config.features.hasNextButton ? props.showNextButton : false
          }
          onNext={props.displayNextSentence}
        />
      </div>
      <FeedbackDisplay feedback={props.feedback} />
      {customContent}
    </div>
  );

  const renderChoiceStoryContent = (props: any) => (
    <div className={config.styling?.containerStyle}>
      <div className="w-full flex justify-between items-center">
        <Link to="/dashboard">
          <Button variant="ghost" className="text-muted-foreground group">
            <Home className="size-5" />
            <span className="opacity-0 translate-x-[-16px] transition-all duration-200 group-hover:opacity-100 group-hover:translate-x-0">
              Home
            </span>
          </Button>
        </Link>
        <h1 className="scroll-m-20 text-3xl font-semibold tracking-tight first:mt-0">
          {config.title}
        </h1>
        <div className="w-16" />
      </div>
      <div className="w-full flex flex-col items-center justify-center gap-6 flex-1">
        <WordBadgeRow
          showHighlightedWords={props.showHighlightedWords}
          wordArray={props.wordArray}
          analysisData={props.analysisData}
        />
        <div className="w-full flex justify-center items-center gap-4">
          {config.features.hasSentenceOptions && props.showSentenceOptions && (
            <Button
              className="h-24 shadow-inner rounded-full hover:bg-fuchsia-200"
              variant="secondary"
              onClick={() =>
                props.displayNextSentence(
                  props.sentenceOptions?.option_1?.sentence ?? "",
                )
              }
            >
              <span className="text-4xl">
                {props.sentenceOptions?.option_1?.icon}
              </span>
              <span className="text-lg">
                {props.sentenceOptions?.option_1?.action}
              </span>
            </Button>
          )}
          <RecordAndNextButtons
            isRecording={props.isRecording}
            onStartRecording={props.onStartRecording}
            onStopRecording={props.onStopRecording}
          />
          {config.features.hasSentenceOptions && props.showSentenceOptions && (
            <Button
              className="h-24 shadow-inner rounded-full hover:bg-fuchsia-200"
              variant="secondary"
              onClick={() =>
                props.displayNextSentence(
                  props.sentenceOptions?.option_2?.sentence ?? "",
                )
              }
            >
              <span className="text-4xl">
                {props.sentenceOptions?.option_2?.icon}
              </span>
              <span className="text-lg">
                {props.sentenceOptions?.option_2?.action}
              </span>
            </Button>
          )}
        </div>
      </div>
      <FeedbackAnimatedText feedback={props.feedback} />
      {customContent}
    </div>
  );

  if (config.basePracticeComponent === "ChoiceStoryBasePractice") {
    return (
      <ChoiceStoryBasePractice
        session={session}
        renderContent={renderChoiceStoryContent}
      />
    );
  }
  if (config.basePracticeComponent === "") {
    return (
      <ChoiceStoryBasePractice
        session={session}
        renderContent={renderChoiceStoryContent}
      />
    );
  }

  return (
    <BasePractice session={session} renderContent={renderDefaultContent} />
  );
};

export default GenericPractice;
