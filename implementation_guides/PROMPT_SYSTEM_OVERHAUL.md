# Prompt System Overhaul - Implementation Guide

**Version:** 1.1  
**Created:** December 2024  
**Last Updated:** December 2024  
**Status:** In Progress  
**Estimated Effort:** 38-52 hours (Phases 1-6, testing removed)

---

## Executive Summary

This guide details the complete overhaul of the prompts system to create a modular, performant, and pedagogically-effective feedback system. The new system will:

1. **Generate prompts dynamically** from prebuilt sections
2. **Programmatically determine feedback goals** before GPT involvement
3. **Focus on ground truth phonemes** (missed/substituted, not added)
4. **Intelligently decide praise vs. correction** based on data
5. **Generate adaptive next sentences** based on user performance
6. **Target specific grapheme-to-phoneme patterns** in feedback and sentences

### Key Architectural Changes

- **From:** Static .txt prompt files loaded per mode
- **To:** Dynamic prompt builder assembling sections based on context

- **From:** GPT decides everything (what to focus on, praise/correction, sentence complexity)
- **To:** Code pre-analyzes and directs GPT with specific instructions

- **From:** Generic "you had trouble with X" feedback
- **To:** Grapheme-specific feedback (e.g., "the 'qu' in 'quick' makes a 'kwi' sound")

---

## Problem Statement Analysis

### Current System Issues

1. **Inflexible Prompts**: Each mode has versioned .txt files that are monolithic
2. **GPT Over-Responsibility**: Model decides focus phoneme, praise, sentence complexity
3. **Imprecise Analysis**: Looks at all phoneme errors equally (including additions)
4. **Generic Feedback**: Doesn't connect phonemes to their grapheme representations
5. **Fixed Sentence Generation**: No adaptive difficulty based on overall performance
6. **SSML Always Appended**: Can't customize SSML per mode/context

### Desired Improvements

1. **Modular Prompts**: Mix-and-match sections for different contexts
2. **Code-Driven Logic**: Pre-analyze and instruct GPT specifically
3. **Ground Truth Focus**: Only analyze phonemes from expected output
4. **Grapheme-Phoneme Connection**: Teach spelling patterns, not just sounds
5. **Adaptive Difficulty**: Adjust sentence length/complexity based on PER
6. **Smart Praise**: Only praise when truly warranted (no consistent errors)

---

## Architecture Design

### Phase 1: Prompt Builder System

#### New Module: `core/prompt_builder.py`

```python
class PromptSection:
    """Individual prompt section with context awareness"""
    def __init__(self, name: str, content: str, required_context: list[str] = None):
        self.name = name
        self.content = content
        self.required_context = required_context or []
    
    def render(self, context: dict) -> str:
        """Render section with context variables"""
        # Template rendering with {variable} syntax
        pass

class PromptBuilder:
    """Builds prompts dynamically from sections"""
    def __init__(self):
        self.sections: dict[str, PromptSection] = {}
        self._load_sections()
    
    def _load_sections(self):
        """Load all prompt sections from directory"""
        pass
    
    def build_prompt(
        self,
        sections: list[str],
        context: dict,
        include_ssml: bool = True
    ) -> str:
        """Assemble prompt from named sections"""
        pass
```

#### Directory Structure

```
backend/core/prompt_sections/
├── base/
│   ├── system_role.txt           # Core role definition
│   ├── output_format.txt          # JSON schema requirements
│   └── validation_rules.txt       # Critical verification rules
├── feedback/
│   ├── praise_criteria.txt        # When to praise vs correct
│   ├── phoneme_focus.txt          # How to use recommended_focus
│   ├── grapheme_instruction.txt   # Grapheme-phoneme teaching
│   └── error_description.txt      # How to describe errors
├── sentence_generation/
│   ├── adaptive_difficulty.txt    # PER-based complexity
│   ├── phoneme_density.txt        # Target phoneme frequency
│   ├── grapheme_patterns.txt      # Include target graphemes
│   └── length_guidelines.txt      # Sentence length by PER
├── modes/
│   ├── unlimited_context.txt      # Unlimited mode specifics
│   ├── story_context.txt          # Story mode specifics
│   └── choice_story_context.txt   # Choice story specifics
└── ssml/
    ├── ssml_base.txt              # Core SSML rules
    └── ssml_minimal.txt           # Minimal SSML for short feedback
```

### Phase 2: Enhanced Analysis Logic

#### New Module: `core/analysis/feedback_analyzer.py`

