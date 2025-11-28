"""
Analysis System Test Runner
Implements Phase 4 of the TESTING_SUITE_IMPLEMENTATION_GUIDE.md
"""
import os
import json
import pandas as pd
from datetime import datetime

# Ensure backend root is in sys.path for core.* imports
import sys
BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from core.grapheme_to_phoneme import grapheme_to_phoneme as g2p
from core.process_audio import process_audio_with_client_phonemes, analyze_results
from schemas.feedback_entry import AudioAnalysis

ANALYSIS_DIR = os.path.join(os.path.dirname(__file__), 'analysis')
RESULTS_DIR = os.path.join(os.path.dirname(__file__), 'results')
os.makedirs(RESULTS_DIR, exist_ok=True)

def run_analysis_test(test_path):
    with open(test_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    sentence = data['sentence']
    client_phonemes = data['client_phonemes']
    client_words = data.get('client_words', None)
    audio_path = data.get('audio_path', None)
    audio_array = None
    word_extractor = None
    if audio_path and os.path.exists(audio_path):
        import soundfile as sf
        audio_array, sr = sf.read(audio_path)
        if sr != 16000:
            raise ValueError(f"Audio must be 16kHz, got {sr}")
        if audio_array.ndim > 1:
            audio_array = audio_array[:, 0]
    ground_truth_phonemes = g2p(sentence)
    # If word_extractor is needed, import and instantiate here
    # from core.word_extractor import WordExtractor
    # word_extractor = WordExtractor()
    pronunciation_data = process_audio_with_client_phonemes(
        client_phonemes=client_phonemes,
        ground_truth_phonemes=ground_truth_phonemes,
        audio_array=audio_array,
        word_extraction_model=word_extractor,
        client_words=client_words
    )
    df, highest_per_word, problem_summary, per_summary = analyze_results(pronunciation_data)
    analysis = AudioAnalysis(
        pronunciation_dataframe=df,
        highest_per_word=highest_per_word,
        problem_summary=problem_summary,
        per_summary=per_summary
    )
    # Save analysis to JSON
    result = {
        'sentence': sentence,
        'analysis': {
            'pronunciation_dataframe': df.to_dict() if hasattr(df, 'to_dict') else str(df),
            'highest_per_word': highest_per_word,
            'problem_summary': problem_summary,
            'per_summary': per_summary
        }
    }
    result_path = os.path.join(RESULTS_DIR, f"analysis_result_{os.path.basename(test_path).replace('.json','')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(result_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, default=str)
    print(f"Analysis test complete for {test_path}. Output saved to {result_path}")
    print("Pronunciation DataFrame:")
    print(pd.DataFrame(df))
    return result_path

def main():
    # Discover all analysis test cases
    test_cases = [
        os.path.join(ANALYSIS_DIR, f) for f in os.listdir(ANALYSIS_DIR)
        if f.endswith('.json')
    ]
    if not test_cases:
        print("No analysis test cases found.")
        return
    for test_path in test_cases:
        run_analysis_test(test_path)

if __name__ == '__main__':
    main()
