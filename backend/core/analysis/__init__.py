"""
Analysis package for pre-processing pronunciation data and determining feedback strategy.

This package contains:
- FeedbackAnalyzer: Determines whether to praise or correct based on PER and error consistency
- SentenceGenerator: Calculates sentence parameters based on performance
"""

from .feedback_analyzer import FeedbackAnalyzer, FeedbackStrategy
from .sentence_generator import SentenceGenerator, SentenceParams

__all__ = [
    'FeedbackAnalyzer',
    'FeedbackStrategy',
    'SentenceGenerator',
    'SentenceParams',
]
