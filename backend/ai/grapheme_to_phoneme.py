#idk why I needed to do this this is gonna be a very simple program
# from g2p_en import G2p
import eng_to_ipa as G2p


def grapheme_to_phoneme(grapheme) -> list[tuple]:
    """
    Converts a string of graphemes into phonemes by removing stress markers and
    returning a list of (word, list of individual phonemes).
    """
    unfiltered_phonemes = G2p.convert(grapheme)
    normalized = unfiltered_phonemes.split(" ")
    output = []
    for word, phonemes in zip(grapheme.split(" "), normalized):
        output.append((word, list(phonemes.replace("ˈ","").replace("ˌ","").replace("*","").replace(",","").replace("'","")))) # remove stress markers
    return output


if __name__ == "__main__":
    print(grapheme_to_phoneme("hello world"))
    # extractor = PhonemeExtractor("speech31/wav2vec2-large-english-phoneme-v2", lambda x: x)
    # print(audio_recording.record_and_process_pronunciation("hello world", extraction_model=extractor))