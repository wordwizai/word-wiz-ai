# Prompt System Overhaul - Quick Reference

**Full Guide:** `PROMPT_SYSTEM_OVERHAUL.md`

## 🎯 Goal

Transform the prompts system from static files to a dynamic, modular, pedagogically-optimized feedback engine.

## 🔑 Key Changes

| Aspect | Before | After |
|--------|--------|-------|
| Prompts | Static .txt files (~200 lines each) | Dynamic sections assembled per context |
| Analysis | GPT decides everything | Code pre-analyzes → GPT executes |
| Focus | All phoneme errors equally | Ground truth only (missed/substituted) |
| Feedback | "You had trouble with X" | "The 'qu' in 'quick' makes a 'kw' sound" |
| Sentences | Fixed complexity | Adaptive based on PER (0.0-1.0) |
| Praise | Sometimes inconsistent | Only when PER ≤ 0.2 AND no consistent errors |

## 📋 7 Implementation Phases

### Phase 1: Core Infrastructure (6-8h)
- Create `core/prompt_builder.py`
- Create `core/prompt_sections/` directory structure
- Split existing prompts into sections

**Output:** PromptBuilder system that loads and assembles sections

### Phase 2: Analysis Logic (8-10h)
- Create `core/analysis/feedback_analyzer.py`
- Create `core/analysis/sentence_generator.py`
- Implement pre-analysis logic

**Output:** Code that determines feedback strategy before GPT

### Phase 3: Grapheme-Phoneme Mapping (6-8h)
- Enhance `core/grapheme_to_phoneme.py`
- Add `GraphemePhonemeMapper` class
- Create grapheme pattern database

**Output:** System that maps sounds to spelling patterns

### Phase 4: Prompt Content (8-10h)
- Write content for all prompt sections
- Create mode-specific sections
- Update SSML sections

**Output:** Complete library of prompt sections

### Phase 5: Mode Integration (6-8h)
- Update `core/modes/base_mode.py`
- Update all mode implementations
- Test with sample audio

**Output:** All modes using new system

### Phase 6: User Input Enhancement (4-6h)
- Add `feedback_instructions` to user input
- Add `sentence_requirements` to user input
- Update all modes

**Output:** GPT receives specific directives, not just data

### Phase 7: Testing & Validation (6-8h)
- Unit tests for all new modules
- Integration tests for all modes
- System tests for scenarios
- GPT output validation

**Output:** Fully tested, production-ready system

## 🏗️ New Architecture

```
User Audio
    ↓
[Existing Analysis Pipeline]
    ↓
pronunciation_data, problem_summary, per_summary
    ↓
[NEW] FeedbackAnalyzer.analyze_for_feedback()
    ↓
FeedbackStrategy {
  should_praise: bool
  focus_phoneme: str (IPA)
  focus_grapheme: str (letters)
  error_words: list[str]
}
    ↓
[NEW] SentenceGenerator.calculate_sentence_params()
    ↓
SentenceParams {
  target_length: int
  complexity: str
  min_focus_instances: int
}
    ↓
[NEW] PromptBuilder.build_prompt()
    ↓
Dynamic Prompt + Specific Instructions
    ↓
GPT-4 (with reduced decision-making)
    ↓
Feedback + Practice Sentence
```

## 📦 New Modules

```
backend/core/
├── prompt_builder.py                # Phase 1
├── prompt_sections/                 # Phase 1 & 4
│   ├── base/
│   ├── feedback/
│   ├── sentence_generation/
│   ├── modes/
│   └── ssml/
├── analysis/                        # Phase 2
│   ├── feedback_analyzer.py
│   └── sentence_generator.py
└── grapheme_to_phoneme.py (enhanced) # Phase 3
```

## 🎓 Key Concepts

### Ground Truth Errors Only
**Before:** Count all phoneme differences (including additions)  
**After:** Only count phonemes from expected output that were missed/substituted