```python
class FeedbackAnalyzer:
    """Pre-analyzes pronunciation data to determine feedback strategy"""
    
    def analyze_for_feedback(
        self,
        pronunciation_data: list[dict],
        problem_summary: dict,
        per_summary: dict
    ) -> FeedbackStrategy:
        """
        Determine feedback strategy before GPT call
        
        Returns:
            FeedbackStrategy with:
                - should_praise: bool
                - focus_phoneme: str (IPA)
                - focus_grapheme: str (letters)
                - error_words: list[str]
                - error_type: 'substituted' | 'missed' | 'mixed'
                - severity: 'low' | 'medium' | 'high'
        """
        pass
    
    def get_ground_truth_errors(
        self,
        pronunciation_data: list[dict]
    ) -> dict:
        """
        Extract only ground truth phoneme errors (missed/substituted)
        Ignores additions (phonemes user said that weren't expected)
        """
        pass
    
    def determine_praise_eligibility(
        self,
        per_summary: dict,
        phoneme_to_error_words: dict
    ) -> tuple[bool, str]:
        """
        Returns (should_praise, reason)
        Only praise if PER <= 0.2 AND no consistent errors
        """
        pass
    
    def find_grapheme_for_phoneme(
        self,
        word: str,
        phoneme: str,
        phonemes_list: list[str]
    ) -> str:
        """
        Find which grapheme (letter combo) produces the phoneme
        Example: word='quick', phoneme='w', phonemes=['k','w','ɪ','k']
        Returns: 'qu' (because 'qu' produces the 'k'+'w' sounds)
        """
        pass
```

#### New Module: `core/analysis/sentence_generator.py`

```python
class SentenceGenerator:
    """Determines next sentence parameters based on performance"""
    
    def calculate_sentence_params(
        self,
        overall_per: float,
        focus_phoneme: str,
        focus_grapheme: str
    ) -> SentenceParams:
        """
        Determine sentence parameters based on performance
        
        Returns:
            SentenceParams with:
                - target_length: int (word count)
                - complexity_level: 'simple' | 'moderate' | 'complex'
                - min_focus_phoneme_instances: int
                - min_focus_grapheme_instances: int
                - other_phoneme_difficulty: 'low' | 'medium'
        """
        pass
    
    def get_difficulty_guidelines(self, overall_per: float) -> dict:
        """
        Map PER to difficulty parameters
        
        PER 0.0-0.1: longer sentences (20-25 words), complex vocab
        PER 0.1-0.3: moderate sentences (15-20 words), grade-level vocab
        PER 0.3-0.5: shorter sentences (10-15 words), simple vocab
        PER 0.5+:    very short (8-12 words), basic vocab
        """
        pass
```

### Phase 3: Grapheme-Phoneme Mapper

#### Enhanced Module: `core/grapheme_to_phoneme.py`

```python
class GraphemePhonemeMapper:
    """Maps between graphemes (letters) and phonemes (sounds)"""
    
    # Common English grapheme-phoneme patterns
    GRAPHEME_PATTERNS = {
        'qu': ['k', 'w'],      # quick -> k+w+ɪ+k
        'ch': ['tʃ'],          # chat -> tʃ+æ+t
        'sh': ['ʃ'],           # ship -> ʃ+ɪ+p
        'th': ['θ', 'ð'],      # think/this
        'ph': ['f'],           # phone -> f+oʊ+n
        'gh': ['f', ''],       # laugh/night
        'ui': ['ɪ', 'w', 'uː'], # quit/fruit/juice
        'oo': ['uː', 'ʊ'],     # food/book
        'ea': ['iː', 'ɛ'],     # eat/bread
        # ... many more patterns
    }
    
    def find_grapheme_for_phoneme(
        self,
        word: str,
        target_phoneme: str,
        word_phonemes: list[str]
    ) -> Optional[str]:
        """
        Find which grapheme produces the target phoneme
        
        Args:
            word: 'quick'
            target_phoneme: 'w'
            word_phonemes: ['k', 'w', 'ɪ', 'k']
        
        Returns:
            'qu' (because 'qu' = 'k' + 'w')
        """
        pass
    
    def get_example_words(self, grapheme: str) -> list[str]:
        """Get example words featuring the grapheme"""
        pass
    
    def get_phoneme_description(self, grapheme: str, phoneme: str) -> str:
        """
        Generate natural language description
        Example: "The 'qu' makes a 'kw' sound"
        """
        pass
```

### Phase 4: Mode Integration

#### Update: `core/modes/base_mode.py`

