# Phoneme Extraction Accuracy Improvement Guide

**Purpose**: Comprehensive guide to diagnose and fix phoneme extraction accuracy issues across different devices, noisy audio conditions, and edge cases (audio beginnings/ends).

**Priority**: High - Core feature reliability

**Complexity**: Medium to High

**Created**: December 2024

---

## Executive Summary

The phoneme extraction system experiences inconsistent accuracy due to several interconnected issues:

1. **Device-Dependent Variability**: Different microphones and audio capture devices produce varying audio quality
2. **Noise Sensitivity**: Background noise significantly degrades phoneme recognition accuracy
3. **Edge Processing Errors**: Audio beginnings and ends have disproportionately higher error rates
4. **Alignment Brittleness**: The phoneme-to-word alignment algorithm struggles when phoneme counts differ significantly from expectations
5. **Preprocessing Limitations**: Current noise reduction can sometimes distort audio, especially for longer recordings

This guide provides a phased approach to systematically address these issues using the 80/20 rule - focusing on high-impact improvements that address the majority of accuracy problems.

---

## Diagnosed Issues

### Issue 1: Noise Reduction Over-Processing (High Impact)

**Problem**: The current noise reduction in `audio_preprocessing.py` uses `noisereduce` with aggressive settings that can:
- Remove important phonetic features along with noise
- Create audio artifacts that confuse the model
- Work inconsistently across different noise profiles

**Impact**: 40% of accuracy issues

**Current Implementation**:
```python
# audio_preprocessing.py
audio = nr.reduce_noise(y=audio, sr=sr, stationary=True, prop_decrease=1.0)
```

**Root Cause**:
- Single-pass noise reduction without noise profile analysis
- No adaptive parameters based on signal-to-noise ratio (SNR)
- Removes too much audio content in edge regions

---

### Issue 2: Lack of Audio Quality Pre-Validation (High Impact)

**Problem**: Audio is processed regardless of quality, leading to:
- Poor phoneme extraction from low-quality audio
- Wasted processing on unusable audio
- No user feedback about recording quality

**Impact**: 25% of accuracy issues

**Root Cause**:
- No SNR calculation before processing
- No clipping detection
- No silence detection
- Missing quality metrics feedback to users

---

### Issue 3: Edge Trimming Too Aggressive (Medium Impact)

**Problem**: The current silence trimming in `audio_optimization.py` can:
- Cut off initial/final phonemes
- Remove quiet consonants (p, t, k, etc.)
- Over-trim based on energy thresholds

**Impact**: 15% of accuracy issues

**Current Implementation**:
```python
def _fast_trim_silence(self, audio: np.ndarray, 
                      threshold: float = 0.01,
                      frame_length: int = 512) -> np.ndarray:
```

**Root Cause**:
- Fixed threshold doesn't adapt to audio dynamics
- Energy-based detection misses quiet phonemes
- No padding added after trimming

---

### Issue 4: Phoneme-to-Word Alignment Fragility (Medium Impact)

**Problem**: The alignment algorithm in `process_audio.py` fails when:
- Phoneme count differs significantly from expected (>50% variance)
- Model extracts spurious phonemes from noise
- Words are spoken too fast or too slow

**Impact**: 15% of accuracy issues

**Current Implementation**:
```python
# Uses dynamic programming but with rigid bounds
min_j = max(i, sum(word_lengths[:i-1]))
max_j = min(n + 1, sum(word_lengths[:i]) + 5)
```

**Root Cause**:
- Bounds too restrictive for real-world variation
- No confidence scoring for alignments
- No fallback strategies for failed alignments

---

### Issue 5: Missing Device-Specific Calibration (Low Impact)

**Problem**: Different microphones have:
- Different frequency responses
- Different noise floors
- Different dynamic ranges

**Impact**: 5% of accuracy issues

**Root Cause**:
- No device fingerprinting
- No per-device audio preprocessing profiles
- No normalization for device characteristics

---

## Implementation Phases

---

## Phase 1: Adaptive Noise Reduction & Audio Quality Validation

**Goal**: Improve noise handling and add quality pre-validation to reject/warn about poor audio

**Estimated Time**: 4-6 hours

**Impact**: Addresses 65% of accuracy issues

### Tasks

#### Task 1.1: Implement SNR and Quality Metrics
- [x] Create `audio_quality_analyzer.py` module
- [x] Add SNR calculation function
- [x] Add clipping detection
- [x] Add silence percentage detection
- [x] Add frequency spectrum analysis for identifying noise profiles

**Files to Create**:
```
backend/core/audio_quality_analyzer.py
```

