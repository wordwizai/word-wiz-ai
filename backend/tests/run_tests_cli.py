# To use interactive CLI, install questionary:
# pip install questionary

import os
import json
from datetime import datetime
import questionary
import pandas as pd
from concurrent.futures import ProcessPoolExecutor, as_completed
from run_tests import discover_test_cases, run_test_in_subprocess, print_summary, TEST_MODES

def interactive_cli():
    while True:
        mode = questionary.select(
            "Which test mode do you want to run?",
            choices=TEST_MODES + ["exit"]
        ).ask()
        if mode == "exit":
            print("Exiting test runner.")
            break
        cases = discover_test_cases(mode)
        if not cases:
            print(f"No test cases found for mode: {mode}")
            continue
        case_choices = [os.path.basename(c) for c in cases]
        selected_cases = questionary.checkbox(
            f"Select test cases to run for mode '{mode}':",
            choices=case_choices
        ).ask()
        if not selected_cases:
            print("No test cases selected.")
            continue
        selected_case_paths = [c for c in cases if os.path.basename(c) in selected_cases]
        print(f"Running {len(selected_case_paths)} test(s) in mode '{mode}'...")
        all_results = []
        with ProcessPoolExecutor() as executor:
            futures = [executor.submit(run_test_in_subprocess, mode, c) for c in selected_case_paths]
            results = [f.result() for f in as_completed(futures)]
        for r in results:
            r['mode'] = mode
        print_summary(results)
        all_results.extend(results)
        # Save results
        results_dir = os.path.join(os.path.dirname(__file__), "results")
        os.makedirs(results_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_path = os.path.join(results_dir, f"results_{timestamp}.json")
        with open(results_path, "w") as f:
            json.dump(all_results, f, indent=2)
        print(f"\nResults saved to {results_path}")
        again = questionary.confirm("Do you want to run more tests?").ask()
        if not again:
            print("Exiting test runner.")
            break

if __name__ == "__main__":
    interactive_cli()