```python
from core.prompt_builder import PromptBuilder
from core.analysis.feedback_analyzer import FeedbackAnalyzer
from core.analysis.sentence_generator import SentenceGenerator

class BaseMode:
    """Enhanced base class with new analysis pipeline"""
    
    def __init__(self):
        self.prompt_builder = PromptBuilder()
        self.feedback_analyzer = FeedbackAnalyzer()
        self.sentence_generator = SentenceGenerator()
    
    async def get_feedback_and_next_sentence(
        self,
        attempted_sentence: str,
        analysis: AudioAnalysis,
        phoneme_assistant: PhonemeAssistant,
        session: Session,
    ):
        """Enhanced with new analysis pipeline"""
        
        # 1. PRE-ANALYSIS: Determine feedback strategy
        feedback_strategy = self.feedback_analyzer.analyze_for_feedback(
            pronunciation_data=analysis.pronunciation_dataframe.to_dict("records"),
            problem_summary=analysis.problem_summary,
            per_summary=analysis.per_summary
        )
        
        # 2. PRE-GENERATION: Calculate sentence parameters
        sentence_params = self.sentence_generator.calculate_sentence_params(
            overall_per=analysis.per_summary.get("sentence_per", 0),
            focus_phoneme=feedback_strategy.focus_phoneme,
            focus_grapheme=feedback_strategy.focus_grapheme
        )
        
        # 3. BUILD PROMPT: Assemble from sections with context
        prompt_context = {
            'should_praise': feedback_strategy.should_praise,
            'focus_phoneme': feedback_strategy.focus_phoneme,
            'focus_grapheme': feedback_strategy.focus_grapheme,
            'error_words': feedback_strategy.error_words,
            'error_type': feedback_strategy.error_type,
            'target_length': sentence_params.target_length,
            'min_phoneme_instances': sentence_params.min_focus_phoneme_instances,
            'min_grapheme_instances': sentence_params.min_focus_grapheme_instances,
            'complexity_level': sentence_params.complexity_level,
        }
        
        system_prompt = self.prompt_builder.build_prompt(
            sections=self._get_prompt_sections(),  # Defined by subclass
            context=prompt_context,
            include_ssml=True
        )
        
        # 4. QUERY GPT: With specific instructions
        user_input = self._build_user_input(
            attempted_sentence,
            analysis,
            feedback_strategy,
            sentence_params
        )
        
        conversation_history = [
            {"role": "system", "content": system_prompt},
            user_input
        ]
        
        # ... rest of GPT query and validation
        pass
    
    def _get_prompt_sections(self) -> list[str]:
        """Override in subclasses to specify sections"""
        raise NotImplementedError()
```

#### Update: `core/modes/unlimited.py`

```python
class UnlimitedPractice(BaseMode):
    """Updated to use modular prompts"""
    
    def _get_prompt_sections(self) -> list[str]:
        return [
            'base/system_role',
            'base/validation_rules',
            'feedback/praise_criteria',
            'feedback/phoneme_focus',
            'feedback/grapheme_instruction',
            'feedback/error_description',
            'sentence_generation/adaptive_difficulty',
            'sentence_generation/phoneme_density',
            'sentence_generation/grapheme_patterns',
            'modes/unlimited_context',
            'base/output_format',
            'ssml/ssml_minimal'  # Short feedback
        ]
```

#### Update: `core/modes/story.py`

```python
class StoryPractice(BaseMode):
    """Updated to use modular prompts"""
    
    def _get_prompt_sections(self) -> list[str]:
        return [
            'base/system_role',
            'base/validation_rules',
            'feedback/praise_criteria',
            'feedback/phoneme_focus',
            'feedback/grapheme_instruction',
            'feedback/error_description',
            'sentence_generation/adaptive_difficulty',
            'sentence_generation/phoneme_density',
            'sentence_generation/grapheme_patterns',
            'modes/story_context',  # Different from unlimited
            'base/output_format',
            'ssml/ssml_minimal'
        ]
    
    def _build_user_input(self, ...):
        """Story mode includes story context"""
        # Include past_sentences, story_name, etc.
        pass
```

---

## Implementation Phases

### Phase 1: Core Infrastructure (6-8 hours) ✅ COMPLETE

**Goal:** Create the prompt builder system and new directory structure

**Tasks:**

1. **Create `core/prompt_builder.py`**
   - [x] Implement `PromptSection` class
   - [x] Implement `PromptBuilder` class with template rendering
   - [x] Verify template variable substitution works

2. **Create prompt sections directory**
   - [x] Create `core/prompt_sections/` with subdirectories
   - [x] Migrate content from existing prompts to sections
   - [x] Split monolithic prompts into logical sections

3. **Create base sections** (from existing prompts)
   - [x] `base/system_role.txt` - Extract role definition
   - [x] `base/output_format.txt` - JSON schema
   - [x] `base/validation_rules.txt` - Critical rules

**Quality Assurance:**
- [x] PromptBuilder can load all sections without errors
- [x] Template variable substitution works correctly
- [x] All sections are valid UTF-8 text files
- [x] Manually verify building a prompt with multiple sections works