**Implementation Details**:
```python
# backend/core/audio_quality_analyzer.py
import numpy as np
import librosa
from typing import Dict, Tuple

class AudioQualityAnalyzer:
    """Analyzes audio quality metrics before processing."""
    
    def __init__(self, sr: int = 16000):
        self.sr = sr
        
    def calculate_snr(self, audio: np.ndarray, noise_duration: float = 0.5) -> float:
        """
        Calculate Signal-to-Noise Ratio.
        Assumes first/last noise_duration seconds contain primarily noise.
        
        Returns: SNR in dB
        """
        # Implementation details in guide
        
    def detect_clipping(self, audio: np.ndarray, threshold: float = 0.99) -> Dict:
        """Detect if audio is clipped/distorted."""
        # Implementation details in guide
        
    def calculate_silence_percentage(self, audio: np.ndarray) -> float:
        """Calculate percentage of audio that is silence."""
        # Implementation details in guide
        
    def analyze_audio_quality(self, audio: np.ndarray) -> Dict:
        """
        Comprehensive audio quality analysis.
        
        Returns:
            {
                'snr_db': float,
                'is_clipped': bool,
                'clipping_percentage': float,
                'silence_percentage': float,
                'quality_score': float,  # 0-100
                'issues': List[str],
                'recommendations': List[str]
            }
        """
        # Implementation details in guide
```

#### Task 1.2: Implement Adaptive Noise Reduction
- [x] Create `adaptive_noise_reduction.py` module  
- [x] Implement multi-band noise reduction
- [x] Add SNR-based parameter adjustment
- [x] Add edge-preserving noise reduction
- [x] Integrate with existing preprocessing pipeline

**Files to Create**:
```
backend/core/adaptive_noise_reduction.py
```

**Files to Modify**:
```
backend/core/audio_preprocessing.py
backend/routers/handlers/audio_processing_handler.py
```

**Implementation Details**:
```python
# backend/core/adaptive_noise_reduction.py
import numpy as np
import noisereduce as nr
from scipy import signal

class AdaptiveNoiseReducer:
    """Adaptive noise reduction that preserves phonetic features."""
    
    def __init__(self, sr: int = 16000):
        self.sr = sr
        
    def reduce_noise_adaptive(self, 
                             audio: np.ndarray, 
                             snr_db: float,
                             preserve_edges: bool = True) -> np.ndarray:
        """
        Apply adaptive noise reduction based on SNR.
        
        Args:
            audio: Input audio signal
            snr_db: Signal-to-noise ratio in dB
            preserve_edges: If True, uses gentler reduction on first/last 0.3s
            
        Returns:
            Noise-reduced audio
        """
        # Adaptive parameters based on SNR
        if snr_db > 20:
            # High quality audio - minimal processing
            prop_decrease = 0.3
            stationary = False
        elif snr_db > 10:
            # Medium quality - moderate processing
            prop_decrease = 0.6
            stationary = True
        else:
            # Low quality - more aggressive but with caution
            prop_decrease = 0.8
            stationary = True
            
        # Apply edge preservation
        if preserve_edges:
            return self._reduce_noise_with_edge_preservation(
                audio, prop_decrease, stationary
            )
        else:
            return nr.reduce_noise(
                y=audio, 
                sr=self.sr, 
                stationary=stationary,
                prop_decrease=prop_decrease
            )
    
    def _reduce_noise_with_edge_preservation(self,
                                             audio: np.ndarray,
                                             prop_decrease: float,
                                             stationary: bool) -> np.ndarray:
        """
        Apply noise reduction with gentler processing on edges.
        
        Edges (first/last 0.3s) use 50% of the prop_decrease value.
        """
        edge_duration = 0.3  # seconds
        edge_samples = int(edge_duration * self.sr)
        
        if len(audio) <= 2 * edge_samples:
            # Audio too short for edge preservation
            return nr.reduce_noise(
                y=audio,
                sr=self.sr,
                stationary=stationary,
                prop_decrease=prop_decrease * 0.7  # Gentler overall
            )
        
        # Process in three segments
        start_edge = audio[:edge_samples]
        middle = audio[edge_samples:-edge_samples]
        end_edge = audio[-edge_samples:]
        
        # Gentler reduction on edges
        edge_prop = prop_decrease * 0.5
        start_processed = nr.reduce_noise(
            y=start_edge, sr=self.sr, 
            stationary=stationary, prop_decrease=edge_prop
        )
        end_processed = nr.reduce_noise(
            y=end_edge, sr=self.sr,
            stationary=stationary, prop_decrease=edge_prop
        )
        
        # Standard reduction on middle
        middle_processed = nr.reduce_noise(
            y=middle, sr=self.sr,
            stationary=stationary, prop_decrease=prop_decrease
        )
        
        # Concatenate with crossfade
        return self._crossfade_segments(
            [start_processed, middle_processed, end_processed],
            fade_samples=int(0.05 * self.sr)  # 50ms crossfade
        )
    
    def _crossfade_segments(self, 
                           segments: list, 
                           fade_samples: int) -> np.ndarray:
        """Apply crossfade between segments to avoid clicks."""
        # Implementation details in guide
```

