# Testing Suite Implementation Guide

This guide outlines a pragmatic, phased approach to implementing a comprehensive testing suite for the phoneme assistant app. Each phase is broken into actionable todos and quality assurance (QA) checks. The suite is designed for maximum coverage with minimal overengineering, following the 80/20 rule.

---

## Overview

The testing suite will provide:

- **System-level tests**: Run end-to-end test cases (audio + sentence) through the full stack, record/visualize outputs.
- **Analysis system tests**: Start from extracted word/phoneme data, run through analysis and GPT, record/visualize outputs.
- **Extraction-only tests**: Run audio through extraction, output word/phoneme data only.
- **GPT-only tests**: Start from fully analyzed pronunciation data, test GPT prompt/response quality.
- **Unified CLI**: A single Python script to select and run any test mode, with clear output and easy extensibility.

---

## Phase 1: Test Case Data & Structure

### Todos

- [ ] **Define test case folder structure**:
  - `/tests/system/` for end-to-end cases: each test = `{audio.wav, sentence.txt}`
  - `/tests/analysis/` for analysis tests: `{input.json}` (word/phoneme data + sentence)
  - `/tests/extraction/` for extraction tests: `{audio.wav, sentence.txt}`
  - `/tests/gpt/` for GPT prompt tests: `{input.json}` (fully analyzed data)
- [ ] **Document data formats**:
  - Audio: 16kHz mono WAV
  - Sentence: plain text file
  - Analysis input: JSON with `words`, `phonemes`, `sentence` (see `client-side-word-extraction.md`)
  - GPT input: JSON matching the schema in `core/gpt_prompts/*_prompt_v*.txt` and `core/modes/`
- [ ] **Create a few sample test cases for each mode**

### QA Checklist

- [ ] All test folders exist and are discoverable by the test runner
- [ ] Each test case is self-contained and valid (audio loads, JSON parses, etc.)
- [ ] Data formats match backend/analysis expectations

---

## Phase 2: Test Runner CLI

### Todos

- [ ] Implement `run_tests.py` in the project root or `/tests/`
- [ ] CLI auto-discovers available test modes and test cases
- [ ] User can select which suite/mode to run (system, analysis, extraction, gpt)
- [ ] For each test, run in parallel (use `concurrent.futures` or `asyncio`)
- [ ] Record outputs to `/tests/results/{mode}/result_{timestamp}.json`
- [ ] Print a clean summary table to the console (test name, pass/fail, key metrics)
- [ ] Optionally, generate a simple HTML or Markdown report for visualization

### QA Checklist

- [ ] CLI runs with `python run_tests.py` and lists all test modes
- [ ] All test cases in each mode are executed and results are saved
- [ ] Parallel execution does not cause race conditions or data loss
- [ ] Console output is readable and highlights failures

---

## Phase 3: System-Level (End-to-End) Tests

### Todos

- [ ] For each `/tests/system/` case:

  - Load audio and sentence

  - **Call**: `PhonemeAssistant.process_audio(attempted_sentence, audio_array)` to get extraction and analysis results.
  - **Call**: The appropriate mode's `get_feedback_and_next_sentence(...)` (e.g., `StoryPractice`, `ChoiceStoryPractice`, `UnlimitedPractice`) with the analysis result and a `PhonemeAssistant` instance.
  - **Save**: All outputs (words/phonemes, analysis, GPT feedback) to JSON.

**Key methods:**

- `PhonemeAssistant.process_audio`
- `StoryPractice.get_feedback_and_next_sentence`
- `ChoiceStoryPractice.get_feedback_and_next_sentence`
- `UnlimitedPractice.get_feedback_and_next_sentence`

**Example code flow:**

```python
assistant = PhonemeAssistant()
df, highest_per_word, problem_summary, per_summary = await assistant.process_audio(sentence, audio_array)
analysis = AudioAnalysis(
    pronunciation_dataframe=df,
    highest_per_word=highest_per_word,
    problem_summary=problem_summary,
    per_summary=per_summary
)
result = await mode.get_feedback_and_next_sentence(sentence, analysis, assistant, session)
```

### QA Checklist

- [ ] All system tests run without manual intervention
- [ ] Outputs match expected structure (see real API responses)
- [ ] Visualization script runs and displays key metrics

---

## Phase 4: Analysis System Tests

### Todos

