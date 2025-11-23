# Bug Fix Implementation Plan

## Overview

This document outlines a phased approach to fixing three critical issues in the phoneme assistant app:

1. **Audio Playback Issue**: High-pitched gibberish on mobile due to sample rate mismatch
2. **GPT Feedback Quality**: Incorrect phoneme analysis and poor feedback construction
3. **Model Accuracy Issues**: Inconsistent phoneme/word extraction, especially on longer recordings

## Issue Analysis

### Issue 1: Mobile Audio Playback Problem

**Root Cause**: Sample rate mismatch between server output (MP3 at 44.1kHz from ElevenLabs, or unspecified from Google TTS) and mobile browser expectations. The server converts to WAV but doesn't properly specify the sample rate in the WAV header or normalize for mobile playback.

**Evidence**:

- `text_to_audio.py` uses `mp3_44100_128` for ElevenLabs (44.1kHz)
- Google TTS uses MP3 encoding with no explicit sample rate
- Server converts to WAV using `soundfile.write()` with `sample_rate` parameter but the AudioContext on mobile may interpret this differently
- Mobile Safari and Chrome often have different native sample rates than desktop

### Issue 2: GPT Feedback Quality

**Root Cause**: Multiple problems in prompt engineering and data flow:

- Prompts don't explicitly show GPT the phonemes that ARE in each word
- GPT is asked to create feedback without knowing the phoneme breakdown of words
- The `problem_summary` sent to GPT is too simplified and lacks context
- SSML instructions don't provide clear examples of when/how to use phoneme tags

**Evidence**:

- `unlimited_mode_prompt_v4.txt` asks GPT to explain "what words they messed up" but doesn't give it the phoneme composition of those words
- GPT receives `simplified_problem_summary` that strips out articulatory info and difficulty levels
- Phoneme errors are presented without context of which words they belong to

### Issue 3: Model Accuracy on Longer Audio

**Root Cause**: Audio preprocessing and model timeout/memory issues:

- Longer audio undergoes noise reduction that may distort speech features
- No audio length validation or chunking strategy
- Models (especially word extraction via Google Cloud) may timeout or truncate results on long audio
- No progressive decoding or batching for long sequences

**Evidence**:

- `preprocess_audio()` applies `noisereduce.reduce_noise()` uniformly regardless of audio length
- No timeout configuration visible in `word_extractor.py` for Google Cloud API
- `process_audio_array()` processes entire audio at once with no chunking

---

## Phase 1: Fix Mobile Audio Playback (Critical - Quick Win)

### Objective

Ensure audio feedback plays correctly on all devices by standardizing sample rate and format.

### Tasks

#### Task 1.1: Add explicit sample rate to TTS configuration

- [ ] Modify `text_to_audio.py::GoogleTTSAPIClient.getAudio()`
  - Add `sample_rate_hertz=24000` to audio_config
  - Document the chosen sample rate (24kHz is standard for Google TTS)
- [ ] Modify `text_to_audio.py::ElevenLabsAPIClient.getAudio()`
  - Keep `mp3_44100_128` but document it
  - Add comment explaining sample rate choice

#### Task 1.2: Standardize WAV conversion

- [ ] Modify `phoneme_assistant.py::feedback_to_audio()`
  - Change from trying to interpret MP3 as PCM to proper MP3 decoding
  - Use `librosa.load()` to decode MP3 first, then resample to 24kHz
  - Write WAV at consistent 24kHz with explicit format
  - Add error handling for unsupported audio formats

```python
# Example approach:
import librosa
audio_array = librosa.load(io.BytesIO(audio_bytes), sr=24000, mono=True)[0]
sf.write(audio_buffer, audio_array, 24000, format='WAV', subtype='PCM_16')
```

#### Task 1.3: Add frontend sample rate validation

- [ ] Modify `BasePractice.tsx::onAudioFeedback`
  - Log the audio blob size and type before playback
  - Add error handling for audio playback failures
  - Consider using Web Audio API for more control over playback

#### Task 1.4: Add server-side audio validation