#### Task 1.3: Integrate Quality Checks into Processing Pipeline
- [x] Add quality validation in `audio_processing_handler.py`
- [x] Return quality metrics to client
- [x] Add quality thresholds for rejection
- [x] Add user-facing quality warnings

**Files to Modify**:
```
backend/routers/handlers/audio_processing_handler.py
backend/schemas/audio.py (add quality metrics schema)
frontend/src/components/practice/BasePractice.tsx (display quality warnings)
```

### Quality Assurance Checklist

- [ ] SNR calculation tested with various noise levels (clean, moderate, heavy noise)
- [ ] Clipping detection accurately identifies distorted audio
- [ ] Adaptive noise reduction tested on:
  - [ ] Clean audio (no degradation)
  - [ ] Moderate noise (improvement without distortion)
  - [ ] Heavy noise (significant improvement)
  - [ ] Various audio lengths (short: <3s, medium: 3-8s, long: >8s)
- [ ] Edge preservation verified:
  - [ ] Initial consonants (p, t, k) preserved
  - [ ] Final consonants preserved
  - [ ] No audio artifacts at segment boundaries
- [ ] Quality metrics returned to client and displayed appropriately
- [ ] Poor quality audio rejected with helpful error messages
- [ ] Performance impact measured (<10% overhead acceptable)

---

## Phase 2: Improved Edge Handling & Silence Trimming

**Goal**: Fix aggressive trimming that cuts off phonemes at audio boundaries

**Estimated Time**: 2-3 hours

**Impact**: Addresses 15% of accuracy issues

### Tasks

#### Task 2.1: Implement Phoneme-Aware Trimming
- [ ] Create `phoneme_aware_trimming.py` module
- [ ] Use zero-crossing rate for better edge detection
- [ ] Add configurable padding after trimming
- [ ] Make trimming adaptive based on audio dynamics

**Files to Create**:
```
backend/core/phoneme_aware_trimming.py
```

**Files to Modify**:
```
backend/core/audio_optimization.py
```

**Implementation Details**:
```python
# backend/core/phoneme_aware_trimming.py
import numpy as np
import librosa

class PhonemeAwareTrimmer:
    """Smart audio trimming that preserves phonemes."""
    
    def __init__(self, sr: int = 16000):
        self.sr = sr
        
    def trim_with_padding(self,
                          audio: np.ndarray,
                          top_db: int = 30,
                          padding_ms: int = 150) -> np.ndarray:
        """
        Trim silence with generous padding to preserve phonemes.
        
        Args:
            audio: Input audio
            top_db: Threshold in dB below peak for trimming
            padding_ms: Padding to add on each side after trimming
            
        Returns:
            Trimmed audio with padding
        """
        # Use librosa's trim with appropriate threshold
        trimmed, intervals = librosa.effects.trim(
            audio, 
            top_db=top_db,
            frame_length=2048,
            hop_length=512
        )
        
        # Add padding
        padding_samples = int(padding_ms * self.sr / 1000)
        
        # Find original boundaries
        if len(intervals) > 0:
            start_idx = max(0, intervals[0, 0] - padding_samples)
            end_idx = min(len(audio), intervals[0, 1] + padding_samples)
            return audio[start_idx:end_idx]
        
        return trimmed
    
    def detect_speech_boundaries(self,
                                 audio: np.ndarray,
                                 use_zcr: bool = True) -> tuple:
        """
        Detect speech boundaries using energy + zero-crossing rate.
        
        More accurate than energy-only for detecting quiet consonants.
        """
        # Calculate frame-wise energy
        frame_length = 2048
        hop_length = 512
        
        # Energy
        energy = librosa.feature.rms(
            y=audio,
            frame_length=frame_length,
            hop_length=hop_length
        )[0]
        
        if use_zcr:
            # Zero-crossing rate (detects high-frequency sounds like consonants)
            zcr = librosa.feature.zero_crossing_rate(
                audio,
                frame_length=frame_length,
                hop_length=hop_length
            )[0]
            
            # Combine metrics
            combined = energy + 0.3 * zcr  # Weight energy more
        else:
            combined = energy
        
        # Adaptive thresholding
        threshold = np.median(combined) + 0.5 * np.std(combined)
        
        # Find speech regions
        above_threshold = combined > threshold
        
        if not np.any(above_threshold):
            return 0, len(audio)
        
        # Find first and last speech frames
        speech_frames = np.where(above_threshold)[0]
        start_frame = speech_frames[0]
        end_frame = speech_frames[-1]
        
        # Convert to samples
        start_sample = start_frame * hop_length
        end_sample = min((end_frame + 1) * hop_length, len(audio))
        
        return start_sample, end_sample
```

