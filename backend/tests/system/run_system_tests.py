import sys
import os
import json
import asyncio
import soundfile as sf
import numpy as np
from datetime import datetime

# Ensure backend root is in sys.path for core.* imports
BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)
# Ensure schemas is in sys.path for schemas.feedback_entry import
SCHEMAS_PATH = os.path.abspath(os.path.join(BACKEND_ROOT, 'schemas'))
if SCHEMAS_PATH not in sys.path:
    sys.path.insert(0, SCHEMAS_PATH)

from core.phoneme_assistant import PhonemeAssistant
from core.modes.story import StoryPractice
from core.modes.choice_story import ChoiceStoryPractice
from core.modes.unlimited import UnlimitedPractice
from schemas.feedback_entry import AudioAnalysis

# Helper to load audio as numpy array
def load_audio(audio_path):
    audio, sr = sf.read(audio_path)
    if sr != 16000:
        raise ValueError(f"Audio must be 16kHz, got {sr}")
    if audio.ndim > 1:
        audio = audio[:, 0]  # Take first channel if stereo
    return audio

# Helper to run a single system-level test case

def run_system_test(test_dir, mode_cls, assistant):
    sentence_path = os.path.join(test_dir, 'sentence.txt')
    audio_path = os.path.join(test_dir, 'audio.wav')
    if not os.path.exists(sentence_path) or not os.path.exists(audio_path):
        print(f"Skipping {test_dir}: missing sentence.txt or audio.wav")
        return None
    with open(sentence_path, 'r', encoding='utf-8') as f:
        sentence = f.read().strip()
    audio = load_audio(audio_path)
    class DummySession:
        def __init__(self):
            self.feedback_entries = []

    async def run():
        df, highest_per_word, problem_summary, per_summary = await assistant.process_audio(sentence, audio)
        analysis = AudioAnalysis(
            pronunciation_dataframe=df,
            highest_per_word=highest_per_word,
            problem_summary=problem_summary,
            per_summary=per_summary
        )
        mode = mode_cls()
        session = DummySession()
        result = await mode.get_feedback_and_next_sentence(sentence, analysis, assistant, session=session)
        output = {
            'words_phonemes': df.to_dict() if hasattr(df, 'to_dict') else str(df),
            'analysis': {
                'highest_per_word': highest_per_word,
                'problem_summary': problem_summary,
                'per_summary': per_summary
            },
            'gpt_feedback': result
        }
        out_path = os.path.join(test_dir, 'result.json')
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, default=str)
        print(f"Test {test_dir} complete. Output saved to {out_path}")
    asyncio.run(run())

if __name__ == '__main__':
    # Discover all test cases in /tests/system/
    base_dir = os.path.dirname(__file__)
    system_dir = os.path.abspath(os.path.join(base_dir))
    test_cases = [
        os.path.join(system_dir, d) for d in os.listdir(system_dir)
        if os.path.isdir(os.path.join(system_dir, d)) and d.startswith('test_case_')
    ]
    # Create a single PhonemeAssistant instance and reuse it
    assistant = PhonemeAssistant()
    # For now, use StoryPractice for all
    for test_dir in test_cases:
        run_system_test(test_dir, StoryPractice, assistant)