- [ ] For each `/tests/analysis/` case:

  - Load input JSON (words, phonemes, sentence)

  - **Start**: With extracted phonemes, words, and sentence (from test JSON).
  - **Acquire analysis data**:
    - If you have audio, use `PhonemeAssistant.process_audio(attempted_sentence, audio_array)`.
    - If you have extracted phonemes/words (client_phonemes, client_words):
      1. Use `g2p(attempted_sentence)` to get ground truth phonemes.
      2. Call `process_audio_with_client_phonemes(client_phonemes, ground_truth_phonemes, audio_array, word_extraction_model, client_words)` (audio_array can be empty if not needed).
      3. Call `analyze_results(pronunciation_data)` on the result.
    - This will give you:
      - `pronunciation_dataframe`
      - `highest_per_word`
      - `problem_summary`
      - `per_summary`
  - **Construct**: An `AudioAnalysis` object from these outputs (see `schemas/feedback_entry.py`).
  - **End**: With a valid `AudioAnalysis` object (do not call GPT or mode methods in this phase).
  - **Save**: The constructed `AudioAnalysis` object to JSON for use in later phases.

**Key methods:**

- `PhonemeAssistant.process_audio` (if starting from audio)
- `g2p` (from `core.grapheme_to_phoneme`) to get ground truth phonemes
- `process_audio_with_client_phonemes` (from `core.process_audio`)
- `analyze_results` (from `core.process_audio`)
- Constructing `AudioAnalysis` from analysis outputs

**Example code flow:**

```python
# If you have audio:
df, highest_per_word, problem_summary, per_summary = await assistant.process_audio(sentence, audio_array)

# If you have extracted phonemes/words:
from core.grapheme_to_phoneme import grapheme_to_phoneme as g2p
from core.process_audio import process_audio_with_client_phonemes, analyze_results
ground_truth_phonemes = g2p(sentence)
pronunciation_data = await process_audio_with_client_phonemes(
    client_phonemes=client_phonemes,
    ground_truth_phonemes=ground_truth_phonemes,
    audio_array=audio_array,  # can be empty if not needed
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
```

### QA Checklist

- [ ] Analysis tests run without errors
- [ ] Outputs match expected structure
- [ ] Edge cases (e.g., mismatched word/phoneme counts) are handled gracefully

---

## Phase 5: Extraction-Only Tests

### Todos

- [ ] For each `/tests/extraction/` case:

  - Load audio and sentence

  - **Call**: `PhonemeAssistant.process_audio(attempted_sentence, audio_array)`
  - **Save**: Only the extraction results (words/phonemes) to JSON.

**Key methods:**

- `PhonemeAssistant.process_audio`

**Example code flow:**

```python
assistant = PhonemeAssistant()
df, *_ = await assistant.process_audio(sentence, audio_array)
# Save df (words/phonemes) to JSON
```

### QA Checklist

- [ ] Extraction tests run and output valid data
- [ ] Word/phoneme alignment is checked
- [ ] Failures are clearly reported

---

## Phase 6: GPT Prompt/Response Tests

### Todos

- [ ] For each `/tests/gpt/` case:

  - Load input JSON (fully analyzed data)

  - **Start**: With an `AudioAnalysis` object (from Phase 4 or constructed directly).
  - **Call**: Each mode's `get_feedback_and_next_sentence(...)` method (e.g., `StoryPractice`, `ChoiceStoryPractice`, `UnlimitedPractice`), passing the analysis object and other required arguments.
  - **Save**: GPT outputs (feedback, next sentence, etc.) and validation results to JSON.

**Key methods:**

- `get_feedback_and_next_sentence` (on each mode class)

**Example code flow:**

```python
result = await mode.get_feedback_and_next_sentence(sentence, analysis, assistant, session)
# Save result to JSON
```

### QA Checklist

- [ ] GPT tests run and output valid JSON
- [ ] Feedback and sentence fields are present and non-empty
- [ ] Validation catches hallucinations or prompt errors

---

## Phase 7: Quality Assurance & Maintenance

### Todos

- [ ] Add regression tests for any bugs found in production
- [ ] Document how to add new test cases and extend the suite
- [ ] Integrate with CI (optional, for future)

### QA Checklist

- [ ] All phases above are covered by at least one test
- [ ] Adding a new test case is documented and takes <5 minutes
- [ ] Test suite can be run before major releases

---

## References

- See `client-side-word-extraction.md` and `client-side-phoneme-extraction.md` for data format details
- See `core/gpt_prompts/` and `core/modes/` for GPT input/output schemas
- See `core/gpt_output_validator.py` for GPT output validation logic

---

## 80/20 Rule Notes

- Focus on automating the most common/critical test flows first
- Use simple JSON and plain text for test data, avoid complex DB or UI dependencies
- Parallelize test execution for speed, but keep reporting simple
- Add more test cases and edge cases over time as needed

---

_This guide is designed for rapid, maintainable implementation. Start with a few high-value test cases and expand as needed._