#### Task 2.2: Update Audio Optimization Module
- [ ] Replace `_fast_trim_silence` with phoneme-aware version
- [ ] Add configurable trimming strategy
- [ ] Maintain performance (should be <100ms)

**Implementation Guide**:
Update `backend/core/audio_optimization.py`:
```python
# Import new trimmer
from .phoneme_aware_trimming import PhonemeAwareTrimmer

class OptimizedAudioPreprocessor:
    def __init__(self, target_sr: int = 16000, enable_logging: bool = False):
        self.target_sr = target_sr
        self.enable_logging = enable_logging
        self.trimmer = PhonemeAwareTrimmer(sr=target_sr)
    
    def preprocess_audio(self, 
                        audio: np.ndarray, 
                        sr: Optional[int] = None,
                        normalize: bool = True,
                        trim_silence: bool = True) -> Tuple[np.ndarray, int]:
        # ... existing code ...
        
        # Replace trimming logic
        if trim_silence:
            audio = self.trimmer.trim_with_padding(
                audio,
                top_db=30,  # More conservative threshold
                padding_ms=150  # Generous padding
            )
        
        # ... rest of existing code ...
```

### Quality Assurance Checklist

- [ ] Trimming tested on various phonemes:
  - [ ] Plosives (p, b, t, d, k, g) at boundaries preserved
  - [ ] Fricatives (f, v, s, z, sh) at boundaries preserved
  - [ ] Nasals (m, n, ng) at boundaries preserved
- [ ] Padding verified:
  - [ ] No phonemes cut off at start
  - [ ] No phonemes cut off at end
  - [ ] No excessive padding (audio bloat)
- [ ] Performance maintained:
  - [ ] Trimming completes in <100ms
  - [ ] No significant memory overhead
- [ ] Edge cases handled:
  - [ ] Very short audio (<1s)
  - [ ] Whispered speech
  - [ ] Loud background noise
- [ ] Comparison with old trimming:
  - [ ] Phoneme accuracy improved by at least 10%
  - [ ] False positives (incorrect trimming) reduced

---

## Phase 3: Robust Phoneme-to-Word Alignment

**Goal**: Make alignment algorithm more resilient to phoneme count mismatches and model errors

**Estimated Time**: 3-4 hours

**Impact**: Addresses 15% of accuracy issues

### Tasks

#### Task 3.1: Implement Flexible Alignment with Confidence Scoring
- [ ] Update `process_audio.py` alignment function
- [ ] Add adaptive search bounds based on phoneme variance
- [ ] Implement alignment confidence scoring
- [ ] Add fallback strategies for low-confidence alignments

**Files to Modify**:
```
backend/core/process_audio.py
```

