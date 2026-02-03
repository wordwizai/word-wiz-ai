# Phoneme-to-Grapheme Feedback - Quick Start Guide

## 📖 Overview

This document provides a quick-start guide for implementing letter-based phoneme feedback in Word Wiz AI. For the **complete detailed implementation guide**, see:

👉 **[PHONEME_TO_GRAPHEME_FEEDBACK_GUIDE.md](./PHONEME_TO_GRAPHEME_FEEDBACK_GUIDE.md)**

---

## 🎯 What This Solves

**Current Problem:**
- Users see word-level errors: "brown" is colored orange (medium error)
- They don't know WHICH letters they mispronounced

**Solution:**
- Show letter-level errors: "**b̲**rown" with 'b' highlighted in red
- Tooltip: "You missed the 'b' sound at the beginning"
- Help children connect letters to sounds

---

## 🔑 Key Insight

**We don't need a general-purpose phoneme-to-grapheme converter!**

Since we already know:
- Target word: "cat"
- Expected phonemes: /k/ /æ/ /t/
- Detected phonemes: /æ/ /t/
- Errors: missed /k/

We can use **forced alignment** to map /k/ → letter 'c' → highlight 'c' in red.

---

## 📋 Implementation Phases

### Phase 1: Backend - Grapheme Segmentation (3-5 days)
- Create `backend/core/grapheme_segmenter.py`
- Segment words into phoneme units: "ship" → ["sh", "i", "p"]
- Handle digraphs, vowel teams, silent letters
- Write comprehensive tests

**Key Function:**
```python
def segment_word_to_graphemes(word: str, expected_phonemes: list) -> list[str]:
    # Returns: ["sh", "i", "p"] for "ship"
```

### Phase 2: Backend - Integration (2-3 days)
- Integrate with `backend/core/process_audio.py`
- Add `graphemes` and `grapheme_errors` to JSON response
- Ensure backward compatibility
- Run integration tests

**API Output:**
```json
{
  "ground_truth_word": "brown",
  "graphemes": ["b", "r", "ow", "n"],
  "grapheme_errors": {
    "0": {"type": "missed", "phoneme": "b", "grapheme": "b"}
  }
}
```

### Phase 3: Frontend - Visualization (4-6 days)
- Enhance `frontend/src/components/WordBadge.tsx`
- Add letter-level highlighting with colors:
  - Red: missed phonemes
  - Orange: substituted phonemes
  - Green dashed: added phonemes (phantom)
- Add tooltips explaining errors
- Toggle between word/letter/grapheme views

**Visual Output:**
```
[b̲][r][ow][n]  ← Click toggle to see
 ↑ Red highlight = missed
```

### Phase 4: Testing & QA (3-4 days)
- Test 100+ words for accuracy
- End-to-end integration tests
- User testing with children (if possible)
- Performance profiling
- Documentation updates

**Total Time: 12-18 days** (1 full-time developer)

---

## ✅ Quality Checkpoints

Each phase has detailed QA checklists in the full guide. Key metrics:

- **Accuracy**: > 95% correct grapheme segmentation
- **Performance**: < 50ms added API latency
- **UX**: Children understand the feedback
- **Compatibility**: Zero regressions in existing features

---

## 📊 Current System Analysis

### Data Already Available (Backend)

```python
# From backend/core/process_audio.py
{
  "ground_truth_word": "brown",
  "ground_truth_phonemes": ["b", "r", "aʊ", "n"],
  "phonemes": ["r", "aʊ", "n", "d"],  # detected
  "missed": ["b"],     # ✅ Already tracked!
  "added": ["d"],      # ✅ Already tracked!
  "substituted": [],   # ✅ Already tracked!
  "per": 0.4
}
```

**What's Missing:** Mapping errors back to letters/graphemes

### Frontend Components

```typescript
// frontend/src/components/WordBadge.tsx
// Currently displays whole words with PER color coding
// Needs: letter-level highlighting

// frontend/src/components/WordBadgeRow.tsx
// Passes analysis data to WordBadge
// Needs: pass grapheme errors
```

---

## 🔧 Technical Architecture

```
┌─────────────────────────────────────────┐
│            Backend Pipeline             │
├─────────────────────────────────────────┤
│ 1. Phoneme extraction (existing) ✅     │
│ 2. Word alignment (existing) ✅         │
│ 3. Error detection (existing) ✅        │
│ 4. Grapheme segmentation (NEW) ⬜       │
│ 5. Error→Grapheme mapping (NEW) ⬜      │
└─────────────────────────────────────────┘
                  ↓ JSON
┌─────────────────────────────────────────┐
│              Frontend UI                │
├─────────────────────────────────────────┤
│ 1. Receive grapheme errors ⬜           │
│ 2. Highlight letters by error type ⬜   │
│ 3. Show tooltips ⬜                     │
│ 4. Toggle views (word/letter/grapheme) ⬜│
└─────────────────────────────────────────┘
```