---

### Phase 2: Analysis Logic (8-10 hours) ⏸️ PENDING

**Goal:** Implement pre-analysis that determines feedback strategy

**Tasks:**

1. **Create `core/analysis/` package**
   - [ ] `__init__.py`
   - [ ] `feedback_analyzer.py`
   - [ ] `sentence_generator.py`

2. **Implement `FeedbackAnalyzer`**
   - [ ] `analyze_for_feedback()` - Main analysis method
   - [ ] `get_ground_truth_errors()` - Filter to missed/substituted only
   - [ ] `determine_praise_eligibility()` - Smart praise logic

3. **Implement `SentenceGenerator`**
   - [ ] `calculate_sentence_params()` - PER-based parameters
   - [ ] `get_difficulty_guidelines()` - PER to complexity mapping

4. **Update `SpeechProblemClassifier`** (if needed)
   - [ ] Ensure `recommended_focus_phoneme` prioritizes ground truth errors
   - [ ] Add logic to filter out addition errors

**Quality Assurance:**
- [ ] `get_ground_truth_errors()` excludes addition errors
- [ ] `determine_praise_eligibility()` only praises when PER <= 0.2 AND no consistent errors
- [ ] Sentence parameters scale correctly with PER (0.0-1.0 range)
- [ ] Edge cases handled (empty data, all errors, perfect pronunciation)
- [ ] Manually verify with sample data

---

### Phase 3: Grapheme-Phoneme Mapping (6-8 hours) ⏸️ PENDING

**Goal:** Connect phonemes to their spelling patterns

**Tasks:**

1. **Enhance `core/grapheme_to_phoneme.py`**
   - [ ] Create `GraphemePhonemeMapper` class
   - [ ] Add `GRAPHEME_PATTERNS` dictionary (common patterns)
   - [ ] Implement `find_grapheme_for_phoneme()`
   - [ ] Implement `get_example_words()`
   - [ ] Implement `get_phoneme_description()`

2. **Integrate with `FeedbackAnalyzer`**
   - [ ] Use mapper to find focus_grapheme from focus_phoneme
   - [ ] Include grapheme info in FeedbackStrategy

3. **Create comprehensive pattern database**
   - [ ] Common digraphs: ch, sh, th, ph, gh, wh
   - [ ] Common vowel teams: ea, oo, ai, ay, oi, oy, ou, ow
   - [ ] Consonant clusters: qu, ck, ng, -tch
   - [ ] R-controlled: ar, er, ir, or, ur

**Quality Assurance:**
- [ ] `find_grapheme_for_phoneme()` correctly maps phonemes to graphemes
- [ ] Handles multi-character graphemes (qu, ch, sh)
- [ ] Returns None when no clear grapheme mapping exists
- [ ] Example words are age-appropriate
- [ ] Manually verify with common words

**Goal:** Connect phonemes to their spelling patterns

**Tasks:**

1. **Enhance `core/grapheme_to_phoneme.py`**
   - Create `GraphemePhonemeMapper` class
   - Add `GRAPHEME_PATTERNS` dictionary (common patterns)
   - Implement `find_grapheme_for_phoneme()`
   - Implement `get_example_words()`
   - Implement `get_phoneme_description()`

2. **Integrate with `FeedbackAnalyzer`**
   - Use mapper to find focus_grapheme from focus_phoneme
   - Include grapheme info in FeedbackStrategy

3. **Create comprehensive pattern database**
   - Common digraphs: ch, sh, th, ph, gh, wh
   - Common vowel teams: ea, oo, ai, ay, oi, oy, ou, ow
   - Consonant clusters: qu, ck, ng, -tch
   - R-controlled: ar, er, ir, or, ur

**Quality Assurance:**
- [ ] `find_grapheme_for_phoneme()` correctly maps phonemes to graphemes
- [ ] Handles multi-character graphemes (qu, ch, sh)
- [ ] Returns None when no clear grapheme mapping exists
- [ ] Example words are age-appropriate

**Testing:**
```python
# Test grapheme mapper
mapper = GraphemePhonemeMapper()

# Test 'qu' = 'k' + 'w'
grapheme = mapper.find_grapheme_for_phoneme(
    word='quick',
    target_phoneme='w',
    word_phonemes=['k', 'w', 'ɪ', 'k']
)
assert grapheme == 'qu'

# Test 'ch' = 'tʃ'
grapheme = mapper.find_grapheme_for_phoneme(
    word='chat',
    target_phoneme='tʃ',
    word_phonemes=['tʃ', 'æ', 't']
)
assert grapheme == 'ch'
```

---