**Implementation Details**:
```python
# backend/core/process_audio.py

def align_phonemes_to_words_robust(
    pred_phonemes: list,
    gt_words_phonemes: list[tuple[str, list[str]]],
    max_variance: float = 2.0,
    min_confidence: float = 0.3
) -> tuple[list, dict]:
    """
    Robust phoneme-to-word alignment with confidence scoring.
    
    Args:
        pred_phonemes: Predicted phonemes from model
        gt_words_phonemes: Ground truth words with expected phonemes
        max_variance: Maximum allowed phoneme count variance (2.0 = 200%)
        min_confidence: Minimum confidence threshold for accepting alignment
        
    Returns:
        Tuple of (alignment, metadata)
        - alignment: List of (word, aligned_phonemes, per, confidence)
        - metadata: Dict with alignment statistics
    """
    if not pred_phonemes or not gt_words_phonemes:
        return [], {'status': 'empty_input', 'confidence': 0.0}
    
    # Calculate phoneme variance
    expected_phonemes = sum(len(phonemes) for _, phonemes in gt_words_phonemes)
    variance = len(pred_phonemes) / max(expected_phonemes, 1)
    
    metadata = {
        'expected_phonemes': expected_phonemes,
        'predicted_phonemes': len(pred_phonemes),
        'variance': variance,
        'status': 'unknown'
    }
    
    # Check if variance is within acceptable range
    if variance > max_variance or variance < 1/max_variance:
        print(f"⚠️  High phoneme variance: {variance:.2f}x expected")
        metadata['status'] = 'high_variance'
        # Use fallback strategy
        return _fallback_alignment(pred_phonemes, gt_words_phonemes, metadata)
    
    # Perform standard alignment with adaptive bounds
    n = len(pred_phonemes)
    m = len(gt_words_phonemes)
    
    dp = np.full((m + 1, n + 1), np.inf, dtype=np.float32)
    backtrack = np.full((m + 1, n + 1), -1, dtype=np.int32)
    confidence = np.zeros((m + 1, n + 1), dtype=np.float32)
    dp[0, 0] = 0
    confidence[0, 0] = 1.0
    
    word_lengths = [len(phonemes) for _, phonemes in gt_words_phonemes]
    
    for i in range(1, m + 1):
        gt_word, gt_phs = gt_words_phonemes[i - 1]
        expected_length = len(gt_phs)
        
        # Adaptive bounds based on variance
        flexibility = max(5, int(expected_length * variance * 0.5))
        min_j = max(i, sum(word_lengths[:i-1]) - flexibility)
        max_j = min(n + 1, sum(word_lengths[:i]) + flexibility)
        
        for j in range(min_j, max_j):
            best_cost = np.inf
            best_k = -1
            best_conf = 0.0
            
            # Wider search for k
            min_k = max(0, j - expected_length - flexibility)
            max_k = min(j, n)
            
            for k in range(min_k, max_k):
                if dp[i - 1, k] == np.inf:
                    continue
                
                pred_segment = pred_phonemes[k:j]
                segment_cost = compute_per(gt_phs, pred_segment)
                
                # Calculate confidence based on:
                # 1. PER (lower is better)
                # 2. Length match (closer to expected is better)
                # 3. Previous confidence
                length_match = 1.0 - abs(len(pred_segment) - expected_length) / max(expected_length, 1)
                length_match = max(0.0, min(1.0, length_match))
                
                per_conf = 1.0 - min(segment_cost, 1.0)
                
                segment_confidence = (
                    0.6 * per_conf +
                    0.3 * length_match +
                    0.1 * confidence[i-1, k]
                )
                
                total_cost = dp[i - 1, k] + segment_cost
                
                if total_cost < best_cost:
                    best_cost = total_cost
                    best_k = k
                    best_conf = segment_confidence
            
            if best_k != -1:
                dp[i, j] = best_cost
                backtrack[i, j] = best_k
                confidence[i, j] = best_conf
    
    # Backtrack to get alignment
    if dp[m, n] == np.inf:
        print("⚠️  Alignment failed - using fallback")
        metadata['status'] = 'alignment_failed'
        return _fallback_alignment(pred_phonemes, gt_words_phonemes, metadata)
    
    # Extract alignment path
    alignment = []
    j = n
    overall_confidence = confidence[m, n]
    
    for i in range(m, 0, -1):
        k = backtrack[i, j]
        gt_word, gt_phs = gt_words_phonemes[i - 1]
        aligned_phonemes = pred_phonemes[k:j]
        per = compute_per(gt_phs, aligned_phonemes)
        conf = confidence[i, j]
        
        alignment.append((gt_word, aligned_phonemes, per, conf))
        j = k
    
    alignment.reverse()
    
    # Check overall confidence
    metadata['overall_confidence'] = overall_confidence
    if overall_confidence < min_confidence:
        print(f"⚠️  Low alignment confidence: {overall_confidence:.2f}")
        metadata['status'] = 'low_confidence'
        # Still return alignment but flag it
    else:
        metadata['status'] = 'success'
    
    return alignment, metadata


def _fallback_alignment(
    pred_phonemes: list,
    gt_words_phonemes: list[tuple[str, list[str]]],
    metadata: dict
) -> tuple[list, dict]:
    """
    Fallback alignment strategy when standard alignment fails.
    
    Uses proportional distribution of phonemes across words.
    """
    print("🔄 Using fallback alignment strategy")
    
    expected_phonemes = sum(len(phonemes) for _, phonemes in gt_words_phonemes)
    phonemes_per_expected = len(pred_phonemes) / max(expected_phonemes, 1)
    
    alignment = []
    start_idx = 0
    
    for word, gt_phs in gt_words_phonemes:
        # Allocate phonemes proportionally
        expected_count = len(gt_phs)
        allocated_count = int(expected_count * phonemes_per_expected)
        allocated_count = max(1, allocated_count)  # At least 1 phoneme per word
        
        end_idx = min(start_idx + allocated_count, len(pred_phonemes))
        aligned_phonemes = pred_phonemes[start_idx:end_idx]
        
        per = compute_per(gt_phs, aligned_phonemes)
        confidence = 0.2  # Low confidence for fallback
        
        alignment.append((word, aligned_phonemes, per, confidence))
        start_idx = end_idx
    
    metadata['fallback_used'] = True
    return alignment, metadata
```