**Why:** Additions are artifacts, not pronunciation errors

### Grapheme-Phoneme Connection
**Before:** "You had trouble with the 'w' sound"  
**After:** "The 'qu' in 'quick' makes a 'kw' sound"

**Why:** Connects spelling to sound (builds literacy, not just pronunciation)

### Adaptive Sentence Difficulty

| PER Range | Length | Complexity | Example |
|-----------|--------|------------|---------|
| 0.0-0.1 | 20-25 words | Complex | "Although the weather was cold..." |
| 0.1-0.3 | 15-20 words | Moderate | "The quick brown fox jumped..." |
| 0.3-0.5 | 10-15 words | Simple | "The cat sat on the mat." |
| 0.5+ | 8-12 words | Very Simple | "I see a cat." |

### Smart Praise Criteria

```python
should_praise = (per <= 0.2) AND (no consistent errors)
```

**Consistent Error:** Same phoneme substituted in 2+ words

**Example:**
- User says "fink" (instead of "think") AND "frough" (instead of "through")
- Both substitute 'θ' → 'f'
- Even if PER = 0.15, this is NOT praise-worthy (consistent error)

## 🧪 Testing Checklist

- [ ] PromptBuilder loads all sections
- [ ] FeedbackAnalyzer excludes addition errors
- [ ] SentenceGenerator scales with PER
- [ ] GraphemeMapper finds correct graphemes
- [ ] All modes build prompts correctly
- [ ] GPT follows instructions
- [ ] Sentences have required phoneme instances
- [ ] SSML is valid
- [ ] No regressions in existing functionality

## 🚀 Quick Start for Implementation

1. **Read full guide:** `PROMPT_SYSTEM_OVERHAUL.md`
2. **Start with Phase 1:** Build the PromptBuilder
3. **Test each phase:** Don't move forward with failures
4. **Use feature flag:** `USE_NEW_PROMPT_SYSTEM=false` for rollback
5. **Migrate gradually:** One mode at a time

## 📊 Success Metrics

- ✅ Prompts are modular and reusable
- ✅ Code determines feedback strategy (not GPT)
- ✅ Only ground truth errors analyzed
- ✅ Feedback mentions graphemes
- ✅ Sentences adapt to performance
- ✅ Praise is only given when appropriate
- ✅ No performance regression (< 150ms added latency)

## 🔧 Key Files to Modify

| File | Phase | Changes |
|------|-------|---------|
| `core/prompt_builder.py` | 1 | Create new |
| `core/prompt_sections/*` | 1, 4 | Create new |
| `core/analysis/feedback_analyzer.py` | 2 | Create new |
| `core/analysis/sentence_generator.py` | 2 | Create new |
| `core/grapheme_to_phoneme.py` | 3 | Enhance |
| `core/modes/base_mode.py` | 5 | Update |
| `core/modes/unlimited.py` | 5 | Update |
| `core/modes/story.py` | 5 | Update |
| `core/modes/choice_story.py` | 5 | Update |

## 💡 Pro Tips

1. **Template Variables:** Use `{variable}` syntax in sections
2. **Context Passing:** Always validate required context exists
3. **Section Order:** Order matters! Build prompts logically
4. **Test Incrementally:** Test after each phase, not at the end
5. **Keep Old System:** Don't delete old prompts until fully validated
6. **Log Everything:** Log prompt assembly for debugging
7. **GPT Validation:** Validate GPT output against requirements

## 📞 Questions?

See full implementation guide: `PROMPT_SYSTEM_OVERHAUL.md`
- Section-by-section specifications
- Detailed code examples
- Test scenarios
- Migration strategy
- Rollback plan
- Troubleshooting guide

---

**Total Effort:** 44-62 hours across 7 phases  
**Timeline:** 3-4 weeks recommended  
**Risk Level:** Medium (gradual migration recommended)  
**Impact:** High (significantly better feedback quality)
