"""
Grapheme to Phoneme Module

Converts graphemes (written letters) to phonemes (sounds) and provides
mapping capabilities to connect spelling patterns to pronunciation.
"""

import eng_to_ipa as G2p
from typing import Optional, List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)


def grapheme_to_phoneme(grapheme) -> list[tuple]:
    """
    Converts a string of graphemes into phonemes by removing stress markers and
    returning a list of (word, list of individual phonemes).
    """
    unfiltered_phonemes = G2p.convert(grapheme)
    normalized = unfiltered_phonemes.split(" ")
    output = []
    for word, phonemes in zip(grapheme.split(" "), normalized):
        output.append(
            (
                word,
                list(
                    phonemes.replace("ˈ", "")
                    .replace("ˌ", "")
                    .replace("*", "")
                    .replace(",", "")
                    .replace("'", "")
                ),
            )
        )  # remove stress markers
    return output


class GraphemePhonemeMapper:
    """
    Maps between graphemes (spelling patterns) and phonemes (sounds).
    
    This class helps connect pronunciation errors to their spelling representations,
    enabling pedagogically effective feedback that teaches both sound and spelling.
    """
    
    # Common English grapheme-to-phoneme patterns
    GRAPHEME_PATTERNS = {
        # Digraphs - two letters, one sound
        'ch': ['tʃ'],           # chat, chair
        'sh': ['ʃ'],            # ship, shell
        'th': ['θ', 'ð'],       # think (θ), this (ð)
        'ph': ['f'],            # phone, photo
        'gh': ['f', 'g', ''],   # laugh (f), ghost (g), night (silent)
        'wh': ['w', 'hw'],      # what, who
        'ng': ['ŋ'],            # sing, ring
        'ck': ['k'],            # back, sick
        
        # Consonant clusters
        'qu': ['k', 'w'],       # quick (makes k+w sound)
        'tch': ['tʃ'],          # catch, match
        
        # Vowel teams
        'ea': ['iː', 'ɛ'],      # eat (iː), bread (ɛ)
        'ee': ['iː'],           # see, tree
        'oo': ['uː', 'ʊ'],      # food (uː), book (ʊ)
        'ai': ['eɪ'],           # rain, mail
        'ay': ['eɪ'],           # day, play
        'oi': ['ɔɪ'],           # coin, oil
        'oy': ['ɔɪ'],           # boy, toy
        'ou': ['aʊ', 'uː'],     # out (aʊ), group (uː)
        'ow': ['aʊ', 'oʊ'],     # cow (aʊ), snow (oʊ)
        'au': ['ɔː'],           # author, cause
        'aw': ['ɔː'],           # saw, draw
        
        # R-controlled vowels
        'ar': ['ɑr'],           # car, star
        'er': ['ɜr'],           # her, term
        'ir': ['ɜr'],           # bird, first
        'or': ['ɔr'],           # for, corn
        'ur': ['ɜr'],           # turn, burn
        
        # Single letters (common sounds)
        'a': ['æ', 'eɪ', 'ɑ'],  # cat, cake, father
        'e': ['ɛ', 'iː'],       # bed, me
        'i': ['ɪ', 'aɪ'],       # sit, I
        'o': ['ɒ', 'oʊ'],       # hot, go
        'u': ['ʌ', 'uː'],       # cup, blue
        'y': ['j', 'aɪ', 'ɪ'],  # yes, my, happy
    }
    
    # Example words for each grapheme
    EXAMPLE_WORDS = {
        'ch': ['chat', 'chair', 'chop', 'cheese'],
        'sh': ['ship', 'shell', 'shop', 'fish'],
        'th': ['think', 'this', 'that', 'path'],
        'ph': ['phone', 'photo', 'graph'],
        'qu': ['quick', 'queen', 'quit', 'quilt'],
        'ea': ['eat', 'bread', 'read', 'head'],
        'oo': ['food', 'book', 'moon', 'look'],
        'ai': ['rain', 'mail', 'train', 'tail'],
        'ng': ['sing', 'ring', 'long', 'song'],
        'ck': ['back', 'sick', 'duck', 'rock'],
    }
    
    def __init__(self):
        """Initialize the grapheme-phoneme mapper."""
        pass
    
    def find_grapheme_for_phoneme(
        self,
        word: str,
        target_phoneme: str,
        word_phonemes: List[str]
    ) -> Optional[str]:
        """
        Find which grapheme (spelling pattern) produces the target phoneme in a word.
        
        This is a heuristic-based approach that looks for common patterns.
        
        Args:
            word: The written word (e.g., 'quick')
            target_phoneme: The phoneme to find (e.g., 'w')
            word_phonemes: List of phonemes in the word (e.g., ['k', 'w', 'ɪ', 'k'])
            
        Returns:
            The grapheme that produces the phoneme, or None if not found
            
        Example:
            find_grapheme_for_phoneme('quick', 'w', ['k', 'w', 'ɪ', 'k']) -> 'qu'
        """
        word_lower = word.lower()
        
        # Try to find the phoneme's position in the word
        try:
            phoneme_index = word_phonemes.index(target_phoneme)
        except ValueError:
            logger.warning(f"Phoneme '{target_phoneme}' not found in word phonemes: {word_phonemes}")
            return None
        
        # Check multi-character graphemes first (longest to shortest)
        for grapheme, phoneme_list in sorted(
            self.GRAPHEME_PATTERNS.items(),
            key=lambda x: len(x[0]),
            reverse=True
        ):
            if target_phoneme in phoneme_list and grapheme in word_lower:
                # Check if this grapheme is at a reasonable position
                grapheme_pos = word_lower.find(grapheme)
                
                # For multi-character graphemes, check if position makes sense
                if len(grapheme) > 1:
                    # Rough heuristic: grapheme position should be near phoneme position
                    if grapheme_pos >= 0:
                        return grapheme
        
        # Fall back to single character if no multi-char match
        # Try to find the character at the approximate position
        if phoneme_index < len(word_lower):
            char = word_lower[phoneme_index]
            if char in self.GRAPHEME_PATTERNS:
                if target_phoneme in self.GRAPHEME_PATTERNS[char]:
                    return char
        
        # No clear mapping found
        logger.debug(f"No grapheme mapping found for phoneme '{target_phoneme}' in word '{word}'")
        return None
    
    def get_example_words(self, grapheme: str, limit: int = 4) -> List[str]:
        """
        Get example words featuring the grapheme.
        
        Args:
            grapheme: The grapheme to find examples for
            limit: Maximum number of examples to return
            
        Returns:
            List of example words
        """
        examples = self.EXAMPLE_WORDS.get(grapheme, [])
        return examples[:limit]
    
    def get_phoneme_description(self, grapheme: str, phoneme: str) -> str:
        """
        Generate a natural language description of how a grapheme makes a sound.
        
        Args:
            grapheme: The grapheme (e.g., 'qu', 'th', 'ch')
            phoneme: The phoneme it produces
            
        Returns:
            Natural language description
            
        Example:
            get_phoneme_description('qu', 'kw') -> "The letters 'qu' make a 'kw' sound"
        """
        # Map IPA phonemes to more readable descriptions
        phoneme_descriptions = {
            'θ': 'soft th',
            'ð': 'voiced th',
            'ʃ': 'sh',
            'tʃ': 'ch',
            'dʒ': 'j',
            'ŋ': 'ng',
            'k': 'k',
            'w': 'w',
        }
        
        # Get readable phoneme
        readable_phoneme = phoneme_descriptions.get(phoneme, phoneme)
        
        # Generate description
        if len(grapheme) > 1:
            return f"The letters '{grapheme}' make a '{readable_phoneme}' sound"
        else:
            return f"The letter '{grapheme}' makes a '{readable_phoneme}' sound"
    
    def get_grapheme_patterns_for_phoneme(self, phoneme: str) -> List[str]:
        """
        Get all graphemes that can produce a given phoneme.
        
        Args:
            phoneme: The target phoneme (IPA format)
            
        Returns:
            List of graphemes that can produce this phoneme
        """
        matching_graphemes = []
        for grapheme, phoneme_list in self.GRAPHEME_PATTERNS.items():
            if phoneme in phoneme_list:
                matching_graphemes.append(grapheme)
        return matching_graphemes


if __name__ == "__main__":
    print(grapheme_to_phoneme("hello world"))
    # extractor = PhonemeExtractor("speech31/wav2vec2-large-english-phoneme-v2", lambda x: x)
    # print(audio_recording.record_and_process_pronunciation("hello world", extraction_model=extractor))