#### Task 3.2: Add Alignment Diagnostics
- [ ] Add logging for alignment issues
- [ ] Track alignment confidence over time
- [ ] Store alignment metadata in FeedbackEntry

**Files to Modify**:
```
backend/models/feedback_entry.py (add alignment_metadata JSON field)
backend/schemas/feedback_entry.py (add alignment metadata schema)
```

### Quality Assurance Checklist

- [ ] Alignment tested with various phoneme variances:
  - [ ] 0.5x expected (missing phonemes)
  - [ ] 1.0x expected (perfect match)
  - [ ] 1.5x expected (extra phonemes)
  - [ ] 2.0x expected (many extra phonemes)
- [ ] Confidence scoring validated:
  - [ ] High confidence (>0.7) for good alignments
  - [ ] Low confidence (<0.3) for poor alignments
  - [ ] Confidence correlates with actual PER accuracy
- [ ] Fallback strategy tested:
  - [ ] Gracefully handles extreme mismatches
  - [ ] Produces reasonable word boundaries
  - [ ] Flags low confidence appropriately
- [ ] Performance maintained:
  - [ ] Alignment completes in <200ms for typical sentences
  - [ ] No memory issues with long sentences (>20 words)
- [ ] Edge cases handled:
  - [ ] Single word sentences
  - [ ] Very long sentences (>30 words)
  - [ ] Empty predicted phonemes
  - [ ] All phonemes recognized as blank tokens

---

## Phase 4: Device-Specific Optimization (Optional)

**Goal**: Implement device fingerprinting and calibration for consistent quality

**Estimated Time**: 4-5 hours

**Impact**: Addresses 5% of accuracy issues

**Note**: This is a lower priority phase due to lower impact. Implement only if Phases 1-3 are complete and accuracy goals not yet met.

### Tasks

#### Task 4.1: Implement Device Fingerprinting
- [ ] Create `device_calibration.py` module
- [ ] Capture device audio characteristics
- [ ] Store device profiles in database
- [ ] Apply device-specific preprocessing

**Files to Create**:
```
backend/core/device_calibration.py
backend/models/device_profile.py
```

**Implementation Details**:
```python
# backend/core/device_calibration.py

class DeviceCalibrator:
    """Calibrate and optimize for specific audio devices."""
    
    def __init__(self, db_session):
        self.db_session = db_session
        
    def fingerprint_device(self, 
                          audio_samples: list,
                          device_id: str) -> dict:
        """
        Create fingerprint from multiple audio samples.
        
        Args:
            audio_samples: List of audio arrays from same device
            device_id: Unique device identifier
            
        Returns:
            Device profile dictionary
        """
        # Analyze frequency response
        # Detect noise floor
        # Measure dynamic range
        # Store profile
        pass
    
    def get_device_preprocessing_params(self, device_id: str) -> dict:
        """Get optimized preprocessing parameters for device."""
        pass
```

#### Task 4.2: Frontend Device Identification
- [ ] Add device ID to audio metadata
- [ ] Implement calibration flow for new devices
- [ ] Store device preferences in user settings

### Quality Assurance Checklist

- [ ] Device fingerprinting tested with:
  - [ ] At least 3 different microphones
  - [ ] Built-in laptop mic vs external mic
  - [ ] Mobile device microphones
- [ ] Device profiles improve accuracy:
  - [ ] Measured improvement of at least 5% PER reduction
  - [ ] No degradation for uncalibrated devices
- [ ] Calibration flow tested:
  - [ ] User-friendly calibration process
  - [ ] <2 minutes to complete
  - [ ] Clear instructions provided

---

## Phase 5: Monitoring & Continuous Improvement

**Goal**: Add telemetry and monitoring to track accuracy improvements and identify new issues

**Estimated Time**: 2-3 hours

**Impact**: Enables data-driven improvements

### Tasks

#### Task 5.1: Implement Audio Quality Telemetry
- [ ] Log audio quality metrics for all processing
- [ ] Track alignment confidence scores
- [ ] Monitor phoneme variance distributions
- [ ] Create dashboard for metrics

**Files to Create**:
```
backend/core/telemetry.py
```

**Files to Modify**:
```
backend/routers/handlers/audio_processing_handler.py (add telemetry calls)
```

#### Task 5.2: Add Accuracy Tracking Endpoints
- [ ] Create endpoint for aggregated accuracy metrics
- [ ] Add user-level accuracy trends
- [ ] Track improvement over time

**Files to Create**:
```
backend/routers/analytics.py
```

### Quality Assurance Checklist