### Phase 4: Prompt Sections Content (8-10 hours) ⏸️ PENDING

**Goal:** Create high-quality prompt section content

**Tasks:**

1. **Create feedback sections**
   - [ ] `feedback/praise_criteria.txt` - Clear praise rules
   - [ ] `feedback/phoneme_focus.txt` - Use recommended_focus_phoneme
   - [ ] `feedback/grapheme_instruction.txt` - Teach grapheme-phoneme
   - [ ] `feedback/error_description.txt` - Describe what went wrong

2. **Create sentence generation sections**
   - [ ] `sentence_generation/adaptive_difficulty.txt` - PER scaling
   - [ ] `sentence_generation/phoneme_density.txt` - 5+ target instances
   - [ ] `sentence_generation/grapheme_patterns.txt` - Include target grapheme
   - [ ] `sentence_generation/length_guidelines.txt` - Length by PER

3. **Create mode-specific sections**
   - [ ] `modes/unlimited_context.txt` - Unlimited mode behavior
   - [ ] `modes/story_context.txt` - Story continuation rules
   - [ ] `modes/choice_story_context.txt` - Choice story specific

4. **Update SSML sections**
   - [ ] `ssml/ssml_minimal.txt` - For short feedback (1-2 sentences)
   - [ ] Keep existing `ssml/ssml_base.txt` for reference

**Quality Assurance:**
- [ ] Each section is focused and single-purpose
- [ ] Template variables are clearly marked with {variable}
- [ ] Instructions are specific and actionable
- [ ] No contradictory guidance across sections
- [ ] Sections can be mixed without conflicts

**Content Guidelines:**
- Be specific and prescriptive (not suggestive)
- Use examples to clarify expectations
- Reference data fields explicitly (e.g., "Check {focus_phoneme}")
- Keep each section under 500 words

**Example Section (`feedback/grapheme_instruction.txt`):**
```
GRAPHEME-PHONEME TEACHING:

Your feedback must connect the phoneme error to its grapheme (spelling pattern).

CRITICAL: The focus is on {focus_grapheme} which produces the {focus_phoneme} sound.

CORRECT FEEDBACK PATTERN:
"You had trouble with the '{focus_grapheme}' in {error_word}. The letters '{focus_grapheme}' make a '{phoneme_description}' sound."

EXAMPLES:
✅ "You had trouble with the 'qu' in 'quick'. The letters 'qu' make a 'kw' sound together."
✅ "You had trouble with the 'ch' in 'chat'. The letters 'ch' make a 'ch' sound like in 'chair'."
❌ "You had trouble with the 'k' sound in 'quick'." (doesn't mention the grapheme!)

WHEN {focus_grapheme} is provided, ALWAYS mention it in feedback.
If no grapheme is provided, fall back to phoneme-only feedback.
```

---

### Phase 5: Mode Integration (6-8 hours) ⏸️ PENDING

**Goal:** Integrate new system into existing modes

**Tasks:**

1. **Update `core/modes/base_mode.py`**
   - [ ] Add prompt_builder, feedback_analyzer, sentence_generator
   - [ ] Implement enhanced `get_feedback_and_next_sentence()`
   - [ ] Add `_get_prompt_sections()` abstract method
   - [ ] Add `_build_user_input()` helper

2. **Update `core/modes/unlimited.py`**
   - [ ] Override `_get_prompt_sections()`
   - [ ] Update `_build_user_input()` to include new fields
   - [ ] Manually verify with sample audio

3. **Update `core/modes/story.py`**
   - [ ] Override `_get_prompt_sections()`
   - [ ] Update `_build_user_input()` with story context
   - [ ] Manually verify with sample audio

4. **Update `core/modes/choice_story.py`**
   - [ ] Override `_get_prompt_sections()`
   - [ ] Update `_build_user_input()` appropriately
   - [ ] Manually verify with sample audio

**Quality Assurance:**
- [ ] All modes build prompts without errors
- [ ] FeedbackStrategy is created correctly
- [ ] SentenceParams are calculated and passed to GPT
- [ ] GPT receives focused instructions
- [ ] Existing functionality is preserved (no regressions)
- [ ] Manually test with real audio samples

---

### Phase 6: User Input Enhancement (4-6 hours) ⏸️ PENDING

**Goal:** Send structured instructions to GPT, not just data

**Tasks:**

1. **Update user input format**
   - [ ] Add `feedback_instructions` field
   - [ ] Add `sentence_requirements` field
   - [ ] Keep existing `pronunciation`, `problem_summary`, etc.

2. **Create instruction templates**
   - [ ] Praise instruction template
   - [ ] Correction instruction template
   - [ ] Sentence generation template

3. **Update all modes to use new format**
   - [ ] Verify all modes use new format

