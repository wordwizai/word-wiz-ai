# THIS FILE IS FOR THE FORMATION OF THE DATASET


import csv
import os
import eng_to_ipa
from evaluation.accuracy_metrics import compute_phoneme_error_rate

def clean_text(text: str) -> str:
    """
    Removes periods and apostrophes from the text.

    Args:
        text (str): Input text.

    Returns:
        str: Cleaned text without periods and apostrophes.
    """
    return text.replace('.', '').replace("ˈ", '')

def clean_phonemes(phonemes: str) -> str:
    """
    Removes asterisks from the phoneme output.

    Args:
        phonemes (str): Input phoneme string.

    Returns:
        str: Cleaned phoneme string.
    """
    return phonemes.replace('*', '')

def read_original_sentences(csv_filepath: str) -> list[tuple[str, str]]:
    """
    Reads original and altered sentences from a CSV file.

    Args:
        csv_filepath (str): Path to the CSV file.

    Returns:
        list[tuple[str, str]]: List of tuples containing original and altered sentences.
    """
    sentences = []
    with open(csv_filepath, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            if row:  # Ensure the row is not empty
                sentences.append((row[0], row[1]))  # Assuming original and altered sentences are in the first two columns
    return sentences

def create_validation_dataset(output_csv_path, num_items=50):
    """
    Creates a validation dataset with consistent phoneme error patterns.
    
    Args:
        output_csv_path (str): Path to save the validation dataset.
        num_items (int): Minimum number of items to include.
    """
    # Define common phoneme error patterns with expanded examples (20+ per pattern)
    error_patterns = [
        # Format: (phoneme, replacement, example_words)
        ("/k/", "/t/", [
            "cat/tat", "cake/take", "card/tard", "cap/tap", "corn/torn", 
            "key/tea", "can/tan", "cool/tool", "kite/tight", "cook/toot",
            "kit/tit", "back/bat", "dock/dot", "luck/lut", "make/mate",
            "pack/pat", "kick/tit", "book/boot", "keep/teep", "peak/peat",
            "know/tow", "king/ting", "crab/tab", "craft/taft", "creek/treat"
        ]),
        ("/s/", "/f/", [
            "sun/fun", "seat/feat", "pass/paff", "sock/fock", "say/fay",
            "sand/fand", "sink/fink", "safe/fafe", "soap/foap", "suit/foot",
            "six/fix", "sing/fing", "saw/faw", "sea/fee", "self/felf",
            "sick/fick", "sell/fell", "sad/fad", "soon/foon", "seed/feed",
            "sit/fit", "sort/fort", "smile/fmile", "slow/flow", "serve/ferve"
        ]),
        ("/ʃ/", "/s/", [
            "ship/sip", "shop/sop", "fish/fiss", "wish/wiss", "brush/bruss",
            "shell/sell", "share/sare", "wash/wass", "cash/cass", "dish/diss",
            "sheep/seep", "shake/sake", "show/so", "shine/sine", "crush/cruss",
            "shall/sall", "shore/sore", "shut/sut", "push/puss", "flash/flass",
            "fresh/fress", "sharp/sarp", "shoot/soot", "shape/sape", "shave/save"
        ]),
        ("/r/", "/w/", [
            "red/wed", "run/wun", "very/vewy", "frog/fwog", "train/twain",
            "rate/wait", "right/wight", "room/woom", "race/wace", "rope/wope",
            "rain/wain", "reach/weach", "ride/wide", "rest/west", "read/wead",
            "road/woad", "risk/wisk", "roll/woll", "rat/wat", "rock/wock",
            "real/weal", "rent/went", "raw/waw", "rich/wich", "round/wound"
        ]),
        ("/θ/", "/f/", [
            "thin/fin", "mouth/mouf", "thumb/fumb", "thief/fief", "thick/fick",
            "path/paf", "think/fink", "thank/fank", "third/fird", "thaw/faw",
            "theme/feme", "north/norf", "earth/earf", "south/souf", "three/free",
            "throw/frow", "thrill/frill", "thread/fred", "thrive/frive", "throne/frone",
            "growth/groff", "throb/frob", "thought/fought", "tooth/toof", "theory/feory"
        ]),
        ("/ð/", "/d/", [
            "the/de", "then/den", "mother/mudder", "brother/brudder", "that/dat",
            "this/dis", "there/dere", "they/dey", "those/dose", "these/dese",
            "other/udder", "father/fadder", "weather/wedder", "leather/ledder", "either/eider",
            "rather/radder", "gather/gadder", "together/togedder", "clothing/cloding", "feather/fedder",
            "worthy/wordy", "further/furder", "northern/nordern", "soothe/sood", "bathe/bade"
        ]),
        ("/b/", "/p/", [
            "bat/pat", "big/pig", "bad/pad", "bus/pus", "bag/pag",
            "book/pook", "bin/pin", "ball/pall", "back/pack", "best/pest",
            "boy/poy", "bed/ped", "bee/pee", "burn/purn", "boat/poat",
            "box/pox", "bike/pike", "buy/py", "bear/pear", "bright/pright",
            "bold/pold", "belly/pelly", "berry/perry", "both/poth", "bake/pake"
        ]),
        ("/t/", "/d/", [
            "tie/die", "hat/had", "tent/dent", "team/deam", "top/dop",
            "two/do", "ten/den", "time/dime", "tell/dell", "town/down",
            "tree/dree", "take/dake", "talk/dock", "tip/dip", "true/drew",
            "trail/drail", "train/drain", "taste/daste", "tool/dool", "tail/dail",
            "tape/dape", "tune/dune", "tear/dear", "try/dry", "tame/dame"
        ]),
        ("/v/", "/b/", [
            "van/ban", "very/bery", "five/fibe", "save/sabe", "over/ober",
            "have/habe", "voice/boice", "vote/boat", "vest/best", "view/biew",
            "vase/base", "vain/bain", "value/balue", "vast/bast", "veil/beil",
            "vet/bet", "vile/bile", "vibe/bibe", "verb/berb", "veer/beer",
            "vine/bine", "void/boid", "vary/bary", "vow/bow", "vector/bector"
        ]),
        ("/z/", "/s/", [
            "zoo/soo", "buzz/buss", "fuzz/fuss", "zone/sone", "freeze/freese",
            "zigzag/sigsag", "zero/sero", "lazy/lasy", "crazy/crasy", "zoom/soom",
            "zap/sap", "zip/sip", "zest/sest", "zombie/sombie", "zebra/sebra",
            "zeal/seal", "size/sise", "prize/prise", "doze/dose", "maze/mase",
            "haze/hase", "gaze/gase", "jazz/jass", "dizzy/dissy", "whiz/whiss"
        ]),
        # Vowel error patterns
        ("/i/", "/ɪ/", [
            "seat/sit", "feel/fill", "sheet/shit", "leave/live", "peace/piss",
            "heal/hill", "wheel/will", "deep/dip", "sleep/slip", "beam/bim",
            "cheap/chip", "sheep/ship", "teen/tin", "seen/sin", "beat/bit",
            "neat/knit", "heat/hit", "reach/rich", "leak/lick", "meal/mill",
            "peel/pill", "steel/still", "meet/mit", "feed/fid", "read/rid"
        ]),
        ("/u/", "/ʊ/", [
            "pool/pull", "fool/full", "Luke/look", "cooed/could", "boot/book",
            "food/foot", "root/root", "noon/nook", "suit/soot", "choose/chuss",
            "rude/rood", "nude/nood", "mood/mudd", "goof/guff", "loose/luss",
            "boost/bust", "shoot/shut", "goose/guss", "proof/pruf", "stool/stull",
            "cool/cull", "tool/tull", "booed/budd", "hoot/hutt", "zoom/zumm"
        ]),
        ("/æ/", "/ɛ/", [
            "bat/bet", "cat/Ket", "hat/het", "sad/sed", "bad/bed",
            "mad/med", "pan/pen", "tan/ten", "man/men", "fan/fen",
            "bag/beg", "lag/leg", "tag/teg", "jam/jem", "ham/hem",
            "lamb/lemb", "back/beck", "stack/stek", "sack/seck", "tap/tep",
            "cap/kep", "map/mep", "nap/nep", "pad/ped", "had/hed"
        ]),
        ("/ɑ/", "/ʌ/", [
            "cot/cut", "pot/putt", "not/nut", "shot/shut", "hot/hut",
            "got/gut", "dot/dut", "tot/tut", "rot/rut", "spot/sput",
            "lot/lut", "dock/duck", "rock/ruck", "sock/suck", "block/bluck",
            "flock/fluck", "shock/shuck", "knock/nuck", "mop/mup", "pop/pup",
            "top/tup", "hop/hup", "stop/stup", "cop/cup", "drop/drup"
        ]),
        ("/eɪ/", "/e/", [
            "mate/met", "rate/ret", "date/det", "late/let", "fate/fet",
            "hate/het", "gate/get", "bake/bek", "take/tek", "lake/lek",
            "make/mek", "sake/sek", "wake/wek", "fade/fed", "made/med",
            "wade/wed", "raid/red", "laid/led", "paid/ped", "maid/med",
            "pain/pen", "gain/gen", "rain/ren", "main/men", "lane/len"
        ]),
        ("/aɪ/", "/eɪ/", [
            "time/tame", "dine/dane", "mine/mane", "fine/fane", "line/lane",
            "wide/wade", "ride/rade", "side/sade", "hide/hade", "tide/tade",
            "pike/pake", "like/lake", "hike/hake", "bike/bake", "wipe/wape",
            "ripe/rape", "type/tape", "right/rate", "light/late", "night/nate",
            "sight/sate", "bright/brate", "flight/flate", "might/mate", "fight/fate"
        ])
    ]
    
    # Create sentence templates that can showcase these errors
    templates = [
        "The {0} is very {1}.",
        "I like my {0} and my {1}.",
        "We can {0} to the {1}.",
        "She has a {0} in her {1}.",
        "The boy {0} with the {1}.",
        "Look at the {0} next to the {1}.",
        "Can you {0} the {1} for me?",
        "My {0} is on the {1}.",
        "The {0} and the {1} are friends.",
        "I {0} to {1} every day.",
        "They found a {0} near the {1}.",
        "Please put the {0} beside the {1}.",
        "I heard the {0} made a noise like a {1}.",
        "We should {0} before we {1}.",
        "Did you see the {0} or the {1} first?"
    ]
    
    rows = []
    idx = 1
    
    # Generate sentences with each error pattern
    for phoneme, replacement, word_pairs in error_patterns:
        for i in range(max(5, num_items // len(error_patterns))):
            # Pick word pairs and template
            word_pair1 = word_pairs[i % len(word_pairs)]
            word_pair2 = word_pairs[(i + 7) % len(word_pairs)]  # Use offset to avoid repeating same pairs
            template = templates[i % len(templates)]
            
            # Create original sentence
            original_word1 = word_pair1.split('/')[0]
            original_word2 = word_pair2.split('/')[0]
            original_sentence = template.format(original_word1, original_word2)
            
            # Create altered sentence with phoneme error
            altered_word1 = word_pair1.split('/')[1]
            altered_word2 = word_pair2.split('/')[0]  # Keep one word correct
            altered_sentence = template.format(altered_word1, original_word2)
            
            # Get IPA for both
            original_cleaned = clean_text(original_sentence)
            altered_cleaned = clean_text(altered_sentence)
            original_phonemes = clean_phonemes(eng_to_ipa.convert(original_cleaned))
            altered_phonemes = clean_phonemes(eng_to_ipa.convert(altered_cleaned))
            
            # Calculate PER
            per = compute_phoneme_error_rate(original_phonemes.split(), altered_phonemes.split())
            
            rows.append([str(idx), original_cleaned, altered_cleaned, 
                         original_phonemes, altered_phonemes, str(per)])
            idx += 1
    
    # Write to CSV
    with open(output_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Key", "Original Sentence", "Altered Sentence", 
                         "Original Phonemes", "Altered Phonemes", "PER"])
        writer.writerows(rows)
    
    print(f"Created validation dataset with {len(rows)} items")
    return rows

# def write_phoneme_sentences(input_csv: str, output_csv: str):
#     """
#     Converts sentences to phonemes, calculates PER, and writes them to a new CSV file.

#     Args:
#         input_csv (str): Path to the input CSV file.
#         output_csv (str): Path to the output CSV file.
#     """
#     sentences = read_original_sentences(input_csv)
#     with open(output_csv, mode='w', encoding='utf-8', newline='') as file:
#         writer = csv.writer(file)
#         writer.writerow(["Key", "Original Sentence", "Altered Sentence", "Original Phonemes", "Altered Phonemes", "PER"])  # Header row
#         for idx, (original, altered) in enumerate(sentences[2:], start=1):
#             original_cleaned = clean_text(original)
#             altered_cleaned = clean_text(altered)
#             original_phonemes = clean_phonemes(eng_to_ipa.convert(original_cleaned))
#             altered_phonemes = clean_phonemes(eng_to_ipa.convert(altered_cleaned))
#             per = compute_phoneme_error_rate(original_phonemes.split(), altered_phonemes.split())
#             writer.writerow([f"{idx}", original_cleaned, altered_cleaned, original_phonemes, altered_phonemes, per])

if __name__ == "__main__":
    # input_csv_path = os.path.join(os.getcwd(), "dataset/originalscentences.csv")
    output_csv_path = os.path.join(os.getcwd(), "dataset/phoneme_sentences.csv")
    create_validation_dataset(output_csv_path)
    print(f"Phoneme sentences written to {output_csv_path}")