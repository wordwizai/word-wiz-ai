# IPA to ARPAbet Mapping
ipa_to_arpabet_dict = {
    'p': 'P', 'b': 'B', 't': 'T', 'd': 'D', 'k': 'K', 'g': 'G',
    'f': 'F', 'v': 'V', 'θ': 'TH', 'ð': 'DH', 's': 'S', 'z': 'Z',
    'ʃ': 'SH', 'ʒ': 'ZH', 'tʃ': 'CH', 'dʒ': 'JH', 'm': 'M', 'n': 'N',
    'ŋ': 'NG', 'l': 'L', 'r': 'R', 'j': 'Y', 'w': 'W', 'h': 'HH',
    'i': 'IY', 'ɪ': 'IH', 'e': 'EY', 'ɛ': 'EH', 'æ': 'AE', 'ɑ': 'AA',
    'ɔ': 'AO', 'o': 'OW', 'u': 'UW', 'ʊ': 'UH', 'ə': 'AH', 'ʌ': 'UH',
    'aɪ': 'AY', 'aʊ': 'AW', 'ɔɪ': 'OY'
}

# Convert ARPAbet to IPA
def ipa2arpa(ipa):
    return ipa_to_arpabet_dict[ipa]