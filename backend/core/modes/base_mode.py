from core.phoneme_assistant import PhonemeAssistant
from core.prompt_builder import PromptBuilder
from core.analysis import FeedbackAnalyzer, SentenceGenerator
from models.session import Session
from schemas.feedback_entry import AudioAnalysis
from typing import List, Dict, Optional
import json
import asyncio


class BaseMode:
    """
    Base class for all modes with integrated new prompt system.
    """

    def __init__(self):
        """Initialize with new analysis components."""
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
        """
        Get the feedback based on the pronunciation using the new analysis pipeline.
        
        This enhanced implementation:
        1. Pre-analyzes data with FeedbackAnalyzer
        2. Calculates sentence parameters with SentenceGenerator
        3. Builds dynamic prompt with PromptBuilder
        4. Queries GPT with focused instructions
        """
        # Extract data from analysis
        per_summary = analysis.per_summary
        pronunciation_data = analysis.pronunciation_dataframe.to_dict("records")
        problem_summary = analysis.problem_summary
        
        # Enhance pronunciation data with phoneme breakdowns
        enhanced_pronunciation = self._enhance_pronunciation_data(pronunciation_data)
        
        # Create phoneme-to-word mapping
        phoneme_to_error_words = self._create_phoneme_to_error_mapping(pronunciation_data)
        
        # Build full problem summary
        full_problem_summary = {
            "most_common_phoneme": problem_summary.get("most_common_phoneme"),
            "phoneme_error_counts": problem_summary.get("phoneme_error_counts", {}),
            "recommended_focus_phoneme": problem_summary.get("recommended_focus_phoneme"),
            "high_frequency_errors": problem_summary.get("high_frequency_errors", []),
            "phoneme_to_error_words": phoneme_to_error_words
        }
        
        # STEP 1: PRE-ANALYSIS - Determine feedback strategy
        feedback_strategy = self.feedback_analyzer.analyze_for_feedback(
            pronunciation_data=enhanced_pronunciation,
            problem_summary=full_problem_summary,
            per_summary=per_summary
        )
        
        # STEP 2: PRE-GENERATION - Calculate sentence parameters
        sentence_params = self.sentence_generator.calculate_sentence_params(
            overall_per=per_summary.get("sentence_per", 0),
            focus_phoneme=feedback_strategy.focus_phoneme,
            focus_grapheme=feedback_strategy.focus_grapheme
        )
        
        # STEP 3: BUILD PROMPT - Assemble from sections with context
        prompt_context = self._build_prompt_context(
            feedback_strategy,
            sentence_params,
            session
        )
        
        system_prompt = self.prompt_builder.build_prompt(
            sections=self._get_prompt_sections(),
            context=prompt_context,
            include_ssml=True
        )
        
        # STEP 4: BUILD USER INPUT - With specific instructions
        user_input_content = self._build_user_input(
            attempted_sentence,
            enhanced_pronunciation,
            full_problem_summary,
            per_summary,
            feedback_strategy,
            sentence_params,
            session
        )
        
        user_input = {
            "role": "user",
            "content": json.dumps(user_input_content)
        }
        
        # STEP 5: QUERY GPT - With focused instructions
        conversation_history = [
            {"role": "system", "content": system_prompt},
            user_input
        ]
        
        print("Using new prompt system with", len(self._get_prompt_sections()), "sections")
        print("Feedback strategy:", feedback_strategy)
        print("Sentence params:", sentence_params)
        
        # Get GPT response
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, phoneme_assistant.query_gpt, conversation_history
        )
        
        # Extract and validate JSON
        json_response = phoneme_assistant.extract_json(response)
        
        # Import validator here to avoid circular import
        from core.gpt_output_validator import validate_and_log
        validated_response = validate_and_log(
            json_response,
            enhanced_pronunciation,
            full_problem_summary,
            include_warnings_in_response=False
        )
        
        return validated_response
    
    def _enhance_pronunciation_data(self, pronunciation_data: List[Dict]) -> List[Dict]:
        """
        Enhance pronunciation data with phoneme breakdowns.
        """
        enhanced_pronunciation = []
        for word_data in pronunciation_data:
            # Get ground truth phonemes
            gt_phonemes = word_data.get("ground_truth_phonemes", [])
            if isinstance(gt_phonemes, tuple) and len(gt_phonemes) == 2:
                gt_phonemes = gt_phonemes[1]
            if not isinstance(gt_phonemes, list):
                gt_phonemes = []
            
            enhanced_word = {
                **word_data,
                "expected_phonemes": gt_phonemes,
                "actual_phonemes": word_data.get("phonemes", []),
                "word_structure": f"{word_data.get('ground_truth_word') or ''} = [{', '.join(gt_phonemes)}]"
            }
            enhanced_pronunciation.append(enhanced_word)
        
        return enhanced_pronunciation
    
    def _create_phoneme_to_error_mapping(self, pronunciation_data: List[Dict]) -> Dict:
        """
        Create mapping of phonemes to words with errors.
        """
        phoneme_to_error_words = {}
        for word_data in pronunciation_data:
            if word_data.get("per", 0) > 0:
                word = word_data.get("ground_truth_word") or ""
                
                # Missed phonemes
                for phoneme in word_data.get("missed", []):
                    if phoneme not in phoneme_to_error_words:
                        phoneme_to_error_words[phoneme] = []
                    phoneme_to_error_words[phoneme].append({"word": word, "error_type": "missed"})
                
                # Added phonemes
                for phoneme in word_data.get("added", []):
                    if phoneme not in phoneme_to_error_words:
                        phoneme_to_error_words[phoneme] = []
                    phoneme_to_error_words[phoneme].append({"word": word, "error_type": "added"})
                
                # Substituted phonemes
                for sub in word_data.get("substituted", []):
                    expected_phoneme = sub[0] if isinstance(sub, (list, tuple)) and len(sub) > 0 else sub
                    if expected_phoneme not in phoneme_to_error_words:
                        phoneme_to_error_words[expected_phoneme] = []
                    phoneme_to_error_words[expected_phoneme].append({"word": word, "error_type": "substituted"})
        
        return phoneme_to_error_words
    
    def _build_prompt_context(
        self,
        feedback_strategy,
        sentence_params,
        session
    ) -> Dict:
        """
        Build context dictionary for prompt template variables.
        """
        # Format sentence params for prompt
        formatted_params = self.sentence_generator.format_for_prompt(sentence_params)
        
        context = {
            'should_praise': str(feedback_strategy.should_praise).lower(),
            'focus_phoneme': feedback_strategy.focus_phoneme or '',
            'focus_grapheme': feedback_strategy.focus_grapheme or '',
            'error_words': ', '.join(feedback_strategy.error_words),
            'target_length': formatted_params['target_length'],
            'complexity_level': formatted_params['complexity_level'],
            'min_focus_phoneme_instances': str(formatted_params['min_focus_phoneme_instances']),
            'min_focus_grapheme_instances': str(formatted_params['min_focus_grapheme_instances']),
        }
        
        return context
    
    def _build_user_input(
        self,
        attempted_sentence: str,
        enhanced_pronunciation: List[Dict],
        full_problem_summary: Dict,
        per_summary: Dict,
        feedback_strategy,
        sentence_params,
        session
    ) -> Dict:
        """
        Build user input content with data and instructions.
        
        Override in subclasses to add mode-specific context.
        """
        return {
            "attempted_sentence": attempted_sentence,
            "pronunciation": enhanced_pronunciation,
            "problem_summary": full_problem_summary,
            "per_summary": per_summary,
            # Add feedback instructions
            "feedback_instructions": {
                "action": "praise" if feedback_strategy.should_praise else "correct",
                "focus_phoneme": feedback_strategy.focus_phoneme,
                "focus_grapheme": feedback_strategy.focus_grapheme,
                "error_words": feedback_strategy.error_words,
                "error_type": feedback_strategy.error_type,
            },
            # Add sentence requirements
            "sentence_requirements": {
                "target_length": sentence_params.target_length,
                "complexity": sentence_params.complexity_level,
                "min_focus_instances": sentence_params.min_focus_grapheme_instances,
            }
        }
    
    def _get_prompt_sections(self) -> List[str]:
        """
        Get list of prompt sections to use.
        
        Override in subclasses to specify different sections.
        """
        raise NotImplementedError("Subclasses should implement this method.")