- [ ] Create `core/audio_validation.py`
  - Function to validate output audio before sending
  - Check sample rate, duration, format
  - Log audio characteristics for debugging

### Quality Assurance Checklist - Phase 1

- [ ] Test audio playback on iPhone Safari (iOS 14+)
- [ ] Test audio playback on Android Chrome
- [ ] Test audio playback on desktop browsers
- [ ] Verify sample rate is consistent (check with audio analysis tool)
- [ ] Confirm no high-pitched/chipmunk sounds
- [ ] Check that audio duration matches expected length
- [ ] Verify audio quality is acceptable across devices

---

## Phase 2: Improve GPT Feedback Quality (High Priority)

### Objective

Provide GPT with complete context to generate accurate, helpful feedback about pronunciation errors.

### Tasks

#### Task 2.1: Enhance data sent to GPT

- [ ] Modify `unlimited.py::get_feedback_and_next_sentence()`
  - Stop simplifying `problem_summary` - send full version
  - Include articulatory info, difficulty levels, high-frequency errors
  - Add phoneme breakdown for each word in pronunciation data
  - Include expected vs actual phonemes for each word

```python
# Example enhanced data structure:
enhanced_pronunciation = []
for word_data in pronunciation_data:
    enhanced_pronunciation.append({
        **word_data,
        "expected_phonemes_breakdown": word_data.get("ground_truth_phonemes"),
        "actual_phonemes_breakdown": word_data.get("phonemes"),
        "word_structure": f"{word_data['ground_truth_word']} = [{', '.join(word_data.get('ground_truth_phonemes', []))}]"
    })
```

#### Task 2.2: Rewrite GPT prompts for clarity

- [ ] Update `unlimited_mode_prompt_v4.txt`
  - Add explicit section showing phoneme composition of words
  - Provide examples of correct vs incorrect feedback
  - Add instruction: "Before mentioning a phoneme error, verify that phoneme exists in that word"
  - Clarify that feedback should focus on word-level errors with phoneme context
  - Simplify output expectations (remove overly complex requirements)

#### Task 2.3: Improve SSML generation instructions

