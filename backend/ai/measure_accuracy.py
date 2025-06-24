#%%
from self_dataset_loader import SelfSpeechDatasetLoader
from phoneme_extractor import PhonemeExtractor
from word_extractor import WordExtractor
from process_audio import process_audio_array, analyze_results
from grapheme_to_phoneme import grapheme_to_phoneme
from evaluation.accuracy_metrics import compute_phoneme_error_rate
import eng_to_ipa as g2p
import pandas as pd
import math
import matplotlib.pyplot as plt  # changed
import time  # added

#%%
loader = SelfSpeechDatasetLoader()
phoneme_model = PhonemeExtractor()
word_model = WordExtractor()
#%%

# ACCURACY IS MEASURED AS THE CORRELATION COEFFICIENT BETWEEN THE DATABASE ACCURACY AND THE MODEL PER

class MeasureAccuracy:
    def __init__(self, dataset, phoneme_model, word_model):
        self.dataset = dataset
        self.phoneme_model = phoneme_model
        self.word_model = word_model

    def compare_indexes(self, index_range: range, merged_list=None) -> tuple[pd.DataFrame, float, float, float, float]:
        if merged_list is None:
            all_results = []
            calc_times = []
            for idx in index_range:
                try:
                    df, calc_time = self.compare_index(idx)
                    all_results.append(df)
                    calc_times.append(calc_time)
                except Exception as e:
                    # import traceback
                    # import sys
                    # # Get exception information
                    # exc_type, exc_value, exc_traceback = sys.exc_info()

                    # # Print the exception type and value
                    # print(f"Error Type: {exc_type.__name__}")
                    # print(f"Error Value: {exc_value}")

                    # # Print the formatted traceback
                    # print("Traceback:")
                    # traceback.print_tb(exc_traceback, file=sys.stdout)

                    print(f"Skipping index {idx} due to error: {e.args}")
                    print(e)

            if not all_results:
                return pd.DataFrame(), 0.0, 0.0, 0.0, 0.0

            merged = pd.concat(all_results, ignore_index=True)
        else:
            merged = merged_list

        model_per_vals = pd.Series(merged["model_per"]).fillna(1).to_list()
        gt_per_vals = pd.Series(merged["ground_truth_per"]).fillna(1).to_list()

        # mean absolute error
        mae = sum(abs(m - g) for m, g in zip(model_per_vals, gt_per_vals)) / len(model_per_vals)

        # mean squared error
        mse = sum((m - g) ** 2 for m, g in zip(model_per_vals, gt_per_vals)) / len(model_per_vals)

        # correlation coefficient
        corr = self.correlation_coefficient(model_per_vals, gt_per_vals)

        average_calc_time = sum(calc_times)/len(calc_times)

        return merged, mae, mse, corr, average_calc_time

    def compare_index(self, index: int) -> tuple[pd.DataFrame, float]:
        """Function that compares our model to the  

        Args:
            index (int): _description_

        Returns:
            tuple[pd.DataFrame, float]: DataFrame and correlation coefficient
        """
        start_time = time.time()  # start timing

        # gets the item from our dataset
        item = self.dataset[index]

        # gets the audio
        audio_array = self.dataset.get_audio_bytes(index)

        # the text we were supposed to say
        text = item["original_sentence"]
        ground_truth = grapheme_to_phoneme(text.lower()) 

        # use our model to process and analyze our results
        results = process_audio_array(ground_truth, audio_array, 16000, phoneme_extraction_model=self.phoneme_model, word_extraction_model=self.word_model)
        df, _, _, per_data = analyze_results(results)

        sentence_per = per_data["sentence_per"]
        ground_truth_per = item["per"]

        # calculate the prediction to the actual error
        altered_text = item["altered_sentence"]
        altered_ground_truth = list(g2p.convert(altered_text).replace(" ",""))
        print("altered gt:", altered_ground_truth)
        predicted_phonemes = []
        for result in results:
            predicted_phonemes += result["phonemes"]
        print("pred phonemes:", predicted_phonemes)
        pred_to_actual_error = compute_phoneme_error_rate(altered_ground_truth, predicted_phonemes)

        # # figure out correlation coef of accuracy and per
        end_time = time.time()  # end timing
        calculation_time = end_time - start_time

        results = pd.DataFrame({
            "model_per": [float(sentence_per)],
            "ground_truth_per": [float(ground_truth_per)],
            "pred_to_actual_error": [float(pred_to_actual_error)]
        })

        return results, calculation_time

    def correlation_coefficient(self, x: list, y: list) -> float:
        """Finds the correlation coefficient between two same sized lists

        Args:
            x (list): the x part of the data
            y (list): the y part of the data

        Returns:
            float: the correlation coefficient between the two
        """
        if len(x) != len(y):
            raise AttributeError("The length of x and y must be the same")

        mean_x = sum(x) / len(x)
        mean_y = sum(y) / len(y)

        numerator = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
        denominator = math.sqrt(
            sum((xi - mean_x) ** 2 for xi in x) * sum((yi - mean_y) ** 2 for yi in y)
        )
        if denominator == 0:
            return 0.0

        return numerator / denominator
#%%
# accuracy = MeasureAccuracy(dataset=loader, phoneme_model=phoneme_model, word_model=word_model)
# results, correlation_coefficient = accuracy.compare_index(1)
# print(results)
# print("correlation coef:", correlation_coefficient)
#%%
import numpy as np
import torch
torch.device("cuda" if torch.cuda.is_available() else "cpu")
accuracy = MeasureAccuracy(dataset=loader, phoneme_model=phoneme_model, word_model=word_model)
results = accuracy.compare_indexes(map(int,list(np.random.randint(1,len(loader),50))))
#%%
print(results)
print("correlation coef:", results[3])
print("mean squared error", results[2])
print("mean absolute error", results[1])

# Import necessary libraries
import numpy as np


# Filter out invalid data for ground_truth_per vs model_per
valid_data = results[0].dropna(subset=["ground_truth_per", "model_per"])
x = valid_data["ground_truth_per"]
y = valid_data["model_per"]

# Plot ground_truth_per vs model_per with extended line of best fit
plt.scatter(x, y, label="Data Points")
coefficients = np.polyfit(x, y, 1)  # Linear fit (degree 1)
line = np.poly1d(coefficients)

# Define the range of x values to cover the entire graph
x_range = np.linspace(0, 1, 100)  # From 0 to 1 with 100 points
plt.plot(x_range, line(x_range), color="red", label="Best Fit Line")  # Extended line
plt.xlabel("Ground Truth PER")
plt.ylabel("Model PER")
plt.xlim(0, 1)  # Ensure the x-axis goes from 0 to 1
plt.legend()
plt.title("Ground Truth PER vs Model PER")
plt.show()

# Filter out invalid data for ground_truth_per vs model_per
valid_data = results[0].dropna(subset=["pred_to_actual_error"])
x = range(0, len(valid_data))
y = valid_data["pred_to_actual_error"]

plt.figure(figsize=(10, 6))  # Larger plot for better visibility
plt.scatter(x, y, label="Data Points")
avg = np.average(y)

# Use the actual range of indices for the line
x_range = np.linspace(0, len(valid_data)-1, 100)
plt.plot(x_range, np.full_like(x_range, avg), color="red", label="Average Line")  # Average line
plt.xlabel("Sample index")
plt.ylabel("Prediction to Actual Error")
plt.legend()
plt.title("Prediction to Actual Error by Sample Index")
plt.ylim(0, 1)  # Ensure the y-axis goes from 0 to 1
plt.show()

print(f"Average Calculation time: {results[4]}")