#%%
import torch
print(torch.device('cuda' if torch.cuda.is_available() else 'cpu'))
import time
from phoneme_assistant import PhonemeAssistant
from self_dataset_loader import SelfSpeechDatasetLoader
import json
import IPython.display as ipd
import numpy as np
import pandas as pd
import csv
import os
# use the SpeechOcean dataset from dataset_loader.py and run the audio through phoneme_assistant.py 
# then get user input on various things through the terminal

rubric = """
1. Speed
Definition: Measures the system's responsiveness in delivering feedback to the user.
Score	Description
5	Feedback is delivered instantly (≤1 second), ensuring a seamless experience.
4	Minor delay (1–2 seconds); negligible impact on user experience.
3	Noticeable delay (2–3 seconds); may slightly affect user engagement.
2	Significant delay (3–5 seconds); disrupts the learning flow.
1	Excessive delay (>5 seconds); hinders usability and user retention.


2. Accuracy
Definition: Assesses the correctness of the system's feedback in identifying and addressing user errors.
Score	Description
5	Feedback is entirely accurate; all errors are correctly identified and addressed.
4	Minor inaccuracies; most errors are correctly identified with negligible misclassifications.
3	Some inaccuracies; noticeable misclassifications that may confuse the user.
2	Frequent inaccuracies; significant misclassifications leading to potential misunderstandings.
1	Predominantly inaccurate; feedback is misleading and may reinforce incorrect usage.

3. Feedback Quality
Definition: Evaluates the clarity, helpfulness, and motivational aspects of the feedback provided.
Score	Description
5	Feedback is clear, constructive, and encourages continued learning; provides actionable suggestions.
4	Feedback is generally clear and helpful; minor improvements could enhance user motivation.
3	Feedback is somewhat helpful but lacks clarity or motivational elements; may not fully engage the user.
2	Feedback is unclear or lacks constructive elements; may discourage user engagement.
1	Feedback is confusing, unhelpful, or demotivating; likely to deter users from continued use.
"""
# Initialize components
assistant = PhonemeAssistant()
loader = SelfSpeechDatasetLoader()

def status_callback(message):
    print(f"Status: {message}")

def evaluate_model(attempts: int):
    if os.path.exists("evaluation_results.csv"):
        df = pd.read_csv("evaluation_results.csv")
        results = df.to_dict(orient="records")
    else:
        results = []

    random_indexes = np.random.permutation(np.arange(len(loader)))[:attempts]

    # Open CSV file for writing
    with open("evaluation_results.csv", "w", newline="") as csvfile:
        fieldnames = ["speed_score", "accuracy_score", "feedback_quality_score", "elapsed_time"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(result)
        csvfile.flush()

        for i in random_indexes.tolist():
            try:
                # Load a sample from the dataset
                sample = loader[i]

                attempted_sentence = sample["original_sentence"].lower()
                audio = loader.get_audio_bytes(i)

                print("Attempted Sentence:", attempted_sentence)

                # Display audio using widgets
                print("\nPlaying audio sample:")
                audio_widget = ipd.Audio(data=audio, rate=16000)
                ipd.display(audio_widget)

                # Measure speed
                start_time = time.time()
                response, _, _, _, _ = assistant.record_audio_and_get_response(
                    attempted_sentence, verbose=True, status_callback=status_callback, audio_array=audio
                )
                end_time = time.time()
                elapsed_time = end_time - start_time

                print("\nFeedback:", response["feedback"])
                print("\nNew Sentence to Say:", response["sentence"])

                # Speed evaluation
                print("\nSpeed Evaluation:")
                if elapsed_time <= 1:
                    speed_score = 5
                elif elapsed_time <= 2:
                    speed_score = 4
                elif elapsed_time <= 3:
                    speed_score = 3
                elif elapsed_time <= 5:
                    speed_score = 2
                else:
                    speed_score = 1
                print(f"Elapsed Time: {elapsed_time:.2f} seconds, Score: {speed_score}")

                # Accuracy evaluation
                print("\nAccuracy Evaluation:")
                print(rubric.split("\n\n")[1])  # Print accuracy rubric
                accuracy_score = int(input("Enter a score for accuracy (1-5): "))

                # Feedback quality evaluation
                print("\nFeedback Quality Evaluation:")
                print(rubric.split("\n\n")[2])  # Print feedback quality rubric
                feedback_quality_score = int(input("Enter a score for feedback quality (1-5): "))

                # Store results
                result = {
                    "speed_score": speed_score,
                    "accuracy_score": accuracy_score,
                    "feedback_quality_score": feedback_quality_score,
                    "elapsed_time": elapsed_time
                }
                results.append(result)

                # Write result to CSV
                writer.writerow(result)
                csvfile.flush()

            except Exception as e:
                print(f"Error processing index {i}: {e}")
                pass
    
    # Save results to a file
    with open("evaluation_results.txt", "w") as file:
        json.dump(results, file, indent=4)

    # Calculate averages
    avg_speed = sum(result["speed_score"] for result in results) / attempts
    avg_accuracy = sum(result["accuracy_score"] for result in results) / attempts
    avg_feedback_quality = sum(result["feedback_quality_score"] for result in results) / attempts

    # Print and save summary
    print("\nSummary of Evaluation:")
    print(f"Average Speed Score: {avg_speed:.2f}")
    print(f"Average Accuracy Score: {avg_accuracy:.2f}")
    print(f"Average Feedback Quality Score: {avg_feedback_quality:.2f}")

    with open("evaluation_summary.txt", "w") as file:
        file.write("Summary of Evaluation:\n")
        file.write(f"Average Speed Score: {avg_speed:.2f}\n")
        file.write(f"Average Accuracy Score: {avg_accuracy:.2f}\n")
        file.write(f"Average Feedback Quality Score: {avg_feedback_quality:.2f}\n")


if __name__ == "__main__":
    print("Welcome to the Quantitative Analysis Tool!")
    print(rubric)
    evaluate_model(attempts=20)