**Quality Assurance:**
- [ ] Instructions are clear and specific
- [ ] GPT receives both data AND what to do with it
- [ ] Reduces GPT's decision-making burden
- [ ] Manually verify GPT follows instructions

---

## Detailed Section Content Specifications

### Base Sections

#### `base/system_role.txt`
```
SYSTEM:
You are a phonics feedback assistant for young readers. You provide:
1. SHORT, focused feedback (1-2 sentences max)
2. Practice sentences with specific phoneme/grapheme patterns
3. Encouragement when appropriate

Your responses must be in valid JSON format.
```

#### `base/validation_rules.txt`
```
CRITICAL VALIDATION RULES:

1. VERIFY data before using it
   - Only mention words from {error_words} list
   - Only mention {focus_phoneme} if provided
   - Check phoneme_to_error_words before claiming errors

2. NO HALLUCINATIONS
   - Don't invent errors not in the data
   - Don't mention words not in error_words
   - Don't claim a word has a phoneme if not listed

3. FOLLOW INSTRUCTIONS
   - If {should_praise} is true, give simple praise
   - If false, correct using {focus_phoneme} and {focus_grapheme}
   - Meet sentence requirements exactly
```

#### `base/output_format.txt`
```
OUTPUT FORMAT:

Return valid JSON with these fields:

{
  "feedback": "1-2 sentence feedback (plain text)",
  "feedback_ssml": "SSML version with phoneme tags",
  "sentence": "Practice sentence meeting requirements"
}

REQUIREMENTS:
- feedback: Direct, clear, specific to the error
- feedback_ssml: Use <phoneme> tags only for corrected words
- sentence: Must contain required phoneme/grapheme instances
```

### Feedback Sections

#### `feedback/praise_criteria.txt`
```
PRAISE CRITERIA:

You will receive {should_praise} = true or false.

IF TRUE (should_praise):
- Give simple, genuine encouragement
- Examples: "Great job!", "Excellent reading!", "Well done!"
- NO specific corrections needed
- Sentence can be more challenging

IF FALSE (should_praise):
- Provide specific correction
- Focus on {focus_phoneme} and {focus_grapheme}
- Be clear about what needs work
- Sentence should practice the problem area
```

#### `feedback/grapheme_instruction.txt`
```
GRAPHEME-PHONEME TEACHING:

CRITICAL: Connect the sound ({focus_phoneme}) to its spelling ({focus_grapheme}).

CORRECT PATTERNS:
✅ "The '{focus_grapheme}' in {error_word} makes a '{phoneme_description}' sound."
✅ "When you see '{focus_grapheme}', it usually sounds like '{phoneme_description}'."

EXAMPLES:
- "The 'qu' in 'quick' makes a 'kw' sound."
- "The letters 'ch' in 'chat' make a 'ch' sound like in 'cheese'."
- "The 'th' in 'think' makes a soft 'th' sound."

ALWAYS mention both:
1. The grapheme (letters): {focus_grapheme}
2. The phoneme (sound): {focus_phoneme}

This helps students connect spelling to sound.
```

### Sentence Generation Sections

#### `sentence_generation/adaptive_difficulty.txt`
```
ADAPTIVE DIFFICULTY:

Sentence length and complexity based on performance:

{complexity_level} = "simple":
- Length: {target_length} words (approximately)
- Vocabulary: Basic, high-frequency words
- Structure: Simple subject-verb-object
- Example: "The cat sat on the mat."

{complexity_level} = "moderate":
- Length: {target_length} words
- Vocabulary: Grade-level words
- Structure: Can include simple conjunctions
- Example: "The quick brown fox jumped over the lazy dog."

{complexity_level} = "complex":
- Length: {target_length} words
- Vocabulary: More advanced, varied
- Structure: Complex sentences with clauses
- Example: "Although the weather was cold, the children played outside until sunset."

MATCH the complexity to student performance.
```

#### `sentence_generation/phoneme_density.txt`
```
PHONEME DENSITY REQUIREMENTS:

Your sentence MUST include:
- Minimum {min_focus_phoneme_instances} instances of the {focus_phoneme} sound
- Minimum {min_focus_grapheme_instances} instances of the '{focus_grapheme}' spelling

VERIFICATION PROCESS:
1. Draft your sentence
2. Count instances of {focus_grapheme}
3. If less than {min_focus_grapheme_instances}, add more words with {focus_grapheme}
4. Ensure sentence still sounds natural

EXAMPLES (for focus_grapheme='th'):
✅ "Think about this: the weather is thick with thunder and the path is worth walking." (7 'th' instances)
✅ "Throw the ball through the thick bushes by the path." (6 'th' instances)
❌ "The cat sat on the mat with Tom." (only 2 'th' instances - NOT ENOUGH)

COUNT CAREFULLY before finalizing.
```

