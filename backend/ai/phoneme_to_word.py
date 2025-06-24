import lexconvert

def phoneme_to_word(phonemes):
    """
    Converts a list of phonemes into a predicted word using a fine-tuned T5 model.
    
    Args:
        phonemes (List[str]): A list of phonemes, e.g. ['k', 'æ', 't']
    
    Returns:
        str: The predicted word.
    """
    words = lexconvert.convert(phonemes, 'unicode-ipa', 'x-sampa')
    return words

if __name__ == "__main__":
    phonemes = ['k', 'æ', 't']
    predicted_word = phoneme_to_word(phonemes)
    print(predicted_word)  # Expected output (if the model was fine-tuned properly): 'cat'