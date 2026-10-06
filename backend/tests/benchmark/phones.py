"""ARPAbet to IPA helpers and phone-position mapping for phone-level scoring.

speechocean762 labels canonical phones in ARPAbet with stress digits. Production G2P
emits IPA through eng_to_ipa. With WWAI_G2P_STRICT off it is one codepoint per phoneme.
With it on it is longest-match (tokenize_ipa), with "<unk>" for OOV words and no symbol
aliasing, so ʧ/ʤ stay ligatures. WWAI_PHONEME_NORMALIZATION never touches G2P output. It
only rewrites the recognized phones (ʧ to tʃ, ʤ to dʒ, y to j, bare a/e/o folded), which
gt_error_flags sees through `actual`.

Mapping works on characters, so it holds for either tokenization. When strict mode joins
characters from two canonical phones into one token (D R AO IH NG gives "ɔɪ"), both
canonical phones map to that one system phone and share its error flag, which matches
how production scores it.
"""

from __future__ import annotations

from . import common  # noqa: F401  (puts backend/ on sys.path)
from core.gt_alignment import align_sequences

# Matches eng_to_ipa's conventions, checked against eng_to_ipa.convert in the tests.
# AH is ə in every stress position, ER is ər, CH and JH use the ʧ/ʤ ligatures, Y is j.
ARPABET_TO_IPA = {
    "AA": "ɑ", "AE": "æ", "AH": "ə", "AO": "ɔ", "AW": "aʊ", "AY": "aɪ",
    "B": "b", "CH": "ʧ", "D": "d", "DH": "ð", "EH": "ɛ", "ER": "ər",
    "EY": "eɪ", "F": "f", "G": "g", "HH": "h", "IH": "ɪ", "IY": "i",
    "JH": "ʤ", "K": "k", "L": "l", "M": "m", "N": "n", "NG": "ŋ",
    "OW": "oʊ", "OY": "ɔɪ", "P": "p", "R": "r", "S": "s", "SH": "ʃ",
    "T": "t", "TH": "θ", "UH": "ʊ", "UW": "u", "V": "v", "W": "w",
    "Y": "j", "Z": "z", "ZH": "ʒ",
}


def arpabet_to_ipa(phone: str) -> str:
    base = phone.strip().upper().rstrip("012")
    try:
        return ARPABET_TO_IPA[base]
    except KeyError:
        raise ValueError(f"unknown ARPAbet phone {phone!r}") from None


def canonical_ipa(phones) -> list[str]:
    return [arpabet_to_ipa(p) for p in phones]


def _chars(tokens) -> tuple[list[str], list[int]]:
    chars: list[str] = []
    owners: list[int] = []
    for index, token in enumerate(tokens):
        if token.startswith("<"):  # strict G2P's "<unk>" carries no sounds
            continue
        for ch in token:
            chars.append(ch)
            owners.append(index)
    return chars, owners


def g2p_agrees(canonical, system) -> bool:
    """True when G2P produced the same sounds as the expert canonical phones."""
    return "".join(_chars(canonical)[0]) == "".join(_chars(system)[0])


def map_canonical_to_system(canonical, system) -> list[list[int]]:
    """For each canonical phone, the indices of the system phones aligned to it."""
    c_chars, c_owner = _chars(canonical)
    s_chars, s_owner = _chars(system)
    mapping = [set() for _ in canonical]
    i = j = 0
    for op, _gt, _pred in align_sequences(c_chars, s_chars):
        if op in ("match", "substitution"):
            mapping[c_owner[i]].add(s_owner[j])
            i += 1
            j += 1
        elif op == "deletion":
            i += 1
        else:  # insertion
            j += 1
    return [sorted(m) for m in mapping]


def gt_error_flags(expected, actual) -> list[bool]:
    """Per expected phoneme, True when production's alignment marks it wrong or missing.

    Uses the same Levenshtein alignment that fills each word's ``missed`` and
    ``substituted`` lists (gt_alignment.align_sequences is behaviorally identical to
    process_audio.align_sequences), so positions agree with what production reported.
    """
    flags = []
    for op, _gt, _pred in align_sequences(list(expected), list(actual)):
        if op != "insertion":
            flags.append(op != "match")
    return flags