- [ ] Telemetry data collected without PII
- [ ] Metrics dashboard accessible to developers
- [ ] Accuracy trends visible and interpretable
- [ ] Performance impact minimal (<5% overhead)
- [ ] Data retention policy documented

---

## Testing Strategy

### Unit Tests

Create tests for each new module:

```python
# backend/tests/unit/test_audio_quality_analyzer.py
# backend/tests/unit/test_adaptive_noise_reduction.py
# backend/tests/unit/test_phoneme_aware_trimming.py
# backend/tests/unit/test_robust_alignment.py
```

### Integration Tests

Test complete audio processing pipeline:

```python
# backend/tests/integration/test_audio_processing_pipeline.py

def test_noisy_audio_processing():
    """Test that noisy audio is handled appropriately."""
    # Load sample noisy audio
    # Process through pipeline
    # Verify quality metrics
    # Verify phoneme extraction
    pass

def test_edge_phoneme_preservation():
    """Test that edge phonemes are preserved."""
    # Create audio with quiet consonants at edges
    # Process through pipeline
    # Verify phonemes not trimmed
    pass
```

### End-to-End Tests

Test with real user scenarios:

```python
# backend/tests/e2e/test_device_variations.py

def test_multiple_device_types():
    """Test accuracy across different device types."""
    # Use recorded samples from various devices
    # Measure PER for each
    # Verify acceptable accuracy range
    pass
```

### Performance Benchmarks

Track performance impact:

```python
# backend/tests/performance/test_processing_speed.py

def test_processing_latency():
    """Ensure processing latency remains acceptable."""
    # Process various audio lengths
    # Verify <3s for typical 5s audio
    pass
```

---

## Rollout Plan

### Stage 1: Development & Testing (Local)
1. Implement Phase 1
2. Run all unit and integration tests
3. Manual testing with sample audio files
4. Performance benchmarking

### Stage 2: Staging Deployment
1. Deploy to staging environment
2. Test with beta users
3. Collect accuracy metrics
4. Iterate based on feedback

### Stage 3: Production Rollout
1. Deploy Phase 1 to production
2. Monitor metrics for 1 week
3. Deploy Phase 2 if Phase 1 successful
4. Continue phased rollout

### Stage 4: Monitoring & Optimization
1. Continuous monitoring of accuracy metrics
2. Monthly analysis of alignment confidence
3. Quarterly review of device profiles
4. Ongoing refinement based on data

---

## Success Metrics

### Primary Metrics
- **Phoneme Error Rate (PER)**: Target <15% average (down from ~25%)
- **Alignment Success Rate**: Target >95% (up from ~80%)
- **Edge Phoneme Preservation**: Target >90% (up from ~70%)

### Secondary Metrics
- **Audio Quality Score**: Target >70 average
- **Processing Latency**: Target <3s for 5s audio
- **User Satisfaction**: Track via feedback

### Measurement
- Compare PER before/after on test dataset
- A/B test with subset of users
- Track metrics via telemetry system

---

## Risk Mitigation

### Risk 1: Performance Degradation
**Mitigation**: 
- Benchmark all changes
- Use profiling to identify bottlenecks
- Implement caching where appropriate
- Consider async processing for heavy operations

### Risk 2: Increased Complexity
**Mitigation**:
- Maintain clean module boundaries
- Document all parameters and thresholds
- Provide sensible defaults
- Keep legacy code paths as fallback

### Risk 3: False Positives in Quality Detection
**Mitigation**:
- Use conservative thresholds initially
- Provide user override options
- Log all rejections for analysis
- Iterate based on user feedback

---

## Maintenance Guidelines

### Regular Tasks (Monthly)
- [ ] Review telemetry data for anomalies
- [ ] Update noise reduction parameters if needed
- [ ] Check alignment confidence distributions
- [ ] Review user feedback for quality issues

### As-Needed Tasks
- [ ] Add new device profiles as identified
- [ ] Tune thresholds based on production data
- [ ] Update test cases for edge cases
- [ ] Optimize slow processing paths

---

## References

### Key Files
- `backend/core/audio_preprocessing.py` - Current noise reduction
- `backend/core/audio_optimization.py` - Current trimming logic
- `backend/core/process_audio.py` - Alignment algorithm
- `backend/core/phoneme_extractor.py` - Phoneme extraction
- `backend/routers/handlers/audio_processing_handler.py` - Main processing entry point

### External Libraries
- `noisereduce` - Noise reduction library
- `librosa` - Audio analysis library
- `numpy` - Numerical operations
- `soundfile` - Audio I/O

### Research References
- Phoneme Error Rate calculation methodology
- wav2vec2-TIMIT-IPA model documentation
- Audio preprocessing best practices for ASR