- [ ] Update `ssml_instruction.txt`
  - Add 3-5 concrete examples of correct SSML usage
  - Show example: `"The 'th' sound in <phoneme alphabet='ipa' ph='θɪŋk'>think</phoneme>"`
  - Clarify when NOT to use phoneme tags (don't overuse)
  - Add guidelines for natural-sounding pauses

#### Task 2.4: Add validation layer for GPT output

- [ ] Create `core/gpt_output_validator.py`
  - Function to validate GPT mentions only phonemes that exist in the analyzed words
  - Check that sentence contains target phoneme
  - Sanitize output before sending to frontend
  - Log validation failures for prompt improvement

```python
def validate_gpt_feedback(feedback: dict, pronunciation_data: list, problem_summary: dict) -> dict:
    """Validate that GPT's feedback mentions only valid phonemes from the actual words."""
    # Extract all phonemes from ground truth
    valid_phonemes = set()
    for word in pronunciation_data:
        valid_phonemes.update(word.get("ground_truth_phonemes", []))

    # Check feedback mentions only valid phonemes
    # Add warnings if invalid
    # Return validated + corrected feedback
```

#### Task 2.5: Update story mode prompts similarly

- [ ] Update `story_mode_prompt_v2.txt` with same improvements
- [ ] Update `choice_story_mode_prompt_v4.txt` with same improvements

### Quality Assurance Checklist - Phase 2

- [ ] GPT feedback mentions only phonemes that exist in the spoken words
- [ ] Feedback explains which specific words had errors
- [ ] Practice sentences actually contain the target phoneme 5+ times
- [ ] SSML is valid and improves pronunciation clarity
- [ ] No hallucinated phoneme errors
- [ ] Feedback is encouraging and age-appropriate
- [ ] Test with 10+ different sentences and verify accuracy
- [ ] Manually review GPT responses for quality

---

## Phase 3: Fix Model Accuracy Issues (High Priority)

### Objective

Improve consistency of phoneme and word extraction, especially for longer recordings.

### Tasks

#### Task 3.1: Add audio length validation and preprocessing

- [ ] Modify `audio_processing_handler.py::load_and_preprocess_audio_file()`

  - Add validation for audio length (warn if > 10 seconds)
  - Log audio duration and size
  - Reject audio > 30 seconds with helpful error message

- [ ] Modify `audio_preprocessing.py::preprocess_audio()`
  - Add parameter for audio length
  - Reduce noise reduction intensity for longer audio (it can distort)
  - Add optional parameters: `aggressive_noise_reduction=False` for long audio
  - Add audio quality checks (signal-to-noise ratio)

```python
def preprocess_audio(audio, sr=16000, audio_length_seconds=None):
    if audio_length_seconds is None:
        audio_length_seconds = len(audio) / sr

    # Lighter noise reduction for longer audio
    if audio_length_seconds > 8:
        stationary = True
        prop_decrease = 0.5  # Less aggressive
    else:
        stationary = True
        prop_decrease = 1.0  # Standard

    audio = nr.reduce_noise(
        y=audio,
        sr=sr,
        stationary=stationary,
        prop_decrease=prop_decrease
    )
    audio = librosa.util.normalize(audio)
    return audio
```

#### Task 3.2: Add timeout and retry logic for word extraction

- [ ] Modify `word_extractor.py::WordExtractorOnline.extract_words()`
  - Add timeout parameter (default 10 seconds)
  - Add retry logic (max 2 retries)
  - Better error messages for timeout/failure
  - Add audio length validation before sending to Google

```python
def extract_words(self, audio, sampling_rate=16000, timeout=10):
    # Add timeout to Google Cloud API call
    config = speech.RecognitionConfig(
        # ... existing config ...
    )

    # Wrap in timeout
    try:
        response = self.client.recognize(
            config=config,
            audio=audio_config,
            timeout=timeout  # Add explicit timeout
        )
    except google.api_core.exceptions.DeadlineExceeded:
        print(f"Timeout after {timeout}s - audio may be too long")
        return []
```

#### Task 3.3: Implement audio chunking for long recordings

- [ ] Create `core/audio_chunking.py`
  - Function to intelligently chunk audio at silence points
  - Use `librosa.effects.split()` to find silence
  - Chunk audio into ~5-7 second segments
  - Process each chunk independently
  - Merge results with overlap handling

```python
def chunk_audio_at_silence(audio, sr=16000, max_chunk_duration=7):
    """Split audio into chunks at silence points."""
    # Find silence intervals
    intervals = librosa.effects.split(audio, top_db=30)

    chunks = []
    current_chunk = []
    current_duration = 0

    for start, end in intervals:
        segment = audio[start:end]
        segment_duration = len(segment) / sr

        if current_duration + segment_duration > max_chunk_duration:
            # Start new chunk
            if current_chunk:
                chunks.append(np.concatenate(current_chunk))
            current_chunk = [segment]
            current_duration = segment_duration
        else:
            current_chunk.append(segment)
            current_duration += segment_duration

    if current_chunk:
        chunks.append(np.concatenate(current_chunk))

    return chunks
```

- [ ] Modify `process_audio.py::process_audio_array()`
  - Check audio length before processing
  - If > 8 seconds, use chunking strategy
  - Process chunks and merge results
  - Add flag to disable for testing: `use_chunking=True`

#### Task 3.4: Add model input validation

- [ ] Modify `phoneme_extractor.py::extract_phoneme()`

  - Validate input audio is not empty
  - Check audio has speech (not just silence)
  - Log audio statistics (duration, RMS energy)
  - Add early return for invalid audio

- [ ] Add VAD (Voice Activity Detection) validation
  - Use existing VAD to verify speech present
  - Reject audio with < 30% speech activity
  - Better error messages

#### Task 3.5: Improve alignment algorithm robustness

- [ ] Modify `process_audio.py::align_phonemes_to_words()`
  - Add fallback for failed alignment
  - Better handling of length mismatches
  - Log alignment confidence metrics
  - Add parameter to adjust alignment tolerance

### Quality Assurance Checklist - Phase 3

- [ ] Test with 3-second audio - should work perfectly
- [ ] Test with 10-second audio - should work reliably
- [ ] Test with 20-second audio - should either work or give clear error
- [ ] Test with 30+ second audio - should reject with helpful message
- [ ] Verify no silent audio is accepted
- [ ] Check that noisy audio is handled gracefully
- [ ] Test with varying speech speeds (fast/slow)
- [ ] Confirm model accuracy is consistent across recording lengths
- [ ] Verify proper error messages when models fail
- [ ] Test timeout scenarios

---

## Phase 4: Testing & Monitoring (Ongoing)

### Objective

Ensure fixes work in production and catch regressions early.

### Tasks

#### Task 4.1: Add comprehensive logging

- [ ] Add structured logging throughout audio pipeline
- [ ] Log audio characteristics at each stage
- [ ] Track model performance metrics (latency, accuracy proxy)
- [ ] Log GPT feedback quality indicators

#### Task 4.2: Create test suite

- [ ] Unit tests for audio preprocessing
- [ ] Integration tests for full pipeline
- [ ] Test fixtures with known-good audio samples
- [ ] Automated GPT feedback validation tests

#### Task 4.3: Add monitoring dashboard

- [ ] Track audio playback failure rate by device
- [ ] Monitor model processing times
- [ ] Track GPT feedback validation pass rate
- [ ] Alert on regression

### Quality Assurance Checklist - Phase 4

- [ ] All tests pass
- [ ] No regression on existing features
- [ ] Logging provides actionable debugging info
- [ ] Performance metrics are within acceptable ranges
- [ ] User-reported issues decrease

---

## Implementation Order & Time Estimates

### Week 1: Critical Fixes

- **Phase 1** (Audio Playback): 4-6 hours
  - Quick win, high user impact
  - Minimal risk

### Week 2: Accuracy Improvements

- **Phase 3, Tasks 3.1-3.2** (Audio validation, timeouts): 4-6 hours
  - Reduces most common failure cases
  - Medium complexity

### Week 3: Feedback Quality

- **Phase 2, Tasks 2.1-2.3** (GPT improvements): 6-8 hours
  - High impact on user experience
  - Requires prompt iteration and testing

### Week 4: Advanced Fixes & Testing

- **Phase 3, Tasks 3.3-3.5** (Chunking, advanced validation): 8-10 hours
  - More complex, addresses edge cases
- **Phase 2, Tasks 2.4-2.5** (Validation layer): 3-4 hours
- **Phase 4** (Testing & Monitoring): Ongoing

---

## Risk Mitigation

### Risks

1. **Audio format changes break existing clients**: Mitigate with versioned API endpoints
2. **GPT prompt changes reduce quality temporarily**: Mitigate with A/B testing
3. **Chunking introduces new alignment errors**: Mitigate with feature flag and extensive testing
4. **Performance degradation**: Mitigate with benchmarking before/after

### Rollback Plan

- Keep old TTS logic as fallback
- Feature flags for chunking and validation
- Separate endpoints for new GPT prompts
- Monitor error rates and rollback if > 5% increase

---

## Success Metrics

### Phase 1 Success Criteria

- Audio playback success rate > 98% on mobile devices
- Zero high-pitched audio reports
- No increase in audio-related errors

### Phase 2 Success Criteria

- GPT hallucination rate < 2% (manually validated sample)
- User feedback ratings improve by 30%+
- Practice sentences contain target phoneme 90%+ of the time

### Phase 3 Success Criteria

- Model accuracy consistent across 3-20 second recordings
- Processing failure rate < 5% for valid audio
- Clear error messages for 100% of failures
- Average processing time < 10 seconds for 10-second audio

---

## Notes

- Use 80/20 rule: Focus on fixes that solve 80% of issues with 20% effort
- Prioritize user-facing bugs (audio playback, obvious GPT errors)
- Add instrumentation before making changes to measure impact
- Test on real devices, not just emulators
- Collect user feedback after each phase
