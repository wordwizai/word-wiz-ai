from datasets import load_dataset
import pandas as pd

# Description: Load the dataset from the Hugging Face Datasets library
class SpeechDatasetLoader:
    def __init__(self, age_range: tuple = None, filter_absurd_entries: bool = False):
        """Initializes a dataset loader object that loads the huggingface dataset for this project
        Args:
            age_range (tuple): min_age, max_age
            filter_absurd_entries (bool): Whether to filter out entries with absurd values
        """

        self.dataset = load_dataset("mispeech/speechocean762")
        self.train = self.dataset["train"]  # changed
        self.test = self.dataset["test"]    # changed

        if age_range is not None:
            self.sort_age(age_range)

        if filter_absurd_entries:
            self.filter_invalid_entries()

    def sort_age(self, age_range: tuple):
        self.train = self.train.filter(
            lambda example: age_range[0] <= example["age"] < age_range[1]
        )

    def filter_invalid_entries(self):
        """Filters out entries with ground_truth_per == 0.0 or ground_truth_accuracy == 10."""
        def calculate_ground_truth_per(example):
            total_phonemes = sum(len(word["phones"]) for word in example["words"])
            total_mispronunciations = sum(len(word["mispronunciations"]) for word in example["words"])
            return total_mispronunciations / total_phonemes if total_phonemes > 0 else 0.0

        self.train = self.train.filter(
            lambda example: calculate_ground_truth_per(example) != 0.0 and example["accuracy"] != 10
        )
    
    def get_dataset(self):
        return self.train, self.test
    
    def get_item(self, item: int):
        return self.train[item]  # changed

if __name__ == "__main__":
    loader = SpeechDatasetLoader((0, 8), filter_absurd_entries=True)
    print(loader.get_item(20)["words"][1])