#### `sentence_generation/grapheme_patterns.txt`
```
GRAPHEME PATTERN FOCUS:

PRIMARY GOAL: Include many words with the '{focus_grapheme}' spelling pattern.

GRAPHEME: {focus_grapheme}
SOUND: {focus_phoneme}

Find natural words containing '{focus_grapheme}':
- Beginning: {focus_grapheme} at start of word
- Middle: {focus_grapheme} in middle of word
- End: {focus_grapheme} at end of word

VARIETY is key - use {focus_grapheme} in different positions.

EXAMPLE (focus_grapheme='qu'):
"Quincy quickly asked a question about the quiet queen's quilt."
- 'qu' appears 6 times in different words
- Natural, coherent sentence
- Student practices 'qu' pattern repeatedly
```

---

## Migration Strategy

### Option A: Gradual Migration (Recommended)

1. **Phase 1-4**: Build new system alongside old
2. **Phase 5**: Add feature flag `USE_NEW_PROMPT_SYSTEM`
3. **Phase 6**: Test new system in parallel
4. **Phase 7**: Migrate one mode at a time (Unlimited → Story → Choice Story)
5. **Phase 8**: Remove old system after validation

### Option B: Fresh Start

1. **Phase 1-4**: Build complete new system
2. **Phase 5**: Switch all modes at once
3. **Phase 6**: Extensive testing
4. **Phase 7**: Fix issues, iterate

**Recommendation: Option A** - Lower risk, allows comparison, easier rollback

---

## Success Criteria

### Functional Requirements

- [ ] Prompts generated dynamically from sections
- [ ] Code determines feedback strategy before GPT
- [ ] Only ground truth phoneme errors analyzed
- [ ] Praise only given when appropriate
- [ ] Sentence difficulty adapts to PER
- [ ] Feedback mentions specific graphemes
- [ ] Sentences include target grapheme 5+ times

### Performance Requirements

- [ ] Prompt building adds < 50ms latency
- [ ] Analysis adds < 100ms latency
- [ ] Overall response time unchanged or better
- [ ] Memory usage unchanged or better

### Quality Requirements

- [ ] GPT feedback is more specific and helpful
- [ ] Students understand grapheme-phoneme connections
- [ ] False praise eliminated (no praise with consistent errors)
- [ ] Sentence generation is pedagogically sound
- [ ] SSML output is valid and natural

---

## Manual Validation Strategy

After each phase, manually verify functionality:

### Manual Verification Steps

1. **Phase 1 - Prompt Builder**
   - Verify sections load without errors
   - Check template variable substitution
   - Inspect generated prompts for correctness

2. **Phase 2 - Analysis Logic**
   - Test with sample pronunciation data
   - Verify ground truth error filtering
   - Check praise eligibility logic
   - Validate sentence parameters scaling

3. **Phase 3 - Grapheme Mapping**
   - Test common words (quick, chat, think, etc.)
   - Verify grapheme-phoneme mappings
   - Check edge cases (no clear mapping)

4. **Phase 4 - Prompt Content**
   - Review all section content for clarity
   - Verify template variables are correct
   - Check for contradictions across sections

5. **Phase 5 - Mode Integration**
   - Run each mode with sample audio
   - Verify GPT responses are appropriate
   - Check no regressions in existing functionality

6. **Phase 6 - User Input Enhancement**
   - Inspect GPT input format
   - Verify instructions are clear
   - Check GPT follows directives

### Success Indicators

- ✅ No Python errors during execution
- ✅ Prompts are coherent and well-structured
- ✅ GPT provides specific, helpful feedback
- ✅ Sentences include target graphemes
- ✅ System performs as well or better than before

---

## Rollback Plan

### If Issues Arise

1. **Feature Flag**: Set `USE_NEW_PROMPT_SYSTEM=false`
2. **Database**: No schema changes needed (data structure unchanged)
3. **Code**: Old system remains available
4. **Monitoring**: Compare old vs new system metrics

### Monitoring Metrics

- Response time (should not increase)
- GPT token usage (should decrease or stay same)
- User satisfaction (survey after implementation)
- Feedback quality (manual review of samples)
- Error rates (system errors, not pronunciation errors)

---

## Future Enhancements (Post-Implementation)

### Phase 8: Advanced Features (Optional)

1. **Multi-phoneme targeting**: Practice multiple phonemes in one sentence
2. **Phoneme progression tracking**: Build on previously mastered phonemes
3. **Context-aware vocabulary**: Adjust vocabulary to user's reading level
4. **Grapheme complexity scoring**: Target simpler graphemes for struggling readers
5. **A/B testing framework**: Compare prompt variations

### Phase 9: ML Enhancement (Optional)

1. **Sentence quality scoring**: ML model to rate practice sentences
2. **Grapheme difficulty prediction**: Learn which graphemes are hard for each user
3. **Personalized feedback templates**: Adapt to individual learning styles

---

## Appendix A: Key Decisions

### Why Modular Sections?

- **Flexibility**: Mix and match for different contexts
- **Maintainability**: Update one section without affecting others
- **Testability**: Test sections independently
- **Reusability**: Share sections across modes

### Why Pre-Analysis?

- **Precision**: Code is better at data analysis than GPT
- **Consistency**: Same input always produces same strategy
- **Performance**: Reduces GPT decision-making (fewer tokens)
- **Reliability**: Eliminates GPT hallucinations in analysis

### Why Ground Truth Focus?

- **Pedagogical**: Additions aren't pronunciation errors, they're artifacts
- **Clarity**: Focus on what should be said, not what was added
- **Effectiveness**: Target actual mispronunciations, not extras

### Why Grapheme Connection?

- **Reading skill**: Connects sound to spelling (decoding)
- **Retention**: Students remember patterns better
- **Generalization**: Applies to other words with same grapheme
- **Literacy**: Builds both pronunciation and spelling skills

---

## Appendix B: Example Transformations

### Before (Current System)

**Prompt:** (Static file, ~200 lines)
```
You are a phonics assistant. Analyze the data and provide feedback...
[Generic instructions]
```

**GPT Receives:**
```json
{
  "pronunciation": [...],
  "problem_summary": {...},
  "per_summary": {...}
}
```

**GPT Output:**
```json
{
  "feedback": "You had trouble with some sounds in the sentence.",
  "sentence": "The cat sat on the mat."
}
```

### After (New System)

**Prompt:** (Dynamic, ~150 lines)
```
[system_role]
[validation_rules]
[praise_criteria with should_praise=false]
[grapheme_instruction with focus_grapheme='th']
[phoneme_density with min_instances=5]
[output_format]
```

**GPT Receives:**
```json
{
  "feedback_instructions": {
    "action": "correct",
    "focus_phoneme": "θ",
    "focus_grapheme": "th",
    "error_words": ["think", "through"],
    "reason": "Consistent 'th' substitution"
  },
  "sentence_requirements": {
    "target_length": "15-20 words",
    "min_focus_grapheme_instances": 5,
    "complexity": "moderate"
  },
  "pronunciation_data": [...]
}
```

**GPT Output:**
```json
{
  "feedback": "The 'th' in 'think' and 'through' makes a soft sound. Put your tongue between your teeth.",
  "sentence": "I think the path through the thick forest is worth exploring with my three brothers."
}
```

**Improvements:**
- Feedback mentions specific grapheme ('th')
- Sentence has 6 'th' instances (meets requirement of 5+)
- Clear connection between sound and spelling
- Length appropriate for moderate complexity

---

## Appendix C: Section Template

Use this template when creating new sections:

```
<!-- Section Name: [name] -->
<!-- Purpose: [one-line description] -->
<!-- Required Context: [list of {variables}] -->
<!-- Used By: [which modes use this] -->

[Section Content]

INSTRUCTIONS:
[Specific instructions for GPT]

EXAMPLES:
✅ [Good example]
❌ [Bad example]

VALIDATION:
[What to check before proceeding]
```

---

## Implementation Timeline

**Estimated Total: 38-52 hours (Testing phase removed)**

- Phase 1: Core Infrastructure - 6-8 hours ✅ COMPLETE
- Phase 2: Analysis Logic - 8-10 hours ⏳ IN PROGRESS
- Phase 3: Grapheme Mapping - 6-8 hours ⏸️ PENDING
- Phase 4: Prompt Content - 8-10 hours ⏸️ PENDING
- Phase 5: Mode Integration - 6-8 hours ⏸️ PENDING
- Phase 6: User Input Enhancement - 4-6 hours ⏸️ PENDING

**Recommended Schedule:**
- Week 1: Phases 1-2 (Foundation)
- Week 2: Phases 3-4 (Content)
- Week 3: Phases 5-6 (Integration + Manual Validation)

---

## Contacts & Resources

- **Repository:** https://github.com/wordwizai/word-wiz-ai
- **Documentation:** `REPOSITORY_GUIDE.md`
- **Existing Prompts:** `backend/core/gpt_prompts/`
- **Mode Implementations:** `backend/core/modes/`
- **Analysis Logic:** `backend/core/speech_problem_classifier.py`

---

**End of Implementation Guide**
