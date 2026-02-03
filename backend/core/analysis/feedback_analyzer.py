"""
Feedback Analyzer Module

Pre-analyzes pronunciation data to determine feedback strategy before GPT involvement.
Filters ground truth errors, determines praise eligibility, and identifies focus phonemes/graphemes.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


@dataclass
class FeedbackStrategy:
    """
    Strategy for providing feedback based on pronunciation analysis.
    
    Attributes:
        should_praise: Whether to praise (True) or correct (False)
        focus_phoneme: Primary phoneme to focus on (IPA format)
        focus_grapheme: Grapheme representation of focus phoneme (letters)
        error_words: List of words that had errors with the focus phoneme
        error_type: Type of error ('substituted', 'missed', 'mixed')
        severity: Error severity ('low', 'medium', 'high')
        reason: Human-readable explanation of the strategy
    """
    should_praise: bool
    focus_phoneme: Optional[str] = None
    focus_grapheme: Optional[str] = None
    error_words: List[str] = None
    error_type: str = 'mixed'
    severity: str = 'medium'
    reason: str = ''
    
    def __post_init__(self):
        if self.error_words is None:
            self.error_words = []


class FeedbackAnalyzer:
    """
    Analyzes pronunciation data to determine feedback strategy.
    
    Key responsibilities:
    1. Filter to ground truth errors only (missed/substituted, not additions)
    2. Determine if praise is appropriate (PER <= 0.2 AND no consistent errors)
    3. Identify focus phoneme and grapheme for correction
    4. Assess error severity
    """
    
    def __init__(self, grapheme_mapper=None):
        """
        Initialize the feedback analyzer.
        
        Args:
            grapheme_mapper: Optional GraphemePhonemeMapper instance. If None, creates one.
        """
        if grapheme_mapper is None:
            from core.grapheme_to_phoneme import GraphemePhonemeMapper
            grapheme_mapper = GraphemePhonemeMapper()
        self.grapheme_mapper = grapheme_mapper
    
    def analyze_for_feedback(
        self,
        pronunciation_data: List[Dict],
        problem_summary: Dict,
        per_summary: Dict
    ) -> FeedbackStrategy:
        """
        Analyze pronunciation data and determine feedback strategy.
        
        Args:
            pronunciation_data: List of word pronunciation dictionaries
            problem_summary: Summary of phoneme errors
            per_summary: Overall PER statistics
            
        Returns:
            FeedbackStrategy with praise/correction decision and focus areas
        """
        sentence_per = per_summary.get('sentence_per', 0.0)
        
        # Get ground truth errors (filter out additions)
        ground_truth_errors = self.get_ground_truth_errors(pronunciation_data)
        
        # Check phoneme_to_error_words for consistent errors
        phoneme_to_error_words = problem_summary.get('phoneme_to_error_words', {})
        
        # Determine if we should praise
        should_praise, reason = self.determine_praise_eligibility(
            sentence_per,
            phoneme_to_error_words
        )
        
        if should_praise:
            return FeedbackStrategy(
                should_praise=True,
                reason=reason
            )
        
        # Need correction - find focus phoneme
        focus_phoneme, focus_grapheme, error_words, error_type = self._determine_focus(
            problem_summary,
            phoneme_to_error_words,
            ground_truth_errors,
            pronunciation_data
        )
        
        # Assess severity
        severity = self._assess_severity(sentence_per, len(error_words))
        
        return FeedbackStrategy(
            should_praise=False,
            focus_phoneme=focus_phoneme,
            focus_grapheme=focus_grapheme,
            error_words=error_words,
            error_type=error_type,
            severity=severity,
            reason=f"PER={sentence_per:.2f}, consistent errors in {len(error_words)} word(s)"
        )
    
    def get_ground_truth_errors(self, pronunciation_data: List[Dict]) -> Dict:
        """
        Extract only ground truth phoneme errors (missed/substituted, not additions).
        
        Additions are artifacts of the detection algorithm, not pronunciation errors.
        We focus on what should have been said but wasn't (missed) or was wrong (substituted).
        
        Args:
            pronunciation_data: List of word pronunciation dictionaries
            
        Returns:
            Dictionary with 'missed' and 'substituted' phoneme lists
        """
        ground_truth_errors = {
            'missed': [],
            'substituted': []
        }
        
        for word_data in pronunciation_data:
            # Only count errors (PER > 0)
            if word_data.get('per', 0) > 0:
                # Missed phonemes (ground truth phonemes not said)
                missed = word_data.get('missed', [])
                if missed:
                    ground_truth_errors['missed'].extend(missed)
                
                # Substituted phonemes (ground truth phonemes said incorrectly)
                substituted = word_data.get('substituted', [])
                if substituted:
                    # substituted is a list of [expected, actual] pairs
                    for sub in substituted:
                        if isinstance(sub, (list, tuple)) and len(sub) > 0:
                            ground_truth_errors['substituted'].append(sub[0])  # Expected phoneme
                        elif isinstance(sub, str):
                            ground_truth_errors['substituted'].append(sub)
        
        logger.info(f"Ground truth errors: {len(ground_truth_errors['missed'])} missed, "
                   f"{len(ground_truth_errors['substituted'])} substituted")
        
        return ground_truth_errors
    
    def determine_praise_eligibility(
        self,
        sentence_per: float,
        phoneme_to_error_words: Dict
    ) -> Tuple[bool, str]:
        """
        Determine if praise is appropriate.
        
        Only praise if:
        1. PER <= 0.2 (few errors overall)
        2. No consistent error patterns (same phoneme in 2+ words)
        
        Args:
            sentence_per: Overall sentence PER
            phoneme_to_error_words: Mapping of phonemes to words with errors
            
        Returns:
            Tuple of (should_praise, reason)
        """
        # Check PER threshold
        if sentence_per > 0.2:
            return False, f"PER too high: {sentence_per:.2f} > 0.2"
        
        # Check for consistent error patterns
        for phoneme, error_list in phoneme_to_error_words.items():
            if len(error_list) >= 2:
                words = [e['word'] for e in error_list]
                return False, f"Consistent '{phoneme}' errors in {len(error_list)} words: {words}"
        
        # Check if there are ANY errors at all
        if not phoneme_to_error_words or all(len(v) == 0 for v in phoneme_to_error_words.values()):
            return True, "Perfect pronunciation, no errors"
        
        # Low PER and no consistent errors
        return True, f"Good performance: PER={sentence_per:.2f}, no consistent errors"
    
    def _determine_focus(
        self,
        problem_summary: Dict,
        phoneme_to_error_words: Dict,
        ground_truth_errors: Dict,
        pronunciation_data: List[Dict]
    ) -> Tuple[Optional[str], Optional[str], List[str], str]:
        """
        Determine which phoneme/grapheme to focus on for correction.
        
        Priority:
        1. Use recommended_focus_phoneme if available (pedagogically chosen)
        2. Find most consistent error from phoneme_to_error_words
        3. Fall back to most common error
        
        Args:
            problem_summary: Problem summary with recommended focus
            phoneme_to_error_words: Phoneme to error words mapping
            ground_truth_errors: Ground truth error dictionary
            pronunciation_data: List of word pronunciation dictionaries
            
        Returns:
            Tuple of (focus_phoneme, focus_grapheme, error_words, error_type)
        """
        # Priority 1: Use recommended_focus_phoneme if available
        recommended = problem_summary.get('recommended_focus_phoneme')
        if recommended and isinstance(recommended, tuple) and len(recommended) >= 1:
            focus_phoneme = recommended[0]
            
            # Get words with this phoneme error
            error_words = []
            if focus_phoneme in phoneme_to_error_words:
                error_words = [e['word'] for e in phoneme_to_error_words[focus_phoneme]]
            
            # Determine error type
            error_type = self._determine_error_type(focus_phoneme, ground_truth_errors)
            
            # Find grapheme for this phoneme using the mapper
            focus_grapheme = self._find_grapheme_for_error(
                focus_phoneme,
                error_words,
                pronunciation_data
            )
            
            return focus_phoneme, focus_grapheme, error_words, error_type
        
        # Priority 2: Find most consistent error (appears in most words)
        if phoneme_to_error_words:
            # Sort by number of affected words
            sorted_phonemes = sorted(
                phoneme_to_error_words.items(),
                key=lambda x: len(x[1]),
                reverse=True
            )
            
            if sorted_phonemes:
                focus_phoneme, error_list = sorted_phonemes[0]
                error_words = [e['word'] for e in error_list]
                error_type = self._determine_error_type(focus_phoneme, ground_truth_errors)
                
                # Find grapheme
                focus_grapheme = self._find_grapheme_for_error(
                    focus_phoneme,
                    error_words,
                    pronunciation_data
                )
                
                return focus_phoneme, focus_grapheme, error_words, error_type
        
        # Priority 3: Fall back to most common error
        most_common = problem_summary.get('most_common_phoneme')
        if most_common and len(most_common) >= 1:
            focus_phoneme = most_common[0]
            error_words = []
            error_type = 'mixed'
            focus_grapheme = None
            
            return focus_phoneme, focus_grapheme, error_words, error_type
        
        # No clear focus
        logger.warning("Could not determine focus phoneme")
        return None, None, [], 'mixed'
    
    def _find_grapheme_for_error(
        self,
        focus_phoneme: str,
        error_words: List[str],
        pronunciation_data: List[Dict]
    ) -> Optional[str]:
        """
        Find the grapheme that corresponds to the focus phoneme in error words.
        
        Args:
            focus_phoneme: The phoneme to find grapheme for
            error_words: List of words with errors
            pronunciation_data: Full pronunciation data
            
        Returns:
            The most common grapheme for this phoneme, or None
        """
        if not error_words:
            return None
        
        # Try to find grapheme from the first error word
        for word_data in pronunciation_data:
            word = word_data.get('ground_truth_word', '')
            if word in error_words:
                # Get expected phonemes for this word
                expected_phonemes = word_data.get('expected_phonemes', [])
                
                # Try to find grapheme
                grapheme = self.grapheme_mapper.find_grapheme_for_phoneme(
                    word,
                    focus_phoneme,
                    expected_phonemes
                )
                
                if grapheme:
                    logger.info(f"Found grapheme '{grapheme}' for phoneme '{focus_phoneme}' in word '{word}'")
                    return grapheme
        
        # Fallback: get common grapheme patterns for this phoneme
        patterns = self.grapheme_mapper.get_grapheme_patterns_for_phoneme(focus_phoneme)
        if patterns:
            return patterns[0]  # Return most common pattern
        
        return None
    
    def _determine_error_type(self, phoneme: str, ground_truth_errors: Dict) -> str:
        """
        Determine if the phoneme error is primarily missed, substituted, or mixed.
        
        Args:
            phoneme: The focus phoneme
            ground_truth_errors: Ground truth error dictionary
            
        Returns:
            Error type: 'missed', 'substituted', or 'mixed'
        """
        missed_count = ground_truth_errors['missed'].count(phoneme)
        substituted_count = ground_truth_errors['substituted'].count(phoneme)
        
        if missed_count > 0 and substituted_count == 0:
            return 'missed'
        elif substituted_count > 0 and missed_count == 0:
            return 'substituted'
        else:
            return 'mixed'
    
    def _assess_severity(self, sentence_per: float, num_error_words: int) -> str:
        """
        Assess error severity based on PER and number of affected words.
        
        Args:
            sentence_per: Overall sentence PER
            num_error_words: Number of words with errors
            
        Returns:
            Severity: 'low', 'medium', or 'high'
        """
        if sentence_per >= 0.5 or num_error_words >= 4:
            return 'high'
        elif sentence_per >= 0.3 or num_error_words >= 2:
            return 'medium'
        else:
            return 'low'
