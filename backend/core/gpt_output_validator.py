"""
GPT Output Validator

This module validates GPT-generated feedback to ensure:
1. GPT only mentions phonemes that exist in the analyzed words
2. Practice sentences contain the target phoneme adequately (5+ times)
3. Feedback is appropriate and doesn't contain hallucinations

This helps catch and correct GPT errors before sending feedback to users.
"""

import logging
import re
from typing import Dict, List, Set, Tuple

logger = logging.getLogger(__name__)


def extract_phonemes_from_pronunciation_data(pronunciation_data: List[Dict]) -> Set[str]:
    """
    Extract all valid phonemes from the pronunciation data.
    
    Args:
        pronunciation_data: List of word pronunciation dictionaries
        
    Returns:
        Set of all phonemes that appear in the ground truth words
    """
    valid_phonemes = set()
    
    for word_data in pronunciation_data:
        # Get expected phonemes from the ground truth
        expected_phonemes = word_data.get("expected_phonemes", [])
        if expected_phonemes:
            valid_phonemes.update(expected_phonemes)
        
        # Also check ground_truth_phonemes as fallback
        ground_truth_phonemes = word_data.get("ground_truth_phonemes", [])
        if ground_truth_phonemes:
            valid_phonemes.update(ground_truth_phonemes)
    
    return valid_phonemes


def count_phoneme_in_sentence(sentence: str, target_phoneme: str) -> int:
    """
    Count approximate occurrences of a target phoneme in a sentence.
    
    This is a heuristic-based approach that looks for common letter patterns.
    Not perfect, but helps validate GPT's sentence generation.
    
    Args:
        sentence: The practice sentence
        target_phoneme: The target phoneme to count
        
    Returns:
        Approximate count of target phoneme occurrences
    """
    sentence_lower = sentence.lower()
    count = 0
    
    # Common phoneme-to-letter mappings (heuristic)
    phoneme_patterns = {
        'θ': [r'\bth', r'th\b'],  # 'th' in think, with, bath
        'ð': [r'\bthe\b', r'\bthis\b', r'\bthat\b'],  # 'th' in the, this
        'ʃ': [r'sh'],  # 'sh' sound
        'tʃ': [r'ch'],  # 'ch' sound
        'dʒ': [r'j', r'\bg'],  # 'j' sound (gem, judge)
        'l': [r'l'],  # 'l' sound
        'r': [r'r'],  # 'r' sound
        'w': [r'w'],  # 'w' sound
        'j': [r'y'],  # 'y' sound (yes)
        'ŋ': [r'ng'],  # 'ng' sound (sing)
    }
    
    # If we have a pattern for this phoneme, use it
    if target_phoneme in phoneme_patterns:
        for pattern in phoneme_patterns[target_phoneme]:
            count += len(re.findall(pattern, sentence_lower))
    else:
        # Fallback: just count the phoneme character itself
        count = sentence_lower.count(target_phoneme.lower())
    
    return count


