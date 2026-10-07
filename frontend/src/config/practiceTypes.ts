
export interface PracticeTypeConfig {
  title: string;
  basePracticeComponent: string; // "BasePractice" or "ChoiceStoryBasePractice"
  features: {
    hasNextButton: boolean;
    hasSentenceOptions: boolean;
    customLayout?: string;
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
  },
  story: {
    title: "Story Practice",
    basePracticeComponent: "BasePractice",
    features: {
      hasNextButton: true,
      hasSentenceOptions: false,
    },
  },
  "choice-story": {
    title: "Choice Story Practice",
    basePracticeComponent: "ChoiceStoryBasePractice",
    features: {
      hasNextButton: false,
      hasSentenceOptions: true,
    },
  },
  "phonics-pattern": {
    title: "Phonics path",
    basePracticeComponent: "BasePractice",
    features: {
      hasNextButton: true,
      hasSentenceOptions: false,
    },
  },
};

export const getPracticeConfig = (activityType: string): PracticeTypeConfig => {
  return practiceTypeConfigs[activityType] || practiceTypeConfigs.unlimited;
};