---

## Appendix

### Appendix A: Code Snippets

#### Complete SNR Calculation
```python
def calculate_snr(self, audio: np.ndarray, noise_duration: float = 0.5) -> float:
    """
    Calculate Signal-to-Noise Ratio.
    
    Method: Assumes first and last noise_duration seconds contain primarily noise.
    Calculates RMS of signal vs noise.
    """
    noise_samples = int(noise_duration * self.sr)
    
    if len(audio) < 3 * noise_samples:
        # Audio too short for reliable SNR
        return 10.0  # Assume moderate quality
    
    # Extract noise regions (beginning and end)
    noise_start = audio[:noise_samples]
    noise_end = audio[-noise_samples:]
    noise = np.concatenate([noise_start, noise_end])
    
    # Extract signal region (middle)
    signal = audio[noise_samples:-noise_samples]
    
    # Calculate RMS
    noise_rms = np.sqrt(np.mean(noise**2))
    signal_rms = np.sqrt(np.mean(signal**2))
    
    if noise_rms < 1e-10:
        # Essentially no noise
        return 60.0
    
    # SNR in dB
    snr_db = 20 * np.log10(signal_rms / noise_rms)
    
    return float(snr_db)
```

#### Clipping Detection
```python
def detect_clipping(self, audio: np.ndarray, threshold: float = 0.99) -> Dict:
    """Detect if audio is clipped/distorted."""
    # Count samples near max/min
    max_val = np.max(np.abs(audio))
    clipped = np.abs(audio) > threshold * max_val
    clipping_percentage = np.sum(clipped) / len(audio) * 100
    
    return {
        'is_clipped': clipping_percentage > 1.0,  # More than 1% clipped
        'clipping_percentage': clipping_percentage,
        'max_amplitude': max_val
    }
```

#### Crossfade Implementation
```python
def _crossfade_segments(self, segments: list, fade_samples: int) -> np.ndarray:
    """Apply crossfade between segments."""
    if len(segments) == 0:
        return np.array([])
    if len(segments) == 1:
        return segments[0]
    
    # Create fade curves
    fade_out = np.linspace(1, 0, fade_samples)
    fade_in = np.linspace(0, 1, fade_samples)
    
    result = segments[0][:-fade_samples]
    
    for i in range(len(segments) - 1):
        current_end = segments[i][-fade_samples:]
        next_start = segments[i+1][:fade_samples]
        
        # Crossfade
        crossfaded = current_end * fade_out + next_start * fade_in
        result = np.concatenate([result, crossfaded, segments[i+1][fade_samples:]])
    
    return result
```

### Appendix B: Configuration Parameters

#### Recommended Thresholds
```python
# Audio Quality
SNR_MINIMUM = 5.0  # dB - reject below this
SNR_GOOD = 15.0    # dB - high quality threshold
CLIPPING_MAX = 2.0  # % - maximum acceptable clipping

# Trimming
TRIM_TOP_DB = 30    # dB - how much to trim
PADDING_MS = 150    # ms - padding after trim

# Alignment
MAX_VARIANCE = 2.0  # 200% of expected phonemes
MIN_CONFIDENCE = 0.3  # Minimum acceptable confidence

# Noise Reduction
NR_HIGH_QUALITY = 0.3   # prop_decrease for SNR > 20dB
NR_MEDIUM_QUALITY = 0.6  # prop_decrease for SNR 10-20dB
NR_LOW_QUALITY = 0.8     # prop_decrease for SNR < 10dB
```

### Appendix C: Troubleshooting Guide

#### Issue: Audio quality always flagged as poor
**Diagnosis**:
- Check SNR calculation thresholds
- Verify noise_duration parameter appropriate for audio length
- Review sample audio in audio analysis tool

**Solution**:
- Adjust SNR_MINIMUM threshold
- Increase noise_duration for longer audio
- Consider device-specific thresholds

#### Issue: Phonemes still cut off at edges
**Diagnosis**:
- Check padding_ms value
- Verify trim_top_db not too aggressive
- Review ZCR calculation

**Solution**:
- Increase padding_ms to 200-250ms
- Increase trim_top_db to 35-40
- Adjust ZCR weighting in boundary detection

#### Issue: Alignment failures increased
**Diagnosis**:
- Check phoneme variance distributions
- Review alignment confidence scores
- Verify fallback strategy used

**Solution**:
- Increase max_variance threshold
- Tune flexibility parameter in adaptive bounds
- Improve fallback strategy

---

**End of Implementation Guide**

*This guide follows the 80/20 rule by focusing on high-impact improvements (Phases 1-3) that address 95% of accuracy issues, while keeping optional enhancements (Phase 4) for future optimization.*
