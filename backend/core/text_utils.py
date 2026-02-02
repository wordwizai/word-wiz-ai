"""
Text processing utilities.

Common text manipulation functions used across the application.
"""

import re


def contains_ssml_tags(text: str) -> bool:
    """
    Check if text contains SSML tags.

    Args:
        text: Text to check for SSML tags.

    Returns:
        bool: True if text contains SSML tags, False otherwise.

    Examples:
        >>> contains_ssml_tags("Hello world")
        False
        >>> contains_ssml_tags("<phoneme>Hello</phoneme>")
        True
        >>> contains_ssml_tags("Hello <break time='1s'/> world")
        True
    """
    # Look for common SSML tags
    ssml_pattern = r"<(phoneme|emphasis|break|say-as|prosody|voice|speak)\b[^>]*>"
    return bool(re.search(ssml_pattern, text, re.IGNORECASE))