---

## 📚 Example Test Cases

### Test Case 1: Simple Word
```json
{
  "word": "cat",
  "expected_phonemes": ["k", "æ", "t"],
  "detected_phonemes": ["æ", "t"],
  "expected_graphemes": ["c", "a", "t"],
  "expected_errors": {
    "0": {"type": "missed", "phoneme": "k", "grapheme": "c"}
  }
}
```

### Test Case 2: Digraph
```json
{
  "word": "ship",
  "expected_phonemes": ["ʃ", "ɪ", "p"],
  "detected_phonemes": ["ɪ", "p"],
  "expected_graphemes": ["sh", "i", "p"],
  "expected_errors": {
    "0": {"type": "missed", "phoneme": "ʃ", "grapheme": "sh"}
  }
}
```

### Test Case 3: Silent Letter
```json
{
  "word": "knight",
  "expected_phonemes": ["n", "aɪ", "t"],
  "detected_phonemes": ["aɪ", "t"],
  "expected_graphemes": ["k", "n", "igh", "t"],
  "expected_errors": {
    "1": {"type": "missed", "phoneme": "n", "grapheme": "n"}
  }
}
```

More test cases in the full guide!

---

## 🚀 Getting Started

### For the Implementing Agent:

1. **Read the full guide**: [PHONEME_TO_GRAPHEME_FEEDBACK_GUIDE.md](./PHONEME_TO_GRAPHEME_FEEDBACK_GUIDE.md)

2. **Start with Phase 1**: Backend grapheme segmentation
   - Create `backend/core/grapheme_segmenter.py`
   - Follow the implementation template in the guide
   - Write tests first (TDD approach recommended)

3. **Follow the QA checklists**: Each phase has detailed checkpoints

4. **Run existing tests**: Ensure no regressions
   ```bash
   cd backend
   python -m tests.analysis.run_analysis_tests
   ```

5. **Commit frequently**: Use the `report_progress` tool after each phase

---

## 📖 Key Files to Review

Before starting, familiarize yourself with:

**Backend:**
- `backend/core/process_audio.py` - Phoneme analysis pipeline
- `backend/core/grapheme_to_phoneme.py` - Existing G2P (reverse direction)
- `backend/tests/system/test_case_02/result.json` - Example response

**Frontend:**
- `frontend/src/components/WordBadge.tsx` - Word display
- `frontend/src/components/WordBadgeRow.tsx` - Word container

---

## ⚠️ Important Notes

1. **Use existing functions**: Leverage `align_sequences()` from process_audio.py

2. **Start simple**: Phase 1-3 will handle 90%+ of cases. Don't over-engineer.

3. **Test with real data**: Use test cases from `backend/tests/system/`

4. **Maintain backward compatibility**: Add fields, don't remove/change existing ones

5. **Focus on education**: The goal is helping children learn, not perfection

---

## 🎓 Research Background

### Why P2G is Hard (and how we solve it)

**Problem:** One phoneme → many graphemes
- /k/ → c, k, ck, ch, qu, q, cc, cq

**Solution:** We know the target word!
- We don't need to guess which grapheme
- We can align phonemes to the actual letters
- Use forced alignment (dynamic programming)

### Approaches Considered

| Approach | Pros | Cons | Status |
|----------|------|------|--------|
| Dictionary-based | Fast, accurate | Only works for known words | ✅ Using |
| Rule-based | Works on novel words | Complex, exceptions | ✅ Using |
| Forced alignment | Very accurate, uses known word | Only works with known word | ✅ **PRIMARY** |
| ML Model | Learns patterns | Training cost, complexity | ⏸️ Phase 5 (optional) |

---

## 📞 Questions?

If you need clarification on any aspect:

1. Check the full guide: [PHONEME_TO_GRAPHEME_FEEDBACK_GUIDE.md](./PHONEME_TO_GRAPHEME_FEEDBACK_GUIDE.md)
2. Review the research section for background
3. Look at existing test cases in `backend/tests/`
4. Check similar implementation in `ERROR_VIEWER_PRACTICE_PAGE.md` for patterns

---

## 🎯 Success Criteria

Implementation is complete when:

- ✅ Backend segments 95%+ of words correctly
- ✅ API returns grapheme errors in JSON
- ✅ Frontend highlights letters by error type
- ✅ Tooltips explain errors clearly
- ✅ Children understand the feedback
- ✅ All tests pass, no regressions
- ✅ Performance impact < 50ms

---

**Ready to start? Begin with Phase 1 in the full guide!**

👉 **[PHONEME_TO_GRAPHEME_FEEDBACK_GUIDE.md](./PHONEME_TO_GRAPHEME_FEEDBACK_GUIDE.md)**
