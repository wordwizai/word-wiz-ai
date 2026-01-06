# Phoneme-to-Grapheme Feedback Implementation Guide

**Version:** 1.0  
**Created:** December 22, 2024  
**Status:** 📋 Planning Phase

---

## Table of Contents

1. [Overview](#overview)
2. [Problem Statement](#problem-statement)
3. [Research Findings](#research-findings)
4. [Technical Approach](#technical-approach)
5. [Implementation Phases](#implementation-phases)
6. [Data Structures](#data-structures)
7. [Quality Assurance](#quality-assurance)
8. [References](#references)

---

## Overview

This guide outlines the implementation of a phoneme-to-grapheme alignment system that enables letter-based feedback display on the frontend. Instead of showing only word-level errors, the system will highlight exactly which letters in a word correspond to missed, added, or substituted phonemes.

### Key Objectives

- **Letter-Level Feedback**: Display which specific letters were mispronounced
- **Visual Highlighting**: Color-code letters based on phoneme errors
- **Educational Value**: Help children see the connection between letters and sounds
- **Maintain Accuracy**: Ensure phoneme-grapheme mapping is reliable
- **Scalable Solution**: Start simple, add complexity as needed

### Core Insight

**We don't need a general-purpose phoneme-to-grapheme converter!**

Since we already know:
1. The target word (e.g., "cat")
2. The expected phonemes (e.g., /k/ /æ/ /t/)
3. The detected phonemes (e.g., /æ/ /t/)
4. The errors (missed: /k/, added: none, substituted: none)

We can use **forced alignment** to map errors back to specific letters in the known word.

---

## Problem Statement

### Current State

The system currently displays:
- ✅ Word-level PER (Phoneme Error Rate) scores
- ✅ Word-level color coding (green = good, red = poor)
- ✅ Phoneme-level error detection (missed, added, substituted)
- ❌ NO letter-level visualization
- ❌ NO connection between phoneme errors and specific letters

Example output today:
```
Word: "brown" (PER: 0.4)
Backend data: {
  "missed": ["b"],
  "added": ["d"],
  "substituted": []
}
```

User sees: The word "brown" colored orange (medium error)

### Desired State

Example output desired:
```
Word: "brown"
Display: "b̲rown" (with 'b' highlighted in red, 'd' shown as phantom at end)
Tooltip: "You missed the 'b' sound at the beginning and added a 'd' sound at the end"
```

User sees: Exactly which letters caused the pronunciation error

### Challenges

1. **One-to-Many Mapping**: Single phoneme can map to multiple graphemes
   - /k/ → c, k, ck, ch, cc, qu, q, cq
   - /f/ → f, ff, ph, gh

2. **Context Dependency**: Correct grapheme depends on position and surrounding letters
   - /k/ at start: usually 'c' or 'k'
   - /k/ at end after short vowel: usually 'ck'

3. **Silent Letters**: Letters that don't produce phonemes
   - "knight" → /n/ /aɪ/ /t/ (k, g, h are silent)

4. **Digraphs**: Two letters representing one phoneme
   - "sh" → /ʃ/
   - "th" → /θ/ or /ð/

---

## Research Findings

### Phoneme-to-Grapheme Conversion Approaches

| Approach | Description | Pros | Cons | Recommended? |
|----------|-------------|------|------|--------------|
| **Dictionary-Based** | Use CMU Pronouncing Dictionary with grapheme annotations | Fast, accurate for known words | Fails on novel words, large size | ✅ Phase 1 |
| **Rule-Based** | Apply orthographic rules based on context | Works on novel words | Complex, many exceptions | ✅ Phase 2 |
| **Forced Alignment** | Align known word phonemes to graphemes using DP | Leverages known word, very accurate | Only works when word is known | ✅ **PRIMARY** |
| **ML Model (Seq2Seq)** | Train model on phoneme-grapheme pairs | Learns patterns automatically | Requires training, compute cost | ⏸️ Phase 4 (optional) |
| **Montreal Forced Aligner** | Use MFA tool for alignment | Professional-grade alignment | Requires audio files, complex setup | ⏸️ Future (if needed) |

### Recommended Strategy: **Forced Alignment with Fallback**

**Phase 1-3**: Implement forced alignment algorithm that:
1. Takes known word graphemes: `['c', 'a', 't']`
2. Takes expected phonemes: `[/k/, /æ/, /t/]`
3. Takes detected phonemes: `[/æ/, /t/]` (missed /k/)
4. Aligns using dynamic programming
5. Maps errors to specific grapheme positions

**Phase 4** (Optional): Add ML model for:
- Novel/misspelled words
- Improved alignment accuracy
- Complex cases (multiple valid mappings)

---

## Technical Approach

### Core Algorithm: Phoneme-Grapheme Forced Alignment

The key insight is that we can leverage the existing dynamic programming alignment code from `process_audio.py` (the `align_sequences` function) and extend it to track grapheme positions.

#### Algorithm Steps

1. **Grapheme Segmentation**: Break word into phoneme-producing units
   ```python
   word = "cat"
   graphemes = ['c', 'a', 't']
   expected_phonemes = [/k/, /æ/, /t/]
   ```

2. **Phoneme-Grapheme Pairing**: Create initial mapping
   ```python
   phoneme_grapheme_map = {
       /k/: [0],    # position 0 = 'c'
       /æ/: [1],    # position 1 = 'a'
       /t/: [2],    # position 2 = 't'
   }
   ```

3. **Error Alignment**: Map detected errors to grapheme positions
   ```python
   # Input: missed = [/k/], detected = [/æ/, /t/]
   # Output: grapheme_errors = {0: 'missed'}  # position 0 (letter 'c')
   ```

4. **Multi-Grapheme Handling**: Handle digraphs and trigraphs
   ```python
   word = "ship"
   graphemes = ['sh', 'i', 'p']  # 'sh' is one unit
   expected_phonemes = [/ʃ/, /ɪ/, /p/]
   ```

#### Complexity Cases

**Case 1: Simple One-to-One**
```
Word: "cat"
Graphemes: ['c', 'a', 't']
Expected: [/k/, /æ/, /t/]
Detected: [/æ/, /t/]
Result: Letter 'c' (position 0) missed
```

**Case 2: Digraph**
```
Word: "ship"
Graphemes: ['sh', 'i', 'p']
Expected: [/ʃ/, /ɪ/, /p/]
Detected: [/ɪ/, /p/]
Result: Grapheme 'sh' (position 0) missed
```

**Case 3: Silent Letter**
```
Word: "knight"
Graphemes: ['k', 'n', 'igh', 't']  # 'k' is silent
Expected: [/n/, /aɪ/, /t/]  # no /k/ phoneme
Detected: [/aɪ/, /t/]
Result: Grapheme 'n' (position 1) missed
```

**Case 4: Substitution**
```
Word: "cat"
Graphemes: ['c', 'a', 't']
Expected: [/k/, /æ/, /t/]
Detected: [/k/, /ɛ/, /t/]  # said /ɛ/ instead of /æ/
Result: Letter 'a' (position 1) substituted
```

### Implementation Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Backend                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. process_audio.py (existing)                             │
│     ├─ align_phonemes_to_words()                            │
│     ├─ align_sequences()                                    │
│     └─ Returns: missed, added, substituted phonemes         │
│                                                              │
│  2. NEW: phoneme_grapheme_aligner.py                        │
│     ├─ align_phonemes_to_graphemes()                        │
│     ├─ segment_word_to_graphemes()                          │
│     ├─ map_phoneme_errors_to_positions()                    │
│     └─ Returns: grapheme_errors with positions              │
│                                                              │
│  3. process_audio.py (enhanced)                             │
│     └─ Call phoneme_grapheme_aligner after phoneme analysis │
│        Add grapheme_errors to response JSON                 │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ JSON API Response
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. WordBadge.tsx (enhanced)                                │
│     ├─ Receive grapheme_errors from API                     │
│     ├─ Highlight letters based on error type                │
│     │  - Red: missed phonemes                               │
│     │  - Orange: substituted phonemes                       │
│     │  - Green dashed: added phonemes (phantom)             │
│     └─ Show tooltips with error explanations                │
│                                                              │
│  2. WordBadgeRow.tsx (enhanced)                             │
│     └─ Pass grapheme_errors to WordBadge components         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Phases

### Phase 1: Backend - Grapheme Segmentation ✅ Ready to Start

**Goal**: Create a robust grapheme segmentation system that breaks words into phoneme-producing units.

#### Todos

- [ ] **Create `backend/core/grapheme_segmenter.py`**
  - [ ] Implement `segment_word_to_graphemes(word: str, expected_phonemes: list) -> list[str]`
  - [ ] Handle common digraphs: sh, ch, th, ph, wh, gh, ck, ng
  - [ ] Handle vowel teams: ai, ay, ee, ea, oa, oo, ou, ow, ue, ew, ie, ei
  - [ ] Handle r-controlled vowels: ar, er, ir, or, ur
  - [ ] Handle silent letters: k in "knight", w in "write", gh in "light"
  - [ ] Return list of grapheme strings with positions

- [ ] **Create test suite `backend/tests/grapheme_segmentation/`**
  - [ ] Create test cases for simple words (cat, dog, run)
  - [ ] Create test cases for digraphs (ship, chat, phone)
  - [ ] Create test cases for vowel teams (rain, boat, light)
  - [ ] Create test cases for silent letters (knight, write, lamb)
  - [ ] Create test cases for edge cases (queue, thought, cough)

- [ ] **Implement phoneme-grapheme mapping**
  - [ ] Create `map_graphemes_to_phonemes(graphemes: list[str], phonemes: list[str]) -> dict`
  - [ ] Use existing `grapheme_to_phoneme()` function for expected phonemes
  - [ ] Align graphemes to phonemes using 1:1, 1:0 (silent), or 2:1 (digraph) rules
  - [ ] Return dictionary mapping grapheme index to phoneme index

#### Implementation Details

**File: `backend/core/grapheme_segmenter.py`**

```python
"""
Grapheme segmentation for phoneme-to-grapheme alignment.

This module segments words into phoneme-producing units (graphemes),
handling digraphs, vowel teams, r-controlled vowels, and silent letters.
"""

import re
from typing import List, Dict, Tuple

# Common digraphs and multi-letter graphemes
DIGRAPHS = {
    # Consonant digraphs
    'sh', 'ch', 'th', 'ph', 'wh', 'gh', 'ck', 'ng', 'qu',
    # Vowel teams
    'ai', 'ay', 'ee', 'ea', 'oa', 'oo', 'ou', 'ow', 'ue', 'ew', 'ie', 'ei', 'ey',
    # R-controlled vowels
    'ar', 'er', 'ir', 'or', 'ur',
}

TRIGRAPHS = {
    'igh',  # light, night
    'tch',  # match, catch
    'dge',  # badge, edge
}

# Silent letter patterns (context-dependent)
SILENT_PATTERNS = [
    (r'^k', 'kn'),      # knight, knee
    (r'^w', 'wr'),      # write, wrong
    (r'^p', 'ps'),      # psychology, psalm
    (r'gh$', 'ugh'),    # laugh, tough
    (r'gh$', 'igh'),    # light, night
    (r'b$', 'mb'),      # lamb, climb
    (r'b$', 'bt'),      # doubt, debt
]


def segment_word_to_graphemes(word: str, expected_phonemes: List[str]) -> List[str]:
    """
    Segment a word into grapheme units that correspond to phonemes.
    
    Args:
        word: The word to segment (e.g., "ship")
        expected_phonemes: Expected phoneme sequence (e.g., [/ʃ/, /ɪ/, /p/])
        
    Returns:
        List of grapheme strings (e.g., ["sh", "i", "p"])
        
    Note:
        This is a heuristic approach that uses phoneme count as a guide.
        For 90% of words, this will produce correct segmentation.
    """
    word_lower = word.lower()
    graphemes = []
    i = 0
    
    # Target number of graphemes should roughly match phoneme count
    target_count = len(expected_phonemes)
    
    while i < len(word_lower):
        # Try trigraphs first (3 letters)
        if i + 2 < len(word_lower):
            three = word_lower[i:i+3]
            if three in TRIGRAPHS:
                graphemes.append(three)
                i += 3
                continue
        
        # Try digraphs (2 letters)
        if i + 1 < len(word_lower):
            two = word_lower[i:i+2]
            if two in DIGRAPHS:
                graphemes.append(two)
                i += 2
                continue
        
        # Check for silent letters
        # (Only mark as silent if we're over the target phoneme count)
        if len(graphemes) >= target_count:
            # Check if current letter might be silent
            remaining = word_lower[i:]
            is_silent = False
            for pattern, context in SILENT_PATTERNS:
                if re.search(pattern, remaining) and remaining.startswith(context):
                    is_silent = True
                    break
            
            if is_silent:
                # Mark as silent by combining with previous grapheme
                if graphemes:
                    graphemes[-1] += word_lower[i]
                else:
                    graphemes.append(word_lower[i])
                i += 1
                continue
        
        # Default: single letter grapheme
        graphemes.append(word_lower[i])
        i += 1
    
    return graphemes


def map_graphemes_to_phonemes(
    word: str,
    graphemes: List[str],
    expected_phonemes: List[str]
) -> Dict[int, int]:
    """
    Map grapheme positions to phoneme positions.
    
    Args:
        word: Original word
        graphemes: List of grapheme units
        expected_phonemes: List of expected phonemes
        
    Returns:
        Dictionary mapping grapheme_index -> phoneme_index
        Silent graphemes map to -1
        
    Example:
        word = "ship"
        graphemes = ["sh", "i", "p"]
        phonemes = [/ʃ/, /ɪ/, /p/]
        Returns: {0: 0, 1: 1, 2: 2}
    """
    mapping = {}
    
    # Simple 1:1 alignment for Phase 1
    # Assumes graphemes and phonemes align linearly
    for g_idx in range(len(graphemes)):
        if g_idx < len(expected_phonemes):
            mapping[g_idx] = g_idx
        else:
            # Extra graphemes (silent letters) map to -1
            mapping[g_idx] = -1
    
    return mapping


def map_phoneme_errors_to_graphemes(
    word: str,
    graphemes: List[str],
    expected_phonemes: List[str],
    detected_phonemes: List[str],
    missed_phonemes: List[str],
    added_phonemes: List[str],
    substituted_phonemes: List[Tuple[str, str]]  # (expected, detected) pairs
) -> Dict[int, Dict]:
    """
    Map phoneme errors back to grapheme positions.
    
    Args:
        word: Original word
        graphemes: Segmented graphemes
        expected_phonemes: Expected phoneme sequence
        detected_phonemes: Detected phoneme sequence
        missed_phonemes: Phonemes that were missed
        added_phonemes: Phonemes that were added
        substituted_phonemes: Phonemes that were substituted (expected, detected) pairs
        
    Returns:
        Dictionary mapping grapheme_index -> error_info
        
    Example:
        word = "cat"
        graphemes = ["c", "a", "t"]
        expected = [/k/, /æ/, /t/]
        detected = [/æ/, /t/]
        missed = [/k/]
        Returns: {0: {"type": "missed", "phoneme": /k/, "grapheme": "c"}}
    """
    grapheme_errors = {}
    
    # Map graphemes to phonemes
    g2p_map = map_graphemes_to_phonemes(word, graphemes, expected_phonemes)
    
    # Create phoneme-to-grapheme reverse map
    p2g_map = {p_idx: g_idx for g_idx, p_idx in g2p_map.items() if p_idx != -1}
    
    # Map missed phonemes to graphemes
    for phoneme in missed_phonemes:
        if phoneme in expected_phonemes:
            p_idx = expected_phonemes.index(phoneme)
            if p_idx in p2g_map:
                g_idx = p2g_map[p_idx]
                grapheme_errors[g_idx] = {
                    "type": "missed",
                    "phoneme": phoneme,
                    "grapheme": graphemes[g_idx]
                }
    
    # Map substituted phonemes to graphemes
    for expected, detected in substituted_phonemes:
        if expected in expected_phonemes:
            p_idx = expected_phonemes.index(expected)
            if p_idx in p2g_map:
                g_idx = p2g_map[p_idx]
                grapheme_errors[g_idx] = {
                    "type": "substituted",
                    "expected_phoneme": expected,
                    "detected_phoneme": detected,
                    "grapheme": graphemes[g_idx]
                }
    
    # Added phonemes don't map to existing graphemes
    # They are "phantom" graphemes that will be shown separately
    # We'll add them as position -1 (special marker for additions)
    for i, phoneme in enumerate(added_phonemes):
        grapheme_errors[-1 - i] = {
            "type": "added",
            "phoneme": phoneme,
            "grapheme": None  # No grapheme, it's an addition
        }
    
    return grapheme_errors
```

#### QA Checklist

- [ ] Grapheme segmentation handles simple words correctly
- [ ] Digraphs (sh, ch, th, etc.) recognized and kept together
- [ ] Vowel teams (ai, ee, oa, etc.) recognized and kept together
- [ ] Silent letters handled appropriately
- [ ] Phoneme-grapheme mapping creates correct 1:1 alignment
- [ ] Error mapping correctly identifies grapheme positions
- [ ] All test cases pass
- [ ] Code follows existing style conventions
- [ ] Docstrings are clear and complete

---

### Phase 2: Backend - Integration with process_audio.py ✅ Ready to Start

**Goal**: Integrate grapheme segmentation with existing phoneme analysis pipeline.

#### Todos

- [ ] **Enhance `backend/core/process_audio.py`**
  - [ ] Import grapheme_segmenter module
  - [ ] Call `segment_word_to_graphemes()` in `_process_word_alignment()`
  - [ ] Call `map_phoneme_errors_to_graphemes()` after error detection
  - [ ] Add `grapheme_errors` field to result dictionary
  - [ ] Add `graphemes` field to result dictionary (for frontend display)

- [ ] **Update result JSON structure**
  - [ ] Add `graphemes` array to each word result
  - [ ] Add `grapheme_errors` dictionary to each word result
  - [ ] Ensure backward compatibility with existing API consumers

- [ ] **Test integration**
  - [ ] Run existing test suite to ensure no regressions
  - [ ] Add new test cases for grapheme error mapping
  - [ ] Verify JSON output structure is correct

#### Implementation Details

**File: `backend/core/process_audio.py` (modifications)**

```python
# Add import
from .grapheme_segmenter import (
    segment_word_to_graphemes,
    map_phoneme_errors_to_graphemes
)

# In _process_word_alignment function, after error detection:
def _process_word_alignment(...):
    # ... existing code ...
    
    for op, gt_word_op, pred_word_op in word_ops:
        if op in ('match', 'substitution'):
            # ... existing code to get gt_word, pred_word, phonemes, etc. ...
            
            # NEW: Segment word into graphemes
            graphemes = segment_word_to_graphemes(gt_word, gt_phonemes)
            
            # Get phoneme-level alignment (existing code)
            phoneme_ops = align_sequences(gt_phonemes, pred_phonemes)
            missed, added, substituted = [], [], []
            for pop, gph, pph in phoneme_ops:
                if pop == 'deletion':
                    missed.append(gph)
                elif pop == 'insertion':
                    added.append(pph)
                elif pop == 'substitution':
                    substituted.append((gph, pph))
            
            # NEW: Map errors to graphemes
            grapheme_errors = map_phoneme_errors_to_graphemes(
                word=gt_word,
                graphemes=graphemes,
                expected_phonemes=gt_phonemes,
                detected_phonemes=pred_phonemes,
                missed_phonemes=missed,
                added_phonemes=added,
                substituted_phonemes=substituted
            )
            
            per = (len(missed) + len(added) + len(substituted)) / max(len(gt_phonemes), 1)
            results.append({
                "type": op,
                "predicted_word": pred_word,
                "ground_truth_word": gt_word,
                "phonemes": pred_phonemes,
                "ground_truth_phonemes": gt_phonemes,
                "per": round(per, 4),
                "missed": missed,
                "added": added,
                "substituted": substituted,
                "total_phonemes": len(gt_phonemes),
                "total_errors": len(missed) + len(added) + len(substituted),
                # NEW FIELDS:
                "graphemes": graphemes,
                "grapheme_errors": grapheme_errors,
            })
    
    # ... rest of function ...
```

**Expected JSON Output**:

```json
{
  "type": "match",
  "predicted_word": "brown",
  "ground_truth_word": "brown",
  "phonemes": ["r", "aʊ", "n", "d"],
  "ground_truth_phonemes": ["b", "r", "aʊ", "n"],
  "per": 0.4,
  "missed": ["b"],
  "added": ["d"],
  "substituted": [],
  "total_phonemes": 4,
  "total_errors": 2,
  "graphemes": ["b", "r", "ow", "n"],
  "grapheme_errors": {
    "0": {
      "type": "missed",
      "phoneme": "b",
      "grapheme": "b"
    },
    "-1": {
      "type": "added",
      "phoneme": "d",
      "grapheme": null
    }
  }
}
```

#### QA Checklist

- [ ] `graphemes` field added to JSON response
- [ ] `grapheme_errors` field added to JSON response
- [ ] Existing functionality not broken (all tests pass)
- [ ] New fields populated correctly for all test cases
- [ ] Backward compatibility maintained
- [ ] JSON structure documented

---

### Phase 3: Frontend - Letter-Level Visualization ✅ Ready to Start

**Goal**: Enhance WordBadge component to display letter-level errors with visual highlighting.

#### Todos

- [ ] **Update `frontend/src/components/WordBadge.tsx`**
  - [ ] Add `graphemeErrors` prop to WordBadgeProps interface
  - [ ] Add `graphemes` prop to WordBadgeProps interface
  - [ ] Create `renderLetterHighlights()` function
  - [ ] Highlight letters based on error type:
    - Red background: missed phonemes
    - Orange background: substituted phonemes
    - Green dashed border: added phonemes (phantom letters after word)
  - [ ] Add tooltip/hover text explaining the error
  - [ ] Update animation to highlight errors sequentially

- [ ] **Update `frontend/src/components/WordBadgeRow.tsx`**
  - [ ] Extract `grapheme_errors` from analysisData
  - [ ] Extract `graphemes` from analysisData
  - [ ] Pass to WordBadge components as props

- [ ] **Create new component `frontend/src/components/LetterBadge.tsx`**
  - [ ] Similar to current grapheme chunks but for individual letters
  - [ ] Support error highlighting
  - [ ] Support hover tooltips
  - [ ] Support click-to-speak individual letters

- [ ] **Update styles**
  - [ ] Define color scheme for error types
  - [ ] Add smooth transitions for error highlights
  - [ ] Ensure accessibility (color contrast)

#### Implementation Details

**File: `frontend/src/components/WordBadge.tsx` (enhanced)**

```typescript
interface GraphemeError {
  type: "missed" | "substituted" | "added";
  phoneme?: string;
  expected_phoneme?: string;
  detected_phoneme?: string;
  grapheme?: string | null;
}

interface WordBadgeProps {
  word: string;
  idx: number;
  showHighlighted: boolean;
  analysisPer?: number;
  isInsertion?: boolean;
  isDeletion?: boolean;
  // NEW PROPS:
  graphemes?: string[];
  graphemeErrors?: Record<number, GraphemeError>;
}

export const WordBadge = ({
  word,
  idx,
  showHighlighted,
  analysisPer,
  isInsertion = false,
  isDeletion = false,
  graphemes,
  graphemeErrors,
}: WordBadgeProps) => {
  // ... existing state and logic ...
  
  const [showLetterLevel, setShowLetterLevel] = useState(false);
  
  /**
   * Render letter-level highlights for phoneme errors
   */
  const renderLetterHighlights = () => {
    if (!graphemes || !graphemeErrors || !showLetterLevel) {
      return renderWholeWord();
    }
    
    return (
      <span className="inline-flex gap-0">
        {graphemes.map((grapheme, g_idx) => {
          const error = graphemeErrors[g_idx];
          
          let bgColor = "transparent";
          let borderStyle = "";
          let tooltip = "";
          
          if (error) {
            if (error.type === "missed") {
              bgColor = "rgba(248, 113, 113, 0.3)"; // light red
              tooltip = `You missed the "${grapheme}" sound (/${error.phoneme}/)`;
            } else if (error.type === "substituted") {
              bgColor = "rgba(251, 146, 60, 0.3)"; // light orange
              tooltip = `You said /${error.detected_phoneme}/ instead of /${error.expected_phoneme}/`;
            }
          }
          
          return (
            <motion.span
              key={g_idx}
              initial={{ scale: 1 }}
              animate={
                showHighlighted && error
                  ? {
                      scale: [1, 1.2, 1],
                      backgroundColor: [
                        "transparent",
                        bgColor,
                        bgColor,
                      ],
                      transition: {
                        delay: g_idx * 0.1,
                        duration: 0.6,
                      },
                    }
                  : {}
              }
              style={{
                backgroundColor: showHighlighted && error ? bgColor : "transparent",
                padding: "2px 1px",
                borderRadius: "4px",
                ...borderStyle,
              }}
              title={tooltip}
              className="cursor-pointer hover:scale-110 transition-transform"
              onClick={() => speak(grapheme, { rate: 0.5 })}
            >
              {grapheme}
            </motion.span>
          );
        })}
        
        {/* Render added phonemes as phantom letters */}
        {Object.entries(graphemeErrors).map(([key, error]) => {
          if (error.type === "added") {
            return (
              <motion.span
                key={`added-${key}`}
                initial={{ opacity: 0, scale: 0.5 }}
                animate={{ opacity: 0.5, scale: 1 }}
                style={{
                  color: "rgb(134, 239, 172)",
                  border: "2px dashed rgb(134, 239, 172)",
                  padding: "2px 4px",
                  borderRadius: "4px",
                  fontStyle: "italic",
                }}
                title={`You added the /${error.phoneme}/ sound`}
              >
                ?
              </motion.span>
            );
          }
          return null;
        })}
      </span>
    );
  };
  
  const renderWholeWord = () => {
    return (
      <motion.span
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        key="whole-word"
        className="text-2xl md:text-4xl font-medium px-1 md:px-3"
      >
        {word}
      </motion.span>
    );
  };
  
  return (
    <motion.div
      // ... existing animation props ...
      className="inline-block group bg-white dark:bg-zinc-900 rounded-xl"
    >
      {/* Toggle Button for Letter-Level View */}
      <button
        type="button"
        aria-label="Toggle letter-level error view"
        onClick={(e) => {
          e.stopPropagation();
          setShowLetterLevel((s) => !s);
        }}
        className="absolute top-[-8px] left-[-8px] z-10 p-1.5 rounded-full bg-white/80 hover:bg-muted shadow transition-opacity opacity-0 group-hover:opacity-100"
        tabIndex={0}
      >
        {showLetterLevel ? (
          <Text className="h-5 w-5" />
        ) : (
          <Target className="h-5 w-5" />
        )}
      </button>
      
      {/* Existing grapheme toggle button on the right */}
      <button
        type="button"
        aria-label="Toggle grapheme mode"
        onClick={(e) => {
          e.stopPropagation();
          setIsGraphemes((s) => !s);
        }}
        className="absolute top-[-8px] right-[-8px] z-10 p-1.5 rounded-full bg-white/80 hover:bg-muted shadow transition-opacity opacity-0 group-hover:opacity-100"
        tabIndex={0}
      >
        {isGraphemes ? (
          <Text className="h-5 w-5" />
        ) : (
          <Columns className="h-5 w-5" />
        )}
      </button>
      
      <Badge
        variant="outline"
        className={`${textClass} ${baseBgClass} cursor-pointer transition-colors hover:bg-muted relative rounded-xl ${
          isInsertion ? "italic text-green-600 dark:text-green-400" : ""
        } ${
          isDeletion
            ? "line-through text-red-400 dark:text-red-400 opacity-60"
            : ""
        }`}
        style={{ background: "transparent" }}
        onClick={() => {
          if (showLetterLevel) {
            // Don't speak on click in letter mode, let individual letters handle it
            return;
          }
          if (!isGraphemes) {
            speak(word, { rate: 1 });
          } else {
            speak(word, { rate: 0.3 });
          }
        }}
      >
        {isGraphemes ? (
          // Existing grapheme chunking view
          renderGraphemeChunks()
        ) : showLetterLevel ? (
          // NEW: Letter-level error view
          renderLetterHighlights()
        ) : (
          // Whole word view
          renderWholeWord()
        )}
      </Badge>
    </motion.div>
  );
};
```

**File: `frontend/src/components/WordBadgeRow.tsx` (modifications)**

```typescript
const WordBadgeRow = ({
  showHighlightedWords,
  analysisData,
  wordArray,
}: WordBadgeRowProps) => {
  // ... existing code ...
  
  // In the map where WordBadge is rendered:
  return (
    <WordBadge
      word={item.word}
      idx={item.originalIdx >= 0 ? item.originalIdx : displayIdx}
      showHighlighted={
        showHighlightedWords && !item.isInsertion && !item.isDeletion
      }
      analysisPer={item.per ?? undefined}
      isInsertion={item.isInsertion}
      isDeletion={item.isDeletion}
      // NEW: Pass grapheme data
      graphemes={
        item.analysisIdx !== null
          ? analysisData?.pronunciation_dataframe.graphemes?.[item.analysisIdx]
          : undefined
      }
      graphemeErrors={
        item.analysisIdx !== null
          ? analysisData?.pronunciation_dataframe.grapheme_errors?.[item.analysisIdx]
          : undefined
      }
      key={`${item.word}-${item.analysisIdx ?? displayIdx}`}
    />
  );
};
```

#### QA Checklist

- [ ] Letter-level highlighting displays correctly
- [ ] Error colors are distinct and accessible
- [ ] Tooltips show helpful error explanations
- [ ] Toggle button switches between word/letter/grapheme views
- [ ] Animations are smooth and not distracting
- [ ] Individual letters are clickable for pronunciation
- [ ] Phantom letters display for added phonemes
- [ ] Works on mobile devices
- [ ] Accessibility features maintained

---

### Phase 4: Testing & Quality Assurance ✅ Ready to Start

**Goal**: Comprehensive testing of the entire phoneme-to-grapheme feedback system.

#### Todos

- [ ] **Backend Testing**
  - [ ] Test grapheme segmentation on 100+ common words
  - [ ] Test error mapping accuracy
  - [ ] Test edge cases (silent letters, digraphs, etc.)
  - [ ] Measure performance impact
  - [ ] Run full backend test suite

- [ ] **Frontend Testing**
  - [ ] Test letter highlighting on various words
  - [ ] Test with different error types
  - [ ] Test animations and interactions
  - [ ] Test on different screen sizes
  - [ ] Test accessibility features
  - [ ] Run frontend test suite

- [ ] **Integration Testing**
  - [ ] End-to-end test: record audio → see letter errors
  - [ ] Test with real student recordings
  - [ ] Test with edge cases (mumbled audio, background noise)
  - [ ] Test error explanations are helpful

- [ ] **User Testing** (if possible)
  - [ ] Show to children and observe understanding
  - [ ] Gather feedback on error display
  - [ ] Iterate based on feedback

#### Test Cases

**Backend Test Cases** (`backend/tests/grapheme_segmentation/test_cases.json`):

```json
[
  {
    "name": "simple_word",
    "word": "cat",
    "expected_phonemes": ["k", "æ", "t"],
    "detected_phonemes": ["æ", "t"],
    "missed": ["k"],
    "expected_graphemes": ["c", "a", "t"],
    "expected_errors": {
      "0": {"type": "missed", "phoneme": "k", "grapheme": "c"}
    }
  },
  {
    "name": "digraph",
    "word": "ship",
    "expected_phonemes": ["ʃ", "ɪ", "p"],
    "detected_phonemes": ["ɪ", "p"],
    "missed": ["ʃ"],
    "expected_graphemes": ["sh", "i", "p"],
    "expected_errors": {
      "0": {"type": "missed", "phoneme": "ʃ", "grapheme": "sh"}
    }
  },
  {
    "name": "vowel_team",
    "word": "rain",
    "expected_phonemes": ["r", "eɪ", "n"],
    "detected_phonemes": ["r", "ɛ", "n"],
    "substituted": [["eɪ", "ɛ"]],
    "expected_graphemes": ["r", "ai", "n"],
    "expected_errors": {
      "1": {
        "type": "substituted",
        "expected_phoneme": "eɪ",
        "detected_phoneme": "ɛ",
        "grapheme": "ai"
      }
    }
  },
  {
    "name": "silent_letter",
    "word": "knight",
    "expected_phonemes": ["n", "aɪ", "t"],
    "detected_phonemes": ["aɪ", "t"],
    "missed": ["n"],
    "expected_graphemes": ["k", "n", "igh", "t"],
    "expected_errors": {
      "1": {"type": "missed", "phoneme": "n", "grapheme": "n"}
    }
  },
  {
    "name": "added_phoneme",
    "word": "dog",
    "expected_phonemes": ["d", "ɔ", "g"],
    "detected_phonemes": ["d", "ɔ", "g", "z"],
    "added": ["z"],
    "expected_graphemes": ["d", "o", "g"],
    "expected_errors": {
      "-1": {"type": "added", "phoneme": "z", "grapheme": null}
    }
  }
]
```

#### Performance Benchmarks

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Grapheme segmentation time | < 5ms per word | TBD | ⏸️ |
| Error mapping time | < 10ms per word | TBD | ⏸️ |
| API response time increase | < 50ms | TBD | ⏸️ |
| Frontend render time | < 100ms | TBD | ⏸️ |
| Memory usage increase | < 10MB | TBD | ⏸️ |

#### QA Checklist

- [ ] All backend tests pass
- [ ] All frontend tests pass
- [ ] Integration tests pass
- [ ] Performance targets met
- [ ] No regressions in existing functionality
- [ ] Error messages are clear and helpful
- [ ] Visual design is polished
- [ ] Accessibility requirements met
- [ ] Documentation updated
- [ ] Code reviewed and approved

---

### Phase 5: Advanced Features (Optional) ⏸️ Future Enhancement

**Goal**: Add ML-based phoneme-to-grapheme conversion for novel words and improved accuracy.

This phase is intentionally deferred as it adds complexity beyond the 80/20 rule. Implement only if:
1. Phases 1-4 reveal significant accuracy issues
2. User testing shows confusion with dictionary-based approach
3. There's demand for handling novel/misspelled words

#### Potential Enhancements

- [ ] Train sequence-to-sequence model for P2G conversion
- [ ] Integrate Montreal Forced Aligner for audio-based alignment
- [ ] Add confidence scores for grapheme error mapping
- [ ] Support multiple language orthographies (Spanish, French)
- [ ] Add pronunciation variant handling (British vs American English)

---

## Data Structures

### Backend JSON Response Structure

```typescript
interface WordAnalysis {
  type: "match" | "substitution" | "insertion" | "deletion";
  predicted_word: string | null;
  ground_truth_word: string | null;
  phonemes: string[] | null;
  ground_truth_phonemes: string[] | null;
  per: number | null;
  missed: string[];
  added: string[];
  substituted: [string, string][];  // [expected, detected] pairs
  total_phonemes: number;
  total_errors: number;
  
  // NEW FIELDS (Phase 2):
  graphemes: string[];  // ["c", "a", "t"] or ["sh", "i", "p"]
  grapheme_errors: {
    [grapheme_index: number]: GraphemeError;
  };
}

interface GraphemeError {
  type: "missed" | "substituted" | "added";
  phoneme?: string;  // For missed/added
  expected_phoneme?: string;  // For substituted
  detected_phoneme?: string;  // For substituted
  grapheme: string | null;  // null for added phonemes
}
```

### Frontend TypeScript Interfaces

```typescript
// In frontend/src/types/analysis.ts

export interface GraphemeError {
  type: "missed" | "substituted" | "added";
  phoneme?: string;
  expected_phoneme?: string;
  detected_phoneme?: string;
  grapheme?: string | null;
}

export interface WordBadgeProps {
  word: string;
  idx: number;
  showHighlighted: boolean;
  analysisPer?: number;
  isInsertion?: boolean;
  isDeletion?: boolean;
  graphemes?: string[];
  graphemeErrors?: Record<number, GraphemeError>;
}
```

---

## Quality Assurance

### Comprehensive QA Checklist

#### Backend

- [ ] Grapheme segmentation accuracy > 95% on test cases
- [ ] Error mapping accuracy > 95% on test cases
- [ ] No performance degradation (< 50ms added latency)
- [ ] All existing tests still pass
- [ ] New tests added for new functionality
- [ ] Code follows Python best practices
- [ ] Type hints added for all functions
- [ ] Docstrings complete and accurate

#### Frontend

- [ ] Letter highlighting displays correctly
- [ ] Error colors are accessible (WCAG AA contrast)
- [ ] Tooltips are informative
- [ ] Animations are smooth
- [ ] Mobile display works correctly
- [ ] Touch interactions work on mobile
- [ ] Keyboard navigation works
- [ ] Screen readers announce errors correctly
- [ ] No visual regressions
- [ ] TypeScript types are correct

#### Integration

- [ ] End-to-end flow works: audio → analysis → letter errors
- [ ] API contract matches between backend and frontend
- [ ] Error cases handled gracefully
- [ ] Loading states display correctly
- [ ] No console errors or warnings
- [ ] Performance is acceptable (< 2 second total time)

#### User Experience

- [ ] Error feedback is clear and helpful
- [ ] Visual design is polished
- [ ] Interactions are intuitive
- [ ] Children can understand the feedback
- [ ] Teachers find it useful
- [ ] No cognitive overload (not too much info at once)

---

## References

### Related Files

**Backend:**
- `backend/core/grapheme_to_phoneme.py` - Existing G2P conversion
- `backend/core/process_audio.py` - Phoneme analysis pipeline
- `backend/core/phoneme_assistant.py` - Main assistant class
- `backend/tests/system/test_case_02/result.json` - Example response structure

**Frontend:**
- `frontend/src/components/WordBadge.tsx` - Word display component
- `frontend/src/components/WordBadgeRow.tsx` - Word row container
- `frontend/src/components/practice/FeedbackDisplay.tsx` - Feedback display

### Research Papers & Resources

1. **Grapheme-to-Phoneme Conversion**
   - "Pronunciation Modeling for Improved Spelling" (Toutanova & Moore, 2002)
   - CMU Pronouncing Dictionary: http://www.speech.cs.cmu.edu/cgi-bin/cmudict

2. **Forced Alignment**
   - Montreal Forced Aligner: https://montreal-forced-aligner.readthedocs.io/
   - "Forced Alignment with Non-Native Speech" (Yuan & Liberman, 2008)

3. **Phoneme-to-Grapheme Models**
   - "Improved Letter-to-Phoneme Conversion using Sequence-to-Sequence Models" (Rao et al., 2015)
   - g2p-seq2seq: https://github.com/cmusphinx/g2p-seq2seq

4. **Educational Research**
   - "The Importance of Phoneme Awareness in Learning to Read" (Adams, 1990)
   - "Visual Feedback for Phoneme Learning" (Thomson & Richardson, 1995)

### External Libraries

- **eng_to_ipa** (Python): Grapheme-to-phoneme conversion
  - Already in use: `backend/requirements.txt`
  - Docs: https://pypi.org/project/eng-to-ipa/

- **epitran** (Python): Grapheme-to-phoneme for multiple languages
  - Alternative if eng_to_ipa insufficient
  - Docs: https://github.com/dmort27/epitran

- **Montreal Forced Aligner** (External tool)
  - Professional-grade phoneme alignment
  - Only if Phase 4 needed
  - Docs: https://montreal-forced-aligner.readthedocs.io/

### Implementation Guides in This Repository

- `implementation_guides/ERROR_VIEWER_PRACTICE_PAGE.md` - Error handling patterns
- `implementation_guides/client-side-phoneme-extraction.md` - Client-side ML
- `implementation_guides/TESTING_SUITE_IMPLEMENTATION_GUIDE.md` - Testing patterns

---

## Success Metrics

After full implementation (Phases 1-4), success will be measured by:

1. **Technical Metrics**
   - ✅ Grapheme segmentation accuracy > 95%
   - ✅ Error mapping accuracy > 95%
   - ✅ API latency increase < 50ms
   - ✅ Zero regressions in existing features

2. **User Experience Metrics**
   - ✅ Children understand letter-level feedback
   - ✅ Teachers report improved learning outcomes
   - ✅ User satisfaction increased (surveys)
   - ✅ Time-to-understanding decreased

3. **Educational Metrics**
   - ✅ Students improve pronunciation faster
   - ✅ Students connect letters to sounds better
   - ✅ Reduced confusion about errors
   - ✅ Increased engagement with feedback

---

## Risks & Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Grapheme segmentation inaccurate | High | Medium | Extensive testing, fallback to whole-word display |
| Performance degradation | Medium | Low | Optimize algorithms, cache results, profile code |
| Complex words not handled | Medium | High | Start with simple words, add complexity gradually |
| User confusion with letter display | High | Medium | User testing, iterate on design, add help tooltips |
| Silent letters mishandled | Low | Medium | Comprehensive silent letter pattern database |
| Backend/frontend mismatch | High | Low | Strict API contract, integration tests |

---

## Timeline Estimate

| Phase | Estimated Time | Dependencies |
|-------|----------------|--------------|
| Phase 1: Backend Segmentation | 3-5 days | None |
| Phase 2: Backend Integration | 2-3 days | Phase 1 |
| Phase 3: Frontend Visualization | 4-6 days | Phase 2 |
| Phase 4: Testing & QA | 3-4 days | Phase 3 |
| **Total (Phases 1-4)** | **12-18 days** | - |
| Phase 5: ML Enhancement (Optional) | 10-15 days | Phase 4 complete |

**Note**: Times assume 1 developer working full-time. Adjust for team size and part-time work.

---

## Future Enhancements (Out of Scope)

Following the 80/20 rule, these are intentionally excluded but could be considered later:

- Sequence-to-sequence ML model for P2G conversion
- Support for multiple languages (Spanish, French, etc.)
- Audio-based forced alignment (Montreal Forced Aligner)
- Confidence scores for error mapping
- Multiple pronunciation variants (regional accents)
- Custom pronunciation dictionaries per user
- Real-time error highlighting during recording
- Animated pronunciation guides showing mouth movements
- Gamification of letter-level practice

---

## Notes

- **Start Simple**: Phase 1-3 will handle 90%+ of use cases
- **Iterate Based on Data**: Only add Phase 4/5 if testing shows need
- **User Testing Critical**: Children's understanding is the key metric
- **Accessibility First**: Ensure all error displays are accessible
- **Performance Matters**: Keep response times fast (< 2 seconds total)
- **Documentation**: Update user-facing docs with new features

---

**End of Implementation Guide**
