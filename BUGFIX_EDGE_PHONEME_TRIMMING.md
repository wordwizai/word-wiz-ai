# Edge Phoneme Trimming Bug Fix

## Problem Statement
Users reported that the AI process drops significantly in accuracy for the last couple of words that they speak. Investigation revealed this was caused by the phoneme-aware trimming model cutting off audio at the end of recordings.

## Root Cause

### Location
`backend/core/phoneme_aware_trimming.py`, function `detect_speech_boundaries()`, lines 145-151

### The Bug
The code was incorrectly calculating the end boundary of detected speech:

```python
# OLD (BUGGY) CODE
speech_frames = np.where(above_threshold)[0]
start_frame = speech_frames[0]
end_frame = speech_frames[-1]

# Convert to samples
start_sample = start_frame * hop_length
end_sample = min((end_frame + 1) * hop_length, len(audio))  # ❌ WRONG
```

### Why It's Wrong

The audio analysis uses overlapping frames:
- **Frame length**: 2048 samples (~128ms at 16kHz sample rate)
- **Hop length**: 512 samples (~32ms) - the step size between frames
- **Overlap**: Frame length - hop length = 1536 samples (~96ms)

When we detect the last frame containing speech (`end_frame`), we need to include the **entire frame duration**, not just hop forward by one hop length.

#### Mathematical Explanation

If the last speech is detected at frame index `N`:
- That frame starts at sample `N * hop_length`
- That frame contains data from samples `[N * hop_length, N * hop_length + frame_length]`
- The old code calculated: `end_sample = (N + 1) * hop_length`
- This only includes: `[N * hop_length, (N + 1) * hop_length]` = 512 samples
- But the frame actually spans: `[N * hop_length, N * hop_length + frame_length]` = 2048 samples

**Missing audio**: `frame_length - hop_length = 2048 - 512 = 1536 samples (~96ms)**

### Impact

96 milliseconds might not sound like much, but in speech processing:
- Most consonants are very short (20-80ms)
- Final consonants are often even shorter
- Words can be pronounced quickly, with the last syllable in < 100ms

**Examples of phonemes that are typically < 96ms:**
- Stop consonants: /p/, /t/, /k/, /b/, /d/, /g/ (20-40ms)
- Fricatives: /s/, /f/, /θ/ (50-80ms) 
- Final nasals: /m/, /n/, /ŋ/ when unreleased (30-60ms)

This means the bug was **consistently cutting off final consonants**, making it appear that users:
- Weren't pronouncing the last word completely
- Had poor pronunciation accuracy on sentence endings
- Had dropped the final phonemes

## The Fix

```python
# NEW (FIXED) CODE
speech_frames = np.where(above_threshold)[0]
start_frame = speech_frames[0]
end_frame = speech_frames[-1]

# Convert to samples
# IMPORTANT: For end_frame, we need to include the entire frame duration (frame_length),
# not just hop forward by hop_length. This ensures we don't cut off the last phonemes.
start_sample = start_frame * hop_length
end_sample = min(end_frame * hop_length + frame_length, len(audio))  # ✅ CORRECT
```

This ensures we include the full duration of the last frame that contains speech, preserving those critical final phonemes.

## Testing

Created `backend/tests/test_edge_phoneme_trimming_fix.py` with three test cases:

1. **test_comparison_old_vs_new()**: Demonstrates the mathematical difference
   - Shows exactly how much audio was being lost (1536 samples = 96ms)

2. **test_frame_boundary_calculation()**: Tests the boundary detection directly
   - Creates audio with speech at the very end
   - Verifies the end boundary is correctly calculated
   - Ensures minimal gap between detected end and actual audio end

3. **test_ending_preservation()**: Tests with realistic audio
   - Generates audio with quiet consonant-like ending
   - Verifies the ending is preserved after trimming
   - Checks that we don't over-trim

## Expected Improvements

After this fix, users should see:
- ✅ Improved accuracy on final words of sentences
- ✅ Better detection of final consonants (p, t, k, s, etc.)
- ✅ More accurate phoneme error rates (PER) for sentence endings
- ✅ Reduced complaints about the AI "not hearing" the last words

## Verification Steps

1. Run the new test suite:
   ```bash
   cd backend
   python tests/test_edge_phoneme_trimming_fix.py
   ```

2. Run existing edge handling tests to ensure no regression:
   ```bash
   python tests/test_phase2_edge_handling.py
   ```

3. Monitor production metrics:
   - Track average PER for final words vs. middle words
   - Should see convergence (final words PER approaching middle words PER)
   - Track user feedback on pronunciation accuracy

## Related Files

- `backend/core/phoneme_aware_trimming.py` - The fixed file
- `backend/core/audio_optimization.py` - Uses the trimmer
- `backend/core/phoneme_extractor.py` - Uses OptimizedAudioPreprocessor
- `backend/core/phoneme_extractor_onnx.py` - Uses OptimizedAudioPreprocessor
- `implementation_guides/PHONEME_EXTRACTION_ACCURACY_IMPROVEMENTS.md` - Background on the issue

## Notes

- The `_fast_trim_silence()` fallback method in `audio_optimization.py` does NOT have this bug because it uses non-overlapping frames (both frame_length and hop are 512)
- The default setting is `use_phoneme_aware_trim=True`, so all users are affected by this bug
- The fix is backward compatible and should not break any existing functionality
- The fix actually makes the existing tests PASS BETTER (higher preservation ratios)

## Technical Details

### Frame Analysis Parameters
- Sample rate: 16000 Hz
- Frame length: 2048 samples (~128ms)
- Hop length: 512 samples (~32ms)
- Frame overlap: 1536 samples (~96ms)

### Why Overlapping Frames?
Audio analysis uses overlapping frames because:
1. Captures temporal changes more smoothly
2. Reduces edge effects from windowing
3. Provides better frequency resolution
4. Standard practice in speech processing

### Why This Bug Wasn't Caught Earlier
1. Tests checked preservation ratios, not exact boundaries
2. 96ms loss is small enough to not obviously fail ratio checks
3. The trimming "worked" (removed silence) but was too aggressive
4. User complaints about "last words" were attributed to model accuracy, not trimming

## References

- Issue: "AI process drops significantly in accuracy for the last couple of words"
- Implementation guide: `implementation_guides/PHONEME_EXTRACTION_ACCURACY_IMPROVEMENTS.md`
- Phase 2 implementation (where bug was introduced): Improved Edge Handling & Silence Trimming
- Related tests: `backend/tests/test_phase2_edge_handling.py`