def validate_gpt_feedback(
    feedback_dict: Dict,
    pronunciation_data: List[Dict],
    problem_summary: Dict,
    min_phoneme_instances: int = 5
) -> Tuple[bool, Dict, List[str]]:
    """
    Validate GPT's feedback output.
    
    Args:
        feedback_dict: The GPT response dictionary with 'feedback', 'feedback_ssml', 'sentence'
        pronunciation_data: The pronunciation data sent to GPT
        problem_summary: The problem summary
        min_phoneme_instances: Minimum required instances of target phoneme in practice sentence
        
    Returns:
        Tuple of (is_valid, corrected_feedback, warnings)
        - is_valid: Whether feedback passes validation
        - corrected_feedback: The feedback dict (potentially with corrections)
        - warnings: List of validation warning messages
    """
    warnings = []
    is_valid = True
    corrected_feedback = feedback_dict.copy()
    
    # Extract valid phonemes from pronunciation data
    valid_phonemes = extract_phonemes_from_pronunciation_data(pronunciation_data)
    
    # Get target phoneme from problem_summary
    target_phoneme = None
    if "recommended_focus_phoneme" in problem_summary:
        recommended = problem_summary["recommended_focus_phoneme"]
        if isinstance(recommended, (list, tuple)) and len(recommended) > 0:
            target_phoneme = recommended[0]
    
    if not target_phoneme and "most_common_phoneme" in problem_summary:
        most_common = problem_summary["most_common_phoneme"]
        if isinstance(most_common, (list, tuple)) and len(most_common) > 0:
            target_phoneme = most_common[0]
    
    # Validation 1: Check if practice sentence has enough instances of target phoneme
    if "sentence" in feedback_dict and target_phoneme:
        sentence = feedback_dict["sentence"]
        phoneme_count = count_phoneme_in_sentence(sentence, target_phoneme)
        
        if phoneme_count < min_phoneme_instances:
            warnings.append(
                f"Practice sentence may not have enough '{target_phoneme}' sounds "
                f"(found ~{phoneme_count}, expected {min_phoneme_instances}+)"
            )
            is_valid = False
    
    # Validation 2: Check that feedback mentions specific words from pronunciation_data
    if "feedback" in feedback_dict and feedback_dict["feedback"] and isinstance(feedback_dict["feedback"], str):
        feedback_text = feedback_dict["feedback"].lower()
        mentioned_any_word = False
        
        for word_data in pronunciation_data:
            # ground_truth_word can be None for insertion/deletion word alignment types
            ground_truth_word = word_data.get("ground_truth_word") or ""
            ground_truth_word_lower = ground_truth_word.lower() if ground_truth_word else ""
            if ground_truth_word_lower and ground_truth_word_lower in feedback_text:
                mentioned_any_word = True
                break
        
        if not mentioned_any_word and len(pronunciation_data) > 0:
            warnings.append(
                "Feedback doesn't mention any specific words from the sentence. "
                "GPT should reference actual words that were mispronounced."
            )
    
    # Validation 3: Log for manual review if feedback seems generic
    if "feedback" in feedback_dict and feedback_dict["feedback"] and isinstance(feedback_dict["feedback"], str):
        feedback_text = feedback_dict["feedback"].lower()
        generic_phrases = [
            "you had trouble",
            "let's practice",
            "keep working",
            "try again"
        ]
        
        if sum(1 for phrase in generic_phrases if phrase in feedback_text) >= 2:
            warnings.append(
                "Feedback may be too generic. Should be more specific about which words "
                "and phonemes were problematic."
            )
    
    # Log validation results
    if warnings:
        logger.warning(f"GPT feedback validation warnings: {warnings}")
    
    if is_valid:
        logger.info("GPT feedback passed validation")
    else:
        logger.error(f"GPT feedback failed validation: {warnings}")
    
    return is_valid, corrected_feedback, warnings


def add_validation_note_to_feedback(
    feedback_dict: Dict,
    warnings: List[str]
) -> Dict:
    """
    Add a validation note to feedback for development/debugging.
    
    In production, you might want to remove this or only include in logs.
    
    Args:
        feedback_dict: The feedback dictionary
        warnings: List of validation warnings
        
    Returns:
        Updated feedback dictionary with validation note
    """
    if warnings:
        # For development, you might append a note
        # In production, you'd just log this
        validation_note = f" [Validation note: {'; '.join(warnings)}]"
        feedback_dict["_validation_warnings"] = warnings
        logger.info(f"Added validation warnings to feedback: {validation_note}")
    
    return feedback_dict


def validate_and_log(
    feedback_dict: Dict,
    pronunciation_data: List[Dict],
    problem_summary: Dict,
    include_warnings_in_response: bool = False
) -> Dict:
    """
    Convenience function to validate feedback and optionally include warnings.
    
    Args:
        feedback_dict: GPT response
        pronunciation_data: Pronunciation data
        problem_summary: Problem summary
        include_warnings_in_response: Whether to include warnings in the response
        
    Returns:
        Validated (and potentially annotated) feedback dictionary
    """
    is_valid, corrected_feedback, warnings = validate_gpt_feedback(
        feedback_dict,
        pronunciation_data,
        problem_summary
    )
    
    # Log validation results
    logger.info(f"GPT Feedback Validation - Valid: {is_valid}, Warnings: {len(warnings)}")
    
    if include_warnings_in_response and warnings:
        corrected_feedback = add_validation_note_to_feedback(corrected_feedback, warnings)
    
    return corrected_feedback
