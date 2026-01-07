"""
Sentence Generator Module

Calculates parameters for practice sentence generation based on user performance (PER).
Determines sentence length, complexity, and phoneme/grapheme instance requirements.
"""

from dataclasses import dataclass
from typing import Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class SentenceParams:
    """
    Parameters for practice sentence generation.
    
    Attributes:
        target_length: Target word count for the sentence
        complexity_level: Difficulty level ('simple', 'moderate', 'complex')
        min_focus_phoneme_instances: Minimum instances of focus phoneme
        min_focus_grapheme_instances: Minimum instances of focus grapheme
        other_phoneme_difficulty: Difficulty of non-focus phonemes ('low', 'medium')
    """
    target_length: int
    complexity_level: str
    min_focus_phoneme_instances: int
    min_focus_grapheme_instances: int
    other_phoneme_difficulty: str = 'low'


class SentenceGenerator:
    """
    Generates sentence parameters based on user performance.
    
    Key responsibility:
    - Adapt sentence difficulty to user's PER (Phoneme Error Rate)
    - Lower PER -> longer, more complex sentences
    - Higher PER -> shorter, simpler sentences
    """
    
    def __init__(self):
        """Initialize the sentence generator."""
        pass
    
    def calculate_sentence_params(
        self,
        overall_per: float,
        focus_phoneme: Optional[str] = None,
        focus_grapheme: Optional[str] = None
    ) -> SentenceParams:
        """
        Calculate sentence parameters based on performance.
        
        Args:
            overall_per: Overall sentence PER (0.0-1.0)
            focus_phoneme: Focus phoneme for practice
            focus_grapheme: Focus grapheme for practice
            
        Returns:
            SentenceParams with calculated values
        """
        # Get difficulty guidelines based on PER
        guidelines = self.get_difficulty_guidelines(overall_per)
        
        # Determine minimum instances based on whether correction is needed
        if focus_phoneme and overall_per > 0.2:
            # Needs practice - require more instances
            min_phoneme_instances = 5
            min_grapheme_instances = 5
        else:
            # Good performance or no focus - fewer instances needed
            min_phoneme_instances = 3
            min_grapheme_instances = 3
        
        return SentenceParams(
            target_length=guidelines['target_length'],
            complexity_level=guidelines['complexity'],
            min_focus_phoneme_instances=min_phoneme_instances,
            min_focus_grapheme_instances=min_grapheme_instances,
            other_phoneme_difficulty=guidelines['other_difficulty']
        )
    
    def get_difficulty_guidelines(self, overall_per: float) -> dict:
        """
        Map PER to difficulty parameters.
        
        PER Ranges:
        - 0.0-0.1: Excellent (long, complex sentences)
        - 0.1-0.3: Good (moderate sentences)
        - 0.3-0.5: Fair (simple sentences)
        - 0.5+: Struggling (very simple sentences)
        
        Args:
            overall_per: Overall sentence PER (0.0-1.0)
            
        Returns:
            Dictionary with target_length, complexity, and other_difficulty
        """
        if overall_per <= 0.1:
            # Excellent performance - challenge them
            return {
                'target_length': 22,  # 20-25 words
                'complexity': 'complex',
                'other_difficulty': 'medium',
                'description': 'Excellent - complex sentences with varied vocabulary'
            }
        
        elif overall_per <= 0.3:
            # Good performance - moderate challenge
            return {
                'target_length': 17,  # 15-20 words
                'complexity': 'moderate',
                'other_difficulty': 'low',
                'description': 'Good - moderate sentences with grade-level vocabulary'
            }
        
        elif overall_per <= 0.5:
            # Fair performance - keep it simple
            return {
                'target_length': 12,  # 10-15 words
                'complexity': 'simple',
                'other_difficulty': 'low',
                'description': 'Fair - simple sentences with basic vocabulary'
            }
        
        else:
            # Struggling - very simple
            return {
                'target_length': 10,  # 8-12 words
                'complexity': 'simple',
                'other_difficulty': 'low',
                'description': 'Struggling - very simple sentences with basic words'
            }
    
    def get_complexity_description(self, complexity_level: str) -> str:
        """
        Get description of what a complexity level means.
        
        Args:
            complexity_level: 'simple', 'moderate', or 'complex'
            
        Returns:
            Human-readable description
        """
        descriptions = {
            'simple': (
                "Simple sentences with basic, high-frequency words. "
                "Subject-verb-object structure. Example: 'The cat sat on the mat.'"
            ),
            'moderate': (
                "Moderate sentences with grade-level vocabulary. "
                "Can include simple conjunctions. Example: 'The quick brown fox jumped over the lazy dog.'"
            ),
            'complex': (
                "Complex sentences with advanced vocabulary and varied structure. "
                "Can include clauses. Example: 'Although the weather was cold, the children played outside until sunset.'"
            )
        }
        
        return descriptions.get(complexity_level, "Unknown complexity level")
    
    def format_for_prompt(self, params: SentenceParams) -> dict:
        """
        Format sentence parameters for inclusion in GPT prompt.
        
        Args:
            params: SentenceParams instance
            
        Returns:
            Dictionary formatted for prompt context
        """
        return {
            'target_length': f"{params.target_length-3}-{params.target_length+3} words",
            'complexity_level': params.complexity_level,
            'min_focus_phoneme_instances': params.min_focus_phoneme_instances,
            'min_focus_grapheme_instances': params.min_focus_grapheme_instances,
            'other_phoneme_difficulty': params.other_phoneme_difficulty,
            'complexity_description': self.get_complexity_description(params.complexity_level)
        }
