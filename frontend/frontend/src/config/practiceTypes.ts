import { type Session } from "@/api";

export interface PracticeTypeConfig {
  title: string;
  basePracticeComponent: string; // "BasePractice" or "ChoiceStoryBasePractice"
  features: {
    hasNextButton: boolean;
    hasSentenceOptions: boolean;
    customLayout?: string;
  };
  styling?: {
    headerStyle?: string;
    containerStyle?: string;
  };
}

export const practiceTypeConfigs: Record<string, PracticeTypeConfig> = {
  unlimited: {
    title: "Unlimited Practice",
    basePracticeComponent: "BasePractice",
    features: {
      hasNextButton: true,
      hasSentenceOptions: false,
    },
    styling: {
      headerStyle: "text-center flex-1",
      containerStyle: "min-h-screen px-4 py-4 flex flex-col items-center gap-6",
    },
  },
  "choice-story": {
    title: "Choice Story Practice",
    basePracticeComponent: "ChoiceStoryBasePractice",
    features: {
      hasNextButton: false,
      hasSentenceOptions: true,
    },
    styling: {
      headerStyle: "",
      containerStyle: "min-h-screen px-4 py-4 flex flex-col items-center gap-6",
    },
  },
};

export const getPracticeConfig = (activityType: string): PracticeTypeConfig => {
  return practiceTypeConfigs[activityType] || practiceTypeConfigs.unlimited;
};
