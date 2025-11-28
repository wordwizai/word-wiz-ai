import argparse
import asyncio
import os
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# Placeholder imports for actual test logic
# from backend.core.phoneme_assistant import PhonemeAssistant
# from backend.core.modes.story import StoryPractice
# from backend.core.modes.choice_story import ChoiceStoryPractice
# from backend.core.modes.unlimited import UnlimitedPractice
# from backend.schemas.feedback_entry import AudioAnalysis

TEST_MODES = ["system", "analysis", "extraction", "gpt"]


def discover_test_cases(mode):
    """Return a list of test case paths for the given mode."""
    test_dir = os.path.join(os.path.dirname(__file__), mode)
    if not os.path.exists(test_dir):
        return []
    if mode in ("system", "extraction"):
        # Each test is a subfolder, skip __pycache__ and hidden/system folders
        return [
            os.path.join(test_dir, d)
            for d in os.listdir(test_dir)
            if os.path.isdir(os.path.join(test_dir, d))
            and not d.startswith(".")
            and not d.startswith("__")
        ]
    else:
        # Each test is a JSON file
        return [os.path.join(test_dir, f) for f in os.listdir(test_dir)
                if f.endswith(".json")]


def print_summary(results):

    print("\n=== Test Results Summary ===")
    print(f"{'Test':<30} {'Status':<10} {'Details':<40}")
    print("-" * 80)
    import pandas as pd
    for r in results:
        print(f"{r['name']:<30} {r['status']:<10} {r['details']:<40}")
        # Only print detailed output for system tests
        if r.get('mode', None) == 'system' and r['details'] == 'Output generated':
            result_json_path = os.path.join(os.path.dirname(__file__), 'system', r['name'], 'result.json')
            if os.path.exists(result_json_path):
                try:
                    with open(result_json_path, 'r', encoding='utf-8') as f:
                        result_data = json.load(f)
                    words_phonemes = result_data.get('words_phonemes', {})
                    # Convert to DataFrame and print
                    df = pd.DataFrame(words_phonemes)
                    print("  Pronunciation DataFrame:")
                    print(df)
                    gpt = result_data.get('gpt_feedback', {})
                    print("  GPT Feedback:")
                    print(f"    Feedback: {gpt.get('feedback', '')}")
                    print(f"    Next Sentence: {gpt.get('sentence', '')}")
                except Exception as e:
                    print(f"  [Error reading result.json: {e}]")



def run_test_in_subprocess(mode, case_path):
    import importlib.util
    import traceback
    import sys
    import os
    backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if backend_root not in sys.path:
        sys.path.insert(0, backend_root)
    try:
        if mode == "system":
            sys_path = os.path.join(os.path.dirname(__file__), "system", "run_system_tests.py")
            spec = importlib.util.spec_from_file_location("run_system_tests", sys_path)
            run_system_tests = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(run_system_tests)
            # Only create one PhonemeAssistant per process
            if not hasattr(run_test_in_subprocess, "_assistant"):
                run_test_in_subprocess._assistant = run_system_tests.PhonemeAssistant()
            assistant = run_test_in_subprocess._assistant
            run_system_tests.run_system_test(case_path, run_system_tests.StoryPractice, assistant)
            result_path = os.path.join(case_path, "result.json")
            if os.path.exists(result_path):
                return {"name": os.path.basename(case_path), "status": "PASS", "details": "Output generated"}
            else:
                return {"name": os.path.basename(case_path), "status": "FAIL", "details": "No result.json output"}
        elif mode == "extraction":
            audio_path = os.path.join(case_path, "audio.wav")
            sentence_path = os.path.join(case_path, "sentence.txt")
            if not (os.path.exists(audio_path) and os.path.exists(sentence_path)):
                return {"name": os.path.basename(case_path), "status": "FAIL", "details": "Missing files"}
            return {"name": os.path.basename(case_path), "status": "PASS", "details": "OK"}
        else:
            if not os.path.exists(case_path):
                return {"name": os.path.basename(case_path), "status": "FAIL", "details": "Missing JSON"}
            with open(case_path) as f:
                json.load(f)  # Just check parse
            return {"name": os.path.basename(case_path), "status": "PASS", "details": "OK"}
    except Exception as e:
        tb = traceback.format_exc()
        return {"name": os.path.basename(case_path), "status": "FAIL", "details": f"Exception: {e}\n{tb}"}


def main():
    parser = argparse.ArgumentParser(description="Run phoneme assistant test suite.")
    parser.add_argument("mode", choices=TEST_MODES + ["all"], help="Test mode to run")
    args = parser.parse_args()

    modes = TEST_MODES if args.mode == "all" else [args.mode]
    all_results = []

    for mode in modes:
        print(f"\n--- Running {mode} tests ---")
        cases = discover_test_cases(mode)
        if not cases:
            print(f"No test cases found for mode: {mode}")
            continue
        # Use ProcessPoolExecutor for all modes for consistency and isolation
        from concurrent.futures import ProcessPoolExecutor, as_completed
        with ProcessPoolExecutor() as executor:
            futures = [executor.submit(run_test_in_subprocess, mode, c) for c in cases]
            results = [f.result() for f in as_completed(futures)]
        # Attach mode to each result for summary filtering
        for r in results:
            r['mode'] = mode
            print(f"{r['name']}: {r['status']} - {r['details']}")
        all_results.extend(results)

    # Save results
    results_dir = os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(results_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_path = os.path.join(results_dir, f"results_{timestamp}.json")
    with open(results_path, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nResults saved to {results_path}")
    print_summary(all_results)

if __name__ == "__main__":
    main()
