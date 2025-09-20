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
    <div className={`min-h-screen bg-gradient-to-br from-background to-purple-50/50 ${config.styling?.containerStyle}`}>
      {/* Enhanced Header */}
      <div className="w-full flex flex-row justify-between items-center p-6 relative">
        {/* Decorative background */}
        <div className="absolute inset-0 bg-gradient-to-r from-purple-100/20 to-pink-100/20 rounded-3xl blur-xl"></div>
        <div className="relative z-10 w-full flex justify-between items-center">
          <Link to="/dashboard">
            <Button variant="ghost" className="text-muted-foreground group hover:bg-white/50 rounded-xl transition-all duration-200">
              <Home className="size-5" />
              <span className="opacity-0 translate-x-[-16px] transition-all duration-200 group-hover:opacity-100 group-hover:translate-x-0 hidden md:inline-block ml-2">
                Home
              </span>
            </Button>
          </Link>
          <h1 className={`text-3xl md:text-4xl font-bold bg-gradient-to-r from-primary via-purple-600 to-pink-600 bg-clip-text text-transparent ${config.styling?.headerStyle}`}>
            {config.title}
          </h1>
          <div className="w-16 hidden md:inline-block" />
        </div>
      </div>

      {/* Main Content Area */}
      <div className="w-full flex flex-col items-center justify-center gap-8 flex-1 px-6 relative">
        {/* Decorative background for content */}
        <div className="absolute inset-0 bg-gradient-to-r from-blue-100/10 to-cyan-100/10 rounded-3xl blur-xl"></div>
        <div className="relative z-10 w-full max-w-4xl mx-auto">
          <SentenceDisplay
            wordArray={props.wordArray}
            showHighlightedWords={props.showHighlightedWords}
            analysisData={props.analysisData}
          />
          <div className="mt-8 flex justify-center">
            <RecordAndNextButtons
              isRecording={props.isRecording}
              isProcessing={props.isProcessing}
              onStartRecording={props.onStartRecording}
              onStopRecording={props.onStopRecording}
              showNextButton={
                config.features.hasNextButton ? props.showNextButton : false
              }
              onNext={props.displayNextSentence}
            />
          </div>
        </div>
      </div>

      {/* Feedback Section */}
      <div className="px-6 pb-6">
        <FeedbackDisplay feedback={props.feedback} />
      </div>
      {customContent}
    </div>
  );

  const renderChoiceStoryContent = (props: any) => (
    <div className={`min-h-screen bg-gradient-to-br from-background to-purple-50/50 ${config.styling?.containerStyle}`}>
      {/* Enhanced Header */}
      <div className="w-full flex justify-between items-center p-6 relative">
        {/* Decorative background */}
        <div className="absolute inset-0 bg-gradient-to-r from-purple-100/20 to-pink-100/20 rounded-3xl blur-xl"></div>
        <div className="relative z-10 w-full flex justify-between items-center">
          <Link to="/dashboard">
            <Button variant="ghost" className="text-muted-foreground group hover:bg-white/50 rounded-xl transition-all duration-200">
              <Home className="size-5" />
              <span className="opacity-0 translate-x-[-16px] transition-all duration-200 group-hover:opacity-100 group-hover:translate-x-0 ml-2">
                Home
              </span>
            </Button>
          </Link>
          <h1 className="text-3xl md:text-4xl font-bold bg-gradient-to-r from-primary via-purple-600 to-pink-600 bg-clip-text text-transparent">
            {config.title}
          </h1>
          <div className="w-16" />
        </div>
      </div>

      {/* Main Content Area */}
      <div className="w-full flex flex-col items-center justify-center gap-8 flex-1 px-6 relative">
        {/* Decorative background for content */}
        <div className="absolute inset-0 bg-gradient-to-r from-blue-100/10 to-cyan-100/10 rounded-3xl blur-xl"></div>
        <div className="relative z-10 w-full max-w-4xl mx-auto">
          <WordBadgeRow
            showHighlightedWords={props.showHighlightedWords}
            wordArray={props.wordArray}
            analysisData={props.analysisData}
          />
          <div className="w-full flex justify-center items-center gap-6 mt-8">
            {config.features.hasSentenceOptions && props.showSentenceOptions && (
              <Button
                className="h-24 w-24 shadow-lg hover:shadow-xl rounded-2xl bg-gradient-to-br from-purple-200 to-fuchsia-200 hover:from-purple-300 hover:to-fuchsia-300 transition-all duration-300 hover:scale-105 flex-col"
                variant="secondary"
                onClick={() =>
                  props.displayNextSentence(
                    props.sentenceOptions?.option_1?.sentence ?? "",
                  )
                }
              >
                <span className="text-3xl mb-1">
                  {props.sentenceOptions?.option_1?.icon}
                </span>
                <span className="text-sm font-medium">
                  {props.sentenceOptions?.option_1?.action}
                </span>
              </Button>
            )}
            <RecordAndNextButtons
              isRecording={props.isRecording}
              isProcessing={props.isProcessing}
              onStartRecording={props.onStartRecording}
              onStopRecording={props.onStopRecording}
            />
            {config.features.hasSentenceOptions && props.showSentenceOptions && (
              <Button
                className="h-24 w-24 shadow-lg hover:shadow-xl rounded-2xl bg-gradient-to-br from-purple-200 to-fuchsia-200 hover:from-purple-300 hover:to-fuchsia-300 transition-all duration-300 hover:scale-105 flex-col"
                variant="secondary"
                onClick={() =>
                  props.displayNextSentence(
                    props.sentenceOptions?.option_2?.sentence ?? "",
                  )
                }
              >
                <span className="text-3xl mb-1">
                  {props.sentenceOptions?.option_2?.icon}
                </span>
                <span className="text-sm font-medium">
                  {props.sentenceOptions?.option_2?.action}
                </span>
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Feedback Section */}
      <div className="px-6 pb-6">
        <FeedbackAnimatedText feedback={props.feedback} />
      </div>
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
