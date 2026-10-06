import unittest

from tests.benchmark import phones as P


class TestArpabet(unittest.TestCase):
    def test_strips_stress(self):
        self.assertEqual(P.arpabet_to_ipa("IY0"), "i")
        self.assertEqual(P.arpabet_to_ipa("AH1"), "ə")

    def test_unknown_phone(self):
        with self.assertRaises(ValueError):
            P.arpabet_to_ipa("QQ")

    def test_matches_eng_to_ipa(self):
        import eng_to_ipa

        cases = {
            "cat": "K AE1 T", "church": "CH ER1 CH", "judge": "JH AH1 JH", "boy": "B OY1",
            "house": "HH AW1 S", "yes": "Y EH1 S", "measure": "M EH1 ZH ER0", "thin": "TH IH1 N",
            "sing": "S IH1 NG", "food": "F UW1 D", "go": "G OW1", "day": "D EY1", "my": "M AY1",
            "book": "B UH1 K", "father": "F AA1 DH ER0", "caught": "K AO1 T", "this": "DH IH1 S",
            "ship": "SH IH1 P", "see": "S IY1", "hat": "HH AE1 T",
        }
        for word, arpa in cases.items():
            with self.subTest(word=word):
                expected = eng_to_ipa.convert(word).replace("ˈ", "").replace("ˌ", "")
                self.assertEqual("".join(P.canonical_ipa(arpa.split())), expected)


class TestMapping(unittest.TestCase):
    def test_legacy_tokenization_splits_diphthongs(self):
        self.assertEqual(P.map_canonical_to_system(["m", "aɪ"], ["m", "a", "ɪ"]), [[0], [1, 2]])

    def test_normalized_tokenization(self):
        self.assertEqual(P.map_canonical_to_system(["m", "aɪ"], ["m", "aɪ"]), [[0], [1]])

    def test_missing_system_phone_is_unmapped(self):
        self.assertEqual(P.map_canonical_to_system(["k", "æ", "t"], ["k", "æ"]), [[0], [1], []])

    def test_unknown_marker_carries_no_sounds(self):
        self.assertEqual(P.map_canonical_to_system(["k", "æ", "t"], ["<unk>"]), [[], [], []])

    def test_g2p_agrees_ignores_tokenization(self):
        self.assertTrue(P.g2p_agrees(["m", "aɪ"], ["m", "a", "ɪ"]))
        self.assertFalse(P.g2p_agrees(["m", "aɪ"], ["m", "a"]))


class TestErrorFlags(unittest.TestCase):
    def test_substitution_and_deletion(self):
        self.assertEqual(P.gt_error_flags(["k", "æ", "t"], ["k", "ɛ"]), [False, True, True])

    def test_deleted_word(self):
        self.assertEqual(P.gt_error_flags(["k", "æ", "t"], []), [True, True, True])

    def test_insertions_are_not_expected_phones(self):
        self.assertEqual(P.gt_error_flags(["k", "æ", "t"], ["k", "æ", "æ", "t"]), [False, False, False])


if __name__ == "__main__":
    unittest.main()
