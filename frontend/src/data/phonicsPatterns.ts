// Programmatic phonics-pattern practice data.
//
// Each entry powers a page at /practice-words/[slug] built from real,
// parent-facing teaching guidance plus an age-appropriate word list and
// decodable sample sentences. Content is organized into five categories:
// word families (rimes), digraphs, blends, vowel teams, and r-controlled
// vowels. See frontend/src/components/PracticePageTemplate.tsx for how
// this data is rendered, and frontend/src/pages/PracticeWordsHub.tsx for
// the category index page.

export type PatternCategory =
  | "word-family"
  | "digraph"
  | "blend"
  | "vowel-team"
  | "r-controlled";

export interface PhonicsPattern {
  /** URL slug, used at /practice-words/[slug] */
  slug: string;
  /** The raw letter pattern, e.g. "at", "sh", "bl", "ai", "ar" */
  pattern: string;
  /** Human-readable name shown in headings, e.g. "-at Word Family" */
  displayName: string;
  category: PatternCategory;
  /** Typical grade/age range this pattern is taught, e.g. "Kindergarten" */
  gradeLevel: string;
  /** 10-25 real, age-appropriate words containing the pattern */
  words: string[];
  /** 3-5 short, fully decodable sample sentences using the word list */
  sampleSentences: string[];
  /** 2-3 paragraphs of real parent-facing teaching guidance */
  teachingNotes: string[];
  /** Common mistakes children make with this pattern */
  commonErrors: string[];
  /** Slugs of related patterns for internal linking */
  relatedSlugs: string[];
}

export const categoryLabels: Record<PatternCategory, string> = {
  "word-family": "Word Families",
  digraph: "Digraphs",
  blend: "Consonant Blends",
  "vowel-team": "Vowel Teams",
  "r-controlled": "R-Controlled Vowels",
};

export const categoryDescriptions: Record<PatternCategory, string> = {
  "word-family":
    "Word families (or rimes) group words that share the same vowel-and-ending sound, like -at in cat, hat, and mat. Because only the first sound changes, they are the fastest way for beginning readers to unlock dozens of words from one pattern.",
  digraph:
    "Digraphs are two letters that combine to make one brand-new sound, like the 'sh' in ship or the 'th' in thin. Neither letter keeps its usual sound, which is why digraphs need to be taught explicitly rather than sounded out letter by letter.",
  blend:
    "Consonant blends are two or three consonants that sit next to each other and keep their own individual sounds, said quickly together, like the 'bl' in black or the 'st' in stop. Unlike digraphs, each letter in a blend is still audible.",
  "vowel-team":
    "Vowel teams are two letters that work together to make one vowel sound, often a long vowel, like the 'ai' in rain or the 'oa' in boat. English has dozens of these teams, and many share the same sound, which is what makes them tricky.",
  "r-controlled":
    "R-controlled vowels (sometimes called 'bossy R') happen when a vowel is followed by the letter r, which changes the vowel's sound completely, like the 'ar' in car or the 'er' in her. Neither the vowel nor the r keeps its usual sound.",
};

export const phonicsPatterns: PhonicsPattern[] = [
  // ============================================================
  // WORD FAMILIES — short A
  // ============================================================
  {
    slug: "at-family",
    pattern: "at",
    displayName: "-at Word Family",
    category: "word-family",
    gradeLevel: "Kindergarten",
    words: [
      "cat", "hat", "bat", "mat", "rat", "sat", "fat", "pat",
      "vat", "that", "flat", "chat", "brat", "scat", "spat",
    ],
    sampleSentences: [
      "The cat sat on the mat.",
      "A fat rat ran to the vat.",
      "Pat has a flat hat.",
      "That cat can chat with a bat.",
    ],
    teachingNotes: [
      "The -at family is where most children take their very first steps into blending, and for good reason: every word follows the same consonant-vowel-consonant shape, with the short a sound /æ/ staying constant while only the beginning consonant changes. Once a child can read 'cat,' they already have the tools to read 'hat,' 'mat,' and 'sat' without learning anything new about the vowel — that transfer is the whole point of teaching word families instead of memorizing words one at a time.",
      "Start with a small set of three or four -at words and have your child swap just the first letter each time, saying the new word aloud before checking it against the page. Watch for kids who default to a memorized guess like 'cat' no matter what letter comes first — that is a sign they are pattern-matching the shape of the word rather than actually reading the beginning sound, and it is worth slowing down to isolate that first consonant sound before moving on.",
    ],
    commonErrors: [
      "Guessing 'cat' for every -at word regardless of the first letter",
      "Confusing short a /æ/ with short e, reading 'at' as 'et'",
      "Adding an extra vowel sound, saying 'ah-t' instead of blending smoothly into 'at'",
    ],
    relatedSlugs: ["an-family", "ap-family", "ack-family"],
  },
  {
    slug: "an-family",
    pattern: "an",
    displayName: "-an Word Family",
    category: "word-family",
    gradeLevel: "Kindergarten",
    words: [
      "can", "man", "pan", "ran", "tan", "van", "fan", "Dan",
      "plan", "than", "clan", "bran", "scan", "span",
    ],
    sampleSentences: [
      "The man ran with a fan.",
      "Can Dan fit in the van?",
      "I have a plan for the tan pan.",
      "A man can scan the can.",
    ],
    teachingNotes: [
      "The -an family sits right alongside -at as one of the first two or three rimes most kindergartners meet, and pairing them on purpose helps children notice that changing the last consonant (t versus n) changes the word family entirely, even though the vowel sound stays the same. This is a useful moment to explicitly point out that 'cat' and 'can' start the same but end differently, since children who are still guessing from shape alone often blur the two together.",
      "A good home activity is a simple word ladder: write 'can,' then ask your child to change one letter to make 'man,' then 'fan,' then 'van.' Say each new word together before writing it. If your child hesitates on the blend in 'plan' or 'scan,' that is normal — those are -an words with an extra consonant blend stacked on the front, and they are best practiced after the plain four-letter -an words feel automatic.",
    ],
    commonErrors: [
      "Mixing up the ending sounds in -at and -an words",
      "Dropping the second consonant in blend words like 'plan' or 'scan'",
      "Reading 'an' with a long a sound instead of the short /æ/",
    ],
    relatedSlugs: ["at-family", "ap-family", "and-family"],
  },
  {
    slug: "ap-family",
    pattern: "ap",
    displayName: "-ap Word Family",
    category: "word-family",
    gradeLevel: "Kindergarten",
    words: [
      "cap", "map", "nap", "tap", "lap", "gap", "rap", "sap",
      "clap", "flap", "snap", "trap", "wrap", "strap",
    ],
    sampleSentences: [
      "The cat can nap on my lap.",
      "Tap the map with your hand.",
      "Clap and snap for the trap.",
      "Dad has a cap and a strap.",
    ],
    teachingNotes: [
      "The -ap family is especially useful for practicing beginning blends because so many common -ap words start with two consonants: 'clap,' 'flap,' 'snap,' and 'trap' all belong here alongside the simpler 'cap' and 'map.' That mix makes -ap a natural bridge from plain CVC words to CCVC words with a consonant blend up front, so it is worth teaching after your child is solid on -at and -an rather than as a first family.",
      "When you get to the blend words, have your child say the two beginning consonant sounds slowly and separately first — /s/ then /n/ for 'snap' — before sliding them together and adding '-ap.' Kids who skip a sound in the blend (saying 'sap' for 'snap') usually just need more practice hearing both consonants distinctly before they are asked to read them.",
    ],
    commonErrors: [
      "Dropping the first consonant in a blend, reading 'snap' as 'nap'",
      "Reversing the blend order, saying 'sw-ap' sounds for 'swap'-like words",
      "Rushing through the vowel and landing on 'up' instead of 'ap'",
    ],
    relatedSlugs: ["at-family", "an-family", "amp-family"],
  },
  {
    slug: "ad-family",
    pattern: "ad",
    displayName: "-ad Word Family",
    category: "word-family",
    gradeLevel: "Kindergarten",
    words: [
      "bad", "dad", "had", "mad", "pad", "sad", "lad", "glad",
      "clad", "shad", "Chad", "Brad",
    ],
    sampleSentences: [
      "Dad is glad, not sad.",
      "The bad cat had a pad.",
      "I am mad about the sad ad.",
      "Chad had a bad day.",
    ],
    teachingNotes: [
      "The -ad family is short, but it earns its place early because 'dad,' 'bad,' 'sad,' 'mad,' and 'had' are among the highest-frequency words a beginning reader encounters in early decodable books and everyday conversation. Because the word list is smaller than -at or -an, this is a good family for building confidence quickly — most children can read all of the common -ad words within a single short session.",
      "One thing to watch for is confusion with -ed, since 'dad' and 'Ted' or 'bad' and 'bed' differ only in the vowel, and short a and short e are the two vowel sounds young children mix up most often. If your child swaps these, have them say the vowel sound in isolation first (/æ/ for a, /ɛ/ for e) with their mouth open wider for the a sound, then blend it into the full word.",
    ],
    commonErrors: [
      "Confusing short a and short e, reading 'bad' as 'bed'",
      "Skipping the ending consonant sound entirely",
      "Misreading 'glad' or 'clad' by dropping the first letter of the blend",
    ],
    relatedSlugs: ["at-family", "ag-family", "am-family"],
  },
  {
    slug: "ag-family",
    pattern: "ag",
    displayName: "-ag Word Family",
    category: "word-family",
    gradeLevel: "Kindergarten",
    words: [
      "bag", "tag", "rag", "wag", "sag", "gag", "nag", "lag",
      "flag", "drag", "brag", "shag", "stag", "snag",
    ],
    sampleSentences: [
      "The dog can wag its tag.",
      "Drag the bag with the flag.",
      "Do not brag or nag, Meg.",
      "The rag is in the bag.",
    ],
    teachingNotes: [
      "The -ag family gives children another chance to work with beginning blends ('flag,' 'drag,' 'brag,' 'snag') right alongside simple four-letter words ('bag,' 'tag,' 'wag'), which makes it a natural follow-up once -at and -ap feel comfortable. Because 'bag,' 'tag,' and 'flag' show up constantly in read-aloud picture books, mastering this family pays off quickly in real reading, not just in worksheet practice.",
      "A fun, low-prep activity is a real bag of small objects: put a few toys in a bag and have your child pull one out, then find or write its matching -ag rhyme if one exists, or simply practice reading a label you have written. Physically manipulating an actual bag while reading the word 'bag' gives young children a concrete anchor for an otherwise abstract print-to-sound connection.",
    ],
    commonErrors: [
      "Dropping the first consonant in blends like 'flag' or 'drag'",
      "Confusing short a with short o, reading 'bag' as closer to 'bog'",
      "Reading the whole word as a memorized sight word instead of decoding it",
    ],
    relatedSlugs: ["at-family", "ad-family", "ang-family"],
  },
  {
    slug: "am-family",
    pattern: "am",
    displayName: "-am Word Family",
    category: "word-family",
    gradeLevel: "Kindergarten",
    words: [
      "am", "ham", "jam", "ram", "Sam", "yam", "clam", "slam",
      "cram", "gram", "swam", "tram",
    ],
    sampleSentences: [
      "Sam am glad to eat ham and jam.",
      "The ram can slam the clam.",
      "I swam to get the yam.",
      "Cram the jam in the tram.",
    ],
    teachingNotes: [
      "The -am family is compact but valuable because 'am' itself is one of the very first sight words children meet ('I am'), and seeing it inside a full rime family helps them realize it decodes just like every other -am word instead of being a special exception. From there, food words like 'ham,' 'jam,' and 'yam' give parents an easy, low-stakes way to fold reading practice into breakfast or lunch conversation.",
      "Several common -am words start with a consonant blend — 'clam,' 'slam,' 'cram,' 'swam' — so this family is good blend practice once the plain three- and four-letter -am words are solid. As with other blend-heavy families, have your child say each beginning consonant sound distinctly before sliding into '-am,' and resist the urge to let them guess from the first letter alone.",
    ],
    commonErrors: [
      "Treating 'am' as an unrelated sight word instead of a decodable -am word",
      "Dropping a consonant in blends like 'swam' or 'clam'",
      "Confusing short a with short u, drifting toward 'um' sounds",
    ],
    relatedSlugs: ["at-family", "ad-family", "ap-family"],
  },
  {
    slug: "ab-family",
    pattern: "ab",
    displayName: "-ab Word Family",
    category: "word-family",
    gradeLevel: "Kindergarten",
    words: [
      "cab", "dab", "gab", "jab", "lab", "nab", "tab", "crab",
      "grab", "drab", "stab", "blab", "flab", "scab",
    ],
    sampleSentences: [
      "Grab the crab from the cab.",
      "Dad has a lab and a tab.",
      "The crab can jab and nab.",
      "Do not blab or gab in the lab.",
    ],
    teachingNotes: [
      "The -ab family follows the same pattern as -ad and -ag but introduces 'crab' and 'grab' as favorite, highly motivating words for young readers — animals and action verbs both tend to stick better than abstract words, so this family often lands well in beginning phonics sessions. Roughly half the common -ab words start with a two-letter blend, so treat this as blend practice rather than a purely plain-CVC family.",
      "Because 'cab,' 'lab,' and 'tab' are shorter and simpler, start there before moving to 'crab,' 'grab,' 'stab,' and 'scab.' If a child is confidently reading four-letter -ab words but stumbling only on the blend words, the issue is almost always the blend itself, not the -ab ending — go back to isolating the two beginning consonant sounds together before reattaching the rest of the word.",
    ],
    commonErrors: [
      "Skipping the second consonant in blends like 'crab' or 'grab'",
      "Confusing 'ab' with 'ob', drifting the vowel toward an o sound",
      "Losing the ending consonant sound and reading 'cab' as 'ca'",
    ],
    relatedSlugs: ["at-family", "ap-family", "ad-family"],
  },
  {
    slug: "ack-family",
    pattern: "ack",
    displayName: "-ack Word Family",
    category: "word-family",
    gradeLevel: "Kindergarten–Grade 1",
    words: [
      "back", "pack", "sack", "tack", "rack", "Jack", "black",
      "crack", "track", "snack", "stack", "quack", "shack",
    ],
    sampleSentences: [
      "Jack has a black pack.",
      "Pack a snack in the sack.",
      "The duck can quack on the track.",
      "Stack the rack by the shack.",
    ],
    teachingNotes: [
      "The -ack family introduces the 'ck' spelling of the /k/ sound, which English uses instead of a plain 'k' right after a short vowel at the end of a one-syllable word. This is a useful rule to name explicitly: 'ck' shows up after short vowels ('back,' 'pack'), while a plain 'k' shows up almost everywhere else, and pointing this out helps children generalize the pattern to other words later instead of treating each 'ck' word as a one-off to memorize.",
      "Many -ack words carry a beginning blend ('black,' 'crack,' 'track,' 'stack,' 'snack'), so this family works well as a next step after -ap and -ab. Since 'ck' always makes one single /k/ sound rather than two, remind your child not to try to sound out 'c' and 'k' separately — it is a single unit, much like the digraphs they will meet soon in patterns like 'sh' and 'ch.'",
    ],
    commonErrors: [
      "Trying to sound out 'c' and 'k' as two separate sounds instead of one",
      "Dropping the beginning blend consonant in words like 'black' or 'track'",
      "Confusing 'ack' with 'ock', drifting the vowel toward an o sound",
    ],
    relatedSlugs: ["at-family", "ang-family", "ank-family"],
  },
  {
    slug: "and-family",
    pattern: "and",
    displayName: "-and Word Family",
    category: "word-family",
    gradeLevel: "Grade 1",
    words: [
      "and", "band", "hand", "land", "sand", "grand", "brand",
      "stand", "bland",
    ],
    sampleSentences: [
      "Stand on the sand with your hand.",
      "The band will land on the grand stage.",
      "I have a brand new hand fan.",
      "We stand and clap for the band.",
    ],
    teachingNotes: [
      "The -and family is a step up in complexity because it ends in a two-consonant blend ('nd') rather than a single consonant, which means a child has to hold onto three separate sounds after the vowel before reaching the end of the word. Since 'and' is also one of the most frequent words in the English language, it is worth teaching this family fairly early even though it is technically harder than a plain CVC rime.",
      "Practice the ending blend in isolation first: say '-and' by itself several times, exaggerating the /n/ and /d/ as two distinct closing sounds, before attaching a beginning consonant. Words like 'stand,' 'brand,' and 'grand' then add a beginning blend on top of the ending blend, so save those for once 'band,' 'hand,' 'land,' and 'sand' are automatic.",
    ],
    commonErrors: [
      "Dropping the final /d/ sound and reading 'and' as 'an'",
      "Struggling to blend three consonants in words like 'stand' or 'brand'",
      "Reading 'and' correctly in isolation but stumbling when it starts a longer word",
    ],
    relatedSlugs: ["an-family", "ang-family", "ank-family"],
  },
  {
    slug: "ang-family",
    pattern: "ang",
    displayName: "-ang Word Family",
    category: "word-family",
    gradeLevel: "Grade 1",
    words: [
      "bang", "hang", "gang", "rang", "sang", "fang", "clang",
      "slang", "twang",
    ],
    sampleSentences: [
      "The bell rang with a loud bang.",
      "We sang a song and hung the swing.",
      "Hang the fang on the wall.",
      "The gang heard a clang and a twang.",
    ],
    teachingNotes: [
      "In the -ang family, the 'n' before 'g' changes the vowel sound slightly — it is nasalized, which is a fancy way of saying air moves through the nose while you say it — but children do not need the technical term to hear the difference. What matters practically is that 'ang' is one connected chunk that should be taught and practiced as a unit rather than sounded out letter by letter, much like '-ing' and '-ong.'",
      "This family pairs naturally with -ing, -ong, and -ung as the four 'nasal' rime families, and once a child has one of them down, the other three tend to come quickly because the pattern (vowel plus 'ng' as a single unit) is identical. If your child is decoding letter by letter and getting stuck between the n and the g, model reading the whole '-ang' chunk as one sound rather than two separate consonant sounds.",
    ],
    commonErrors: [
      "Trying to separate the 'n' and 'g' into two distinct sounds",
      "Confusing -ang with -ing or -ong when reading quickly",
      "Dropping the beginning blend in words like 'clang' or 'twang'",
    ],
    relatedSlugs: ["ack-family", "ank-family", "and-family"],
  },
  {
    slug: "ank-family",
    pattern: "ank",
    displayName: "-ank Word Family",
    category: "word-family",
    gradeLevel: "Grade 1",
    words: [
      "bank", "tank", "rank", "sank", "thank", "blank", "crank",
      "drank", "plank", "prank", "spank", "yank",
    ],
    sampleSentences: [
      "The tank sank by the bank.",
      "Thank you for the blank plank.",
      "I drank juice and played a prank.",
      "Yank the crank on the tank.",
    ],
    teachingNotes: [
      "Like -ang, the -ank family should be taught as a single nasalized chunk rather than three separate letter sounds, and it shows up in a surprising number of everyday words: 'bank,' 'thank,' 'tank,' and 'blank' are all common in early reading materials. Because 'thank' starts with the digraph 'th,' this family is a natural place to review digraphs at the same time you are practicing the rime.",
      "Many -ank words carry a beginning blend as well ('blank,' 'crank,' 'drank,' 'plank,' 'prank,' 'spank'), which makes this one of the more demanding word families on this list — a child is coordinating a beginning blend, a vowel, and a nasal ending blend all in one word. If -ank feels hard, back up to -an and -ang first and return to -ank once both of those are fluent.",
    ],
    commonErrors: [
      "Splitting the 'ank' chunk into separate n and k sounds",
      "Dropping a consonant from beginning blends like 'crank' or 'drank'",
      "Misreading 'thank' by treating 'th' as two separate letter sounds",
    ],
    relatedSlugs: ["ang-family", "and-family", "ack-family"],
  },
  {
    slug: "ash-family",
    pattern: "ash",
    displayName: "-ash Word Family",
    category: "word-family",
    gradeLevel: "Grade 1",
    words: [
      "cash", "dash", "mash", "sash", "wash", "gash", "trash",
      "flash", "crash", "smash", "splash", "stash",
    ],
    sampleSentences: [
      "Dash to wash the cash.",
      "The crash made a big splash.",
      "Mash the trash with a flash.",
      "Do not smash the sash.",
    ],
    teachingNotes: [
      "The -ash family combines a short vowel rime with the digraph 'sh,' so it is best taught after your child already recognizes 'sh' as a single sound on its own — otherwise they may try to sound out an 's' and an 'h' separately at the end of the word. Once 'sh' is solid, -ash behaves like any other rime family: swap the beginning sound and the rest stays constant.",
      "This family is unusually rich in blend words — 'trash,' 'flash,' 'crash,' 'smash,' 'splash,' and 'stash' all start with two or three consonants — which makes it excellent practice for children who have already mastered simpler families and are ready for a challenge. 'Splash' in particular is a three-consonant blend ('spl') and is worth celebrating as a milestone word once your child can read it smoothly.",
    ],
    commonErrors: [
      "Sounding out 's' and 'h' separately instead of reading 'sh' as one unit",
      "Dropping consonants in longer blends like 'splash' or 'smash'",
      "Confusing -ash with -esh or -ish when reading quickly",
    ],
    relatedSlugs: ["sh-digraph", "at-family", "amp-family"],
  },
  {
    slug: "amp-family",
    pattern: "amp",
    displayName: "-amp Word Family",
    category: "word-family",
    gradeLevel: "Grade 1",
    words: [
      "camp", "damp", "lamp", "ramp", "stamp", "clamp", "cramp",
      "tramp", "champ",
    ],
    sampleSentences: [
      "We camp near the lamp.",
      "Stamp your foot on the damp ramp.",
      "Clamp the tramp's cramp.",
      "The champ set up camp.",
    ],
    teachingNotes: [
      "The -amp family ends in a two-consonant blend ('mp'), so children need to hold the /m/ and /p/ sounds together smoothly rather than pausing between them. This is a common source of choppy, disconnected reading — a child says 'cam...p' with a noticeable break instead of gliding straight through to 'camp' — and the fix is simply modeling the smooth version and having them echo it several times.",
      "'Camp' and 'lamp' are excellent starting points since they are common, concrete nouns young children already know from experience, which makes the connection between the printed word and its meaning immediate. Save the blend-plus-blend words like 'clamp,' 'cramp,' 'stamp,' and 'tramp' for after the plain -amp words feel comfortable.",
    ],
    commonErrors: [
      "Pausing awkwardly between the m and p instead of blending smoothly",
      "Dropping the final p sound entirely, reading 'camp' as 'cam'",
      "Missing the beginning consonant in blend words like 'stamp' or 'clamp'",
    ],
    relatedSlugs: ["and-family", "ash-family", "ump-family"],
  },
  {
    slug: "ast-family",
    pattern: "ast",
    displayName: "-ast Word Family",
    category: "word-family",
    gradeLevel: "Grade 1",
    words: [
      "cast", "fast", "last", "mast", "past", "vast", "blast",
      "outlast", "contrast",
    ],
    sampleSentences: [
      "Run fast to the last mast.",
      "The blast was vast and fast.",
      "We went past the fast cast.",
      "Do not go too fast at last.",
    ],
    teachingNotes: [
      "The -ast family stacks two consonants at the end ('st'), which children usually find easier than 'nd' or 'mp' endings because the /s/ and /t/ sounds are both made near the front of the mouth and glide together naturally. 'Fast' and 'last' are extremely common words in everyday speech, so this family often clicks quickly once a child has a few solid -at or -an words under their belt.",
      "Because the word list is relatively short, this is a good family to practice fluency rather than just accuracy — once your child can read all the words correctly, time a few rounds of reading the list aloud and see how their speed improves session to session. Fluency practice like this matters just as much as accuracy for building a reader who does not have to stop and labor over every word.",
    ],
    commonErrors: [
      "Dropping the final t sound and reading 'fast' as 'fas'",
      "Confusing short a with short u in this family",
      "Reading 'blast' by skipping the beginning blend consonant",
    ],
    relatedSlugs: ["amp-family", "and-family", "at-family"],
  },
  {
    slug: "atch-family",
    pattern: "atch",
    displayName: "-atch Word Family",
    category: "word-family",
    gradeLevel: "Grade 1",
    words: [
      "catch", "match", "patch", "hatch", "batch", "latch",
      "watch", "scratch", "snatch",
    ],
    sampleSentences: [
      "Watch the cat catch the ball.",
      "Match the patch to the batch.",
      "Scratch the latch to hatch it.",
      "Snatch the watch before it drops.",
    ],
    teachingNotes: [
      "The -atch family uses 'tch' instead of a plain 'ch' after a short vowel, following the same spelling logic as -ack using 'ck' instead of 'k' — English tends to add an extra silent letter after a short vowel at the end of a word for certain sounds. Explaining this pattern by comparison ('ack has an extra c, atch has an extra t, both come right after a short vowel') helps children generalize the rule instead of memorizing each word separately.",
      "'Watch' is a slightly irregular member of this family since its vowel sound shifts a bit in many dialects, so do not be surprised if it takes extra repetition compared to the more regular 'catch,' 'match,' and 'patch.' 'Scratch' and 'snatch' add a beginning blend on top of the 'tch' ending, making them good stretch words once the shorter -atch words are solid.",
    ],
    commonErrors: [
      "Sounding out 't' and 'ch' as separate sounds instead of blending 'tch' as one unit",
      "Confusing -atch with -ach or -itch when reading quickly",
      "Dropping the beginning blend in 'scratch' or 'snatch'",
    ],
    relatedSlugs: ["ack-family", "ch-digraph", "ash-family"],
  },

  // ============================================================
  // WORD FAMILIES — short E
  // ============================================================
  {
    slug: "ed-family",
    pattern: "ed",
    displayName: "-ed Word Family",
    category: "word-family",
    gradeLevel: "Kindergarten",
    words: [
      "bed", "fed", "led", "red", "wed", "Ted", "Ned", "sled",
      "bred", "fled", "shed", "sped",
    ],
    sampleSentences: [
      "Ted fed the red bird in bed.",
      "Ned led the way to the shed.",
      "The sled sped past the bed.",
      "We fled to the shed in the sled.",
    ],
    teachingNotes: [
      "The -ed family is worth teaching carefully because the same three letters, 'ed,' also appear as a past-tense verb ending later on (as in 'jumped' or 'wanted'), where they are pronounced completely differently and are not a stand-alone rime at all. At this early stage, keep the two uses separate in your child's mind: here, 'ed' is simply the short-e rime at the end of a one-syllable word like 'bed' or 'red,' not a grammatical ending.",
      "'Bed' and 'red' are typically the easiest entry points since they are common, concrete words. From there, 'sled,' 'shed,' 'fled,' and 'sped' introduce beginning blends and the digraph 'sh,' so save those until the plain four-letter -ed words are automatic. If your child later starts pronouncing 'ed' the same way in both contexts (rime versus verb ending), that confusion is completely normal and resolves with more reading exposure over time.",
    ],
    commonErrors: [
      "Confusing short e with short a, reading 'bed' as 'bad'",
      "Later confusing this rime with the grammatical -ed past-tense ending",
      "Dropping the beginning consonant in blend words like 'sled' or 'sped'",
    ],
    relatedSlugs: ["at-family", "en-family", "et-family"],
  },
  {
    slug: "en-family",
    pattern: "en",
    displayName: "-en Word Family",
    category: "word-family",
    gradeLevel: "Kindergarten",
    words: [
      "hen", "pen", "ten", "men", "den", "Ben", "ken", "then",
      "when", "wren",
    ],
    sampleSentences: [
      "The hen has ten pens.",
      "Ben and the men sat in the den.",
      "When will the hen use the pen?",
      "Then the wren flew to the den.",
    ],
    teachingNotes: [
      "The -en family gives children a short, manageable word list built almost entirely from familiar, concrete nouns — 'hen,' 'pen,' 'ten,' 'den' — which makes it a satisfying family to complete quickly and build momentum. Because the list is short, this is a good time to introduce simple word sorts: give your child a mixed pile of -at, -an, and -en words and have them sort by ending sound, which builds the auditory discrimination skill of hearing rimes apart.",
      "'Then' and 'when' both include the digraph 'th' or 'wh,' so if your child has not yet learned those digraphs, treat 'then' and 'when' as sight words for now and revisit them once digraphs are covered — trying to sound out 't-h-en' or 'w-h-en' letter by letter will only build a bad decoding habit.",
    ],
    commonErrors: [
      "Confusing short e and short a in words like 'hen' versus 'han'",
      "Sounding out 'th' or 'wh' as two separate letters in 'then' and 'when'",
      "Mixing up 'pen' and 'ten' due to similar shapes",
    ],
    relatedSlugs: ["ed-family", "et-family", "eg-family"],
  },
  {
    slug: "et-family",
    pattern: "et",
    displayName: "-et Word Family",
    category: "word-family",
    gradeLevel: "Kindergarten",
    words: [
      "get", "jet", "let", "met", "net", "pet", "set", "vet",
      "wet", "yet", "fret",
    ],
    sampleSentences: [
      "Let the wet pet get a net.",
      "We met the vet at the jet.",
      "Set the net, not the pet.",
      "I have not seen the jet yet.",
    ],
    teachingNotes: [
      "The -et family includes several extremely high-frequency words — 'get,' 'let,' 'met,' 'set' — that children will encounter constantly in early readers, so fluency here pays off across almost every book they pick up next. Because so many -et words are also common sight words, some children read them from memory before they can truly decode them; it is worth double-checking true decoding skill by presenting a less familiar -et word, like 'fret' or 'vet,' and seeing if they can sound it out the same way.",
      "This family also offers a natural moment to talk about rhyming versus spelling: 'debt' rhymes with 'net' but is spelled completely differently, which is a gentle, age-appropriate way to introduce the idea that rhyme and spelling pattern do not always match, without derailing the main lesson.",
    ],
    commonErrors: [
      "Reading high-frequency -et words from memory rather than truly decoding",
      "Confusing short e with short i, drifting 'get' toward 'git'",
      "Skipping the final t sound in fast, casual reading",
    ],
    relatedSlugs: ["ed-family", "en-family", "eck-family"],
  },
  {
    slug: "eg-family",
    pattern: "eg",
    displayName: "-eg Word Family",
    category: "word-family",
    gradeLevel: "Kindergarten",
    words: ["leg", "peg", "beg", "keg", "Meg", "Greg"],
    sampleSentences: [
      "Meg has a leg and a peg.",
      "Greg will beg for the keg.",
      "The peg is on Meg's leg.",
      "Do not beg, Greg.",
    ],
    teachingNotes: [
      "The -eg family is one of the smallest word families your child will meet, with only a handful of common real words, so treat it as a quick, confidence-building session rather than a multi-day unit. 'Leg' is by far the most useful and familiar word here, and many children already recognize it before formal instruction even begins.",
      "Because the list is so short, this is a good family to fold into a broader short-e review alongside -ed, -en, and -et rather than teaching it as a stand-alone lesson. Mixing several short-e families together in one practice sheet also helps children generalize that the vowel sound stays the same across all of them, which is the real skill being built.",
    ],
    commonErrors: [
      "Confusing short e with short a in 'leg' versus 'lag'",
      "Treating unfamiliar words like 'keg' as unreadable rather than sounding them out",
      "Mixing up 'Meg' and 'leg' due to similar letter shapes",
    ],
    relatedSlugs: ["ed-family", "en-family", "et-family"],
  },
  {
    slug: "ell-family",
    pattern: "ell",
    displayName: "-ell Word Family",
    category: "word-family",
    gradeLevel: "Grade 1",
    words: [
      "bell", "sell", "tell", "well", "yell", "fell", "shell",
      "smell", "spell", "swell", "dwell",
    ],
    sampleSentences: [
      "The bell will tell us to yell.",
      "Sell the shell by the well.",
      "Smell and spell the word well.",
      "Dwell on the swell of the bell.",
    ],
    teachingNotes: [
      "The -ell family introduces double consonants at the end of a word ('ll'), which is a common English spelling pattern: a short vowel followed by 'll,' 'ss,' or 'ff' at the end of a short word. Point out that even though there are two L's, they only make one /l/ sound — the doubling is a spelling convention, not a signal to say the sound twice.",
      "Several -ell words start with digraphs or blends ('shell,' 'smell,' 'spell,' 'swell,' 'dwell'), so this family works well as review once your child has covered both 'sh' and basic s-blends. 'Tell,' 'well,' and 'bell' are the simplest entry points and a good place to start before layering in the blend words.",
    ],
    commonErrors: [
      "Trying to pronounce double letters as two separate sounds",
      "Dropping the s in blends like 'smell' or 'spell'",
      "Confusing -ell with -ill due to similar shape and sound",
    ],
    relatedSlugs: ["et-family", "end-family", "sh-digraph"],
  },

  {
    slug: "est-family",
    pattern: "est",
    displayName: "-est Word Family",
    category: "word-family",
    gradeLevel: "Grade 1",
    words: [
      "best", "rest", "test", "nest", "pest", "vest", "west",
      "zest", "chest", "crest",
    ],
    sampleSentences: [
      "The best nest is in the west.",
      "Rest your vest on the chest.",
      "Take a test, then a rest.",
      "The pest sat on the crest.",
    ],
    teachingNotes: [
      "The -est family stacks a three-consonant ending ('st' after the vowel is already two, and many -est words also add a beginning blend like 'chest' or 'crest'), so it is best introduced after -et and -ed feel automatic. 'Best,' 'rest,' 'test,' and 'nest' are common, useful words that show up constantly in school vocabulary, which makes this family worth prioritizing even though it is mechanically a bit harder than simpler short-e families.",
      "Because 'chest' and 'crest' begin with a consonant digraph or blend on top of the -est ending, read those two last. If your child reads 'best' and 'nest' confidently but stalls on 'chest,' the breakdown is happening at the beginning of the word, not the familiar -est ending — go back and isolate the 'ch' sound before reattaching the rest.",
    ],
    commonErrors: [
      "Dropping the final t and reading 'best' as 'bes'",
      "Struggling with the beginning digraph in 'chest'",
      "Confusing short e with short i, drifting 'nest' toward 'nist'",
    ],
    relatedSlugs: ["ed-family", "end-family", "ent-family"],
  },
  {
    slug: "end-family",
    pattern: "end",
    displayName: "-end Word Family",
    category: "word-family",
    gradeLevel: "Grade 1",
    words: [
      "end", "bend", "lend", "mend", "send", "tend", "blend",
      "spend", "trend",
    ],
    sampleSentences: [
      "Send the bend to the end.",
      "Mend and tend the blend.",
      "I will lend and spend at the end.",
      "The trend will bend and end.",
    ],
    teachingNotes: [
      "The -end family mirrors -and in structure — both end in the two-consonant blend 'nd' — so teaching them close together lets your child notice that the ending blend behaves the same way regardless of the vowel in front of it. That kind of cross-family comparison is exactly how strong readers eventually generalize spelling patterns instead of relearning them from scratch every time the vowel changes.",
      "Practice the 'nd' ending in isolation, holding the /n/ briefly before releasing into /d/, and then attach a beginning sound. 'Blend' and 'spend' add a beginning consonant blend on top of the ending blend, so those two are naturally more demanding and worth saving for last within this family.",
    ],
    commonErrors: [
      "Dropping the final d sound and reading 'end' as 'en'",
      "Struggling with the double blend in 'blend' or 'spend'",
      "Confusing -end with -and when reading quickly",
    ],
    relatedSlugs: ["and-family", "est-family", "ent-family"],
  },
  {
    slug: "ent-family",
    pattern: "ent",
    displayName: "-ent Word Family",
    category: "word-family",
    gradeLevel: "Grade 1",
    words: [
      "went", "bent", "dent", "rent", "sent", "tent", "cent",
      "spent", "scent",
    ],
    sampleSentences: [
      "We went to rent a tent.",
      "The cent was bent and sent.",
      "I spent a dent on the tent.",
      "Follow the scent to the tent.",
    ],
    teachingNotes: [
      "The -ent family is anchored by 'went,' one of the most common irregular-feeling but actually fully decodable words a beginning reader meets — many kids memorize it as a sight word before realizing it follows the same -ent pattern as 'bent,' 'dent,' and 'tent.' Pointing out that 'went' decodes just like its family members can be a genuinely satisfying realization for a child who thought it was an exception.",
      "'Spent' and 'scent' both add a beginning blend, and 'scent' in particular has a silent-feeling first letter that trips kids up (the 's' is fully pronounced, but the word does not look the way it sounds at first glance). Treat 'scent' as a slightly advanced bonus word rather than a core practice word if your child is still building basic fluency.",
    ],
    commonErrors: [
      "Treating 'went' as an unrelated sight word instead of part of the family",
      "Dropping the final t sound",
      "Struggling with the beginning blend in 'spent'",
    ],
    relatedSlugs: ["end-family", "est-family", "eck-family"],
  },
  {
    slug: "eck-family",
    pattern: "eck",
    displayName: "-eck Word Family",
    category: "word-family",
    gradeLevel: "Grade 1",
    words: ["neck", "peck", "deck", "check", "wreck", "speck"],
    sampleSentences: [
      "Peck the neck on the deck.",
      "Check the deck for a wreck.",
      "A speck is on the neck.",
      "The bird will peck and check.",
    ],
    teachingNotes: [
      "The -eck family uses the same 'ck' spelling logic your child already met in -ack: after a short vowel at the end of a word, English spells the /k/ sound with 'ck' rather than a plain 'k.' Reminding your child of this rule ('short vowel, then ck') helps them apply it confidently to new -eck words instead of treating each one as unfamiliar.",
      "'Wreck' is worth calling out specifically because the 'w' is silent before 'r' — this is the same silent-w pattern found in words like 'write' and 'wrong,' and -eck is often a child's first encounter with it. Simply tell your child the 'w' is silent here rather than expecting them to sound it out; some spelling patterns are best taught directly rather than discovered.",
    ],
    commonErrors: [
      "Trying to sound out 'c' and 'k' separately",
      "Attempting to pronounce the silent w in 'wreck'",
      "Confusing -eck with -ick when reading quickly",
    ],
    relatedSlugs: ["ack-family", "ock-family", "ent-family"],
  },
  {
    slug: "elt-family",
    pattern: "elt",
    displayName: "-elt Word Family",
    category: "word-family",
    gradeLevel: "Grade 1",
    words: ["belt", "felt", "melt", "welt", "smelt", "dwelt"],
    sampleSentences: [
      "The belt will melt if it felt hot.",
      "Smelt the metal by the belt.",
      "We dwelt on the felt belt.",
      "Did the ice melt or felt cold?",
    ],
    teachingNotes: [
      "The -elt family is small, but 'belt,' 'felt,' and 'melt' are common enough in everyday language that it is still worth a focused practice session. Like other short-e families ending in a consonant blend, the key skill is blending the /l/ and /t/ sounds together smoothly rather than pausing between them.",
      "This family is a natural pairing with -ell, since both share the double-l-adjacent short-e sound, and comparing 'bell' to 'belt' side by side highlights how a single added final consonant changes both the spelling and the ending sound. Use this comparison to reinforce that reading is about tracking every letter in sequence, not just the first and last.",
    ],
    commonErrors: [
      "Rushing through and dropping the final t sound",
      "Confusing -elt with -ell",
      "Pausing awkwardly between the l and t instead of blending",
    ],
    relatedSlugs: ["ell-family", "eck-family", "end-family"],
  },

  // ============================================================
  // WORD FAMILIES — short I
  // ============================================================
  {
    slug: "ig-family",
    pattern: "ig",
    displayName: "-ig Word Family",
    category: "word-family",
    gradeLevel: "Kindergarten",
    words: [
      "big", "dig", "fig", "jig", "pig", "rig", "wig", "twig",
      "sprig",
    ],
    sampleSentences: [
      "The big pig can dig.",
      "Dig for a fig by the rig.",
      "The pig has a wig.",
      "Snap the twig off the sprig.",
    ],
    teachingNotes: [
      "The -ig family is often a child's first real exposure to short i, and it is worth spending a moment contrasting the short i sound /ɪ/ with the short e sound /ɛ/ your child likely just learned, since these two vowels are commonly confused by beginning readers — have them say 'pig' and 'peg' back to back and notice how the mouth position changes slightly for each.",
      "'Big' and 'pig' are the easiest, most familiar entry points, both concrete and highly motivating for young children. 'Twig' and 'sprig' introduce beginning blends and are good stretch words once the plain three- and four-letter -ig words are solid.",
    ],
    commonErrors: [
      "Confusing short i and short e, reading 'pig' as 'peg'",
      "Dropping the beginning consonant in blend words like 'twig'",
      "Guessing based on picture context instead of decoding the letters",
    ],
    relatedSlugs: ["in-family", "ip-family", "it-family"],
  },
  {
    slug: "in-family",
    pattern: "in",
    displayName: "-in Word Family",
    category: "word-family",
    gradeLevel: "Kindergarten",
    words: [
      "in", "bin", "fin", "pin", "tin", "win", "chin", "grin",
      "shin", "skin", "spin", "twin",
    ],
    sampleSentences: [
      "Win the pin in the bin.",
      "The twin has a grin on his chin.",
      "Spin the tin can on your shin.",
      "The fish has a fin and skin.",
    ],
    teachingNotes: [
      "Like -et and -en before it, 'in' itself is a very common preposition that children often recognize instantly as a whole word, which makes it a useful anchor for the rest of the -in family — if they can already read 'in,' point out that 'bin,' 'fin,' 'pin,' and 'win' just add one sound to the front of a word they already know.",
      "This family includes a nice mix of digraph words ('chin,' 'shin') and blend words ('grin,' 'skin,' 'spin,' 'twin'), so it is a good comprehensive review once your child has covered both digraphs and blends separately. If digraphs have not been introduced yet, hold off on 'chin' and 'shin' and focus on the plain -in words first.",
    ],
    commonErrors: [
      "Confusing short i and short e in this family",
      "Sounding out 'ch' or 'sh' as separate letters in 'chin' or 'shin'",
      "Dropping a consonant in blends like 'spin' or 'twin'",
    ],
    relatedSlugs: ["ig-family", "ip-family", "ink-family"],
  },
  {
    slug: "ip-family",
    pattern: "ip",
    displayName: "-ip Word Family",
    category: "word-family",
    gradeLevel: "Kindergarten",
    words: [
      "dip", "hip", "lip", "nip", "rip", "sip", "tip", "zip",
      "chip", "ship", "skip", "trip", "whip",
    ],
    sampleSentences: [
      "Sip and dip the chip.",
      "Skip to the ship with a trip.",
      "Zip your lip and flip the tip.",
      "The whip can rip and nip.",
    ],
    teachingNotes: [
      "The -ip family has one of the largest and most varied word lists among the short-i families, giving a lot of runway for practice: plain words ('dip,' 'hip,' 'lip'), digraph words ('chip,' 'ship,' 'whip'), and blend words ('skip,' 'trip') are all represented. This variety makes -ip an excellent family for a mixed-review session once your child has separately learned digraphs and blends.",
      "'Zip,' 'skip,' and 'trip' tend to be favorites because they connect to real actions a child can act out, which helps cement the word-to-meaning connection alongside the word-to-sound connection. Consider having your child physically skip across the room after reading the word 'skip' — movement paired with reading is a simple, effective way to reinforce new vocabulary.",
    ],
    commonErrors: [
      "Confusing 'ship' and 'chip' due to similar shapes",
      "Dropping a consonant in blends like 'skip' or 'trip'",
      "Reading 'whip' with the w sound omitted",
    ],
    relatedSlugs: ["ig-family", "in-family", "it-family"],
  },
  {
    slug: "it-family",
    pattern: "it",
    displayName: "-it Word Family",
    category: "word-family",
    gradeLevel: "Kindergarten",
    words: [
      "bit", "fit", "hit", "kit", "pit", "sit", "wit", "quit",
      "spit", "slit",
    ],
    sampleSentences: [
      "Sit in the pit and hit the ball.",
      "Fit the kit in the bit.",
      "Do not quit or spit.",
      "The slit is a bit small.",
    ],
    teachingNotes: [
      "The -it family is another workhorse short-i family full of common, everyday words — 'sit,' 'hit,' 'fit,' 'bit' — that appear constantly in early readers and classroom instructions. Because these words are so frequent, this is a good family to practice for automatic, instant recognition rather than slow, effortful sounding-out, since your child will need instant recall of these words very soon in their reading development.",
      "'Quit' is worth a specific mention: the 'qu' combination always makes a /kw/ sound together, never just /k/, so remind your child that q is essentially never seen without u right after it in English. This is a good early introduction to the qu spelling convention that will reappear in many future words.",
    ],
    commonErrors: [
      "Reading 'qu' as just a /k/ sound instead of /kw/",
      "Confusing short i with short e in this family",
      "Dropping the beginning consonant in 'spit' or 'slit'",
    ],
    relatedSlugs: ["ig-family", "in-family", "ip-family"],
  },
  {
    slug: "id-family",
    pattern: "id",
    displayName: "-id Word Family",
    category: "word-family",
    gradeLevel: "Kindergarten",
    words: ["bid", "did", "hid", "kid", "lid", "rid", "grid", "skid"],
    sampleSentences: [
      "The kid did hid the lid.",
      "Bid to get rid of the grid.",
      "Did the kid skid on the lid?",
      "Rid the kid of the grid.",
    ],
    teachingNotes: [
      "The -id family centers on 'did' and 'kid,' two extremely common words that show up in almost every early reader and everyday conversation with young children. 'Did' in particular is worth extra attention because it is often confused visually with 'bid' due to the similar shapes of the letters b and d — a very common reversal error at this age that usually resolves with more reading mileage rather than needing special intervention.",
      "If your child regularly swaps b and d (reading 'bid' as 'did' or vice versa), a simple trick many teachers use is having the child make a fist with both hands, thumbs up, then point index fingers out: the left hand forms a lowercase b, the right hand forms a lowercase d, matching the order of the letters in the alphabet and in the word 'bed.'",
    ],
    commonErrors: [
      "Confusing b and d, reading 'bid' as 'did' or vice versa",
      "Confusing short i with short e in this family",
      "Dropping a consonant in blend words like 'grid' or 'skid'",
    ],
    relatedSlugs: ["ig-family", "it-family", "ick-family"],
  },
  {
    slug: "ick-family",
    pattern: "ick",
    displayName: "-ick Word Family",
    category: "word-family",
    gradeLevel: "Kindergarten–Grade 1",
    words: [
      "kick", "lick", "pick", "sick", "tick", "wick", "brick",
      "chick", "click", "quick", "stick", "thick", "trick",
    ],
    sampleSentences: [
      "Pick a brick and kick it quick.",
      "The chick can lick the stick.",
      "Click the tick, not the trick.",
      "The thick wick is sick.",
    ],
    teachingNotes: [
      "The -ick family, like -ack and -eck before it, uses the 'ck' short-vowel spelling rule for the /k/ sound, so by this point your child should be recognizing that pattern across families without needing it re-taught from scratch. This is a good moment to check for that transfer: if your child hesitates on 'ck' here after having learned it in -ack, a quick reminder ('remember, ck after a short vowel') is usually all it takes.",
      "This family also contains 'chick,' 'click,' 'quick,' 'thick,' and 'trick' — a rich mix of digraphs and blends layered onto the same ending, making -ick an excellent comprehensive review word list once digraphs and blends have both been introduced separately.",
    ],
    commonErrors: [
      "Trying to sound out 'c' and 'k' separately",
      "Confusing -ick with -ack or -eck when reading quickly",
      "Dropping consonants in blend words like 'stick' or 'trick'",
    ],
    relatedSlugs: ["ack-family", "eck-family", "id-family"],
  },
  {
    slug: "ill-family",
    pattern: "ill",
    displayName: "-ill Word Family",
    category: "word-family",
    gradeLevel: "Kindergarten–Grade 1",
    words: [
      "bill", "fill", "hill", "mill", "pill", "will", "chill",
      "drill", "grill", "skill", "spill", "still", "thrill",
    ],
    sampleSentences: [
      "Bill will fill the hill.",
      "Spill the pill on the grill.",
      "Chill by the mill, then drill.",
      "The thrill was still a skill.",
    ],
    teachingNotes: [
      "The -ill family uses the same double-consonant spelling convention your child saw in -ell: two L's make just one /l/ sound. 'Will,' 'hill,' and 'fill' are common, familiar words that give an easy start before moving into digraph and blend words like 'chill,' 'drill,' 'grill,' 'skill,' 'spill,' 'still,' and 'thrill.'",
      "'Still' and 'thrill' are among the more demanding words in this list — 'still' has a beginning blend plus the double-l ending, and 'thrill' stacks a digraph, a blend, and the ending together. Treat these as milestone words rather than starting points, and celebrate them once your child reads them smoothly.",
    ],
    commonErrors: [
      "Trying to pronounce double letters as two separate sounds",
      "Dropping consonants in more complex blend words like 'thrill'",
      "Confusing -ill with -ell",
    ],
    relatedSlugs: ["ell-family", "ick-family", "ing-family"],
  },
  {
    slug: "ing-family",
    pattern: "ing",
    displayName: "-ing Word Family",
    category: "word-family",
    gradeLevel: "Grade 1",
    words: [
      "king", "ring", "sing", "wing", "bring", "cling", "sting",
      "swing", "thing",
    ],
    sampleSentences: [
      "The king can sing and swing.",
      "Bring the ring to the wing.",
      "Cling to the thing that stings.",
      "Sing a song on the swing.",
    ],
    teachingNotes: [
      "The -ing family is one of the most important nasal rime families to teach as a single chunk, since '-ing' also happens to be the most common word ending in the entire English language once children start reading verbs like 'running' and 'jumping.' Teaching your child to instantly recognize '-ing' as one unit here pays enormous dividends across nearly every book they will read from this point forward.",
      "Several -ing words carry beginning blends ('bring,' 'cling,' 'sting,' 'swing'), so use 'king,' 'ring,' 'sing,' and 'wing' as the entry point before tackling those. As with -ang and -ank, resist letting your child sound out the 'n' and 'g' separately — model the whole '-ing' chunk as one smooth sound.",
    ],
    commonErrors: [
      "Splitting '-ing' into separate n and g sounds",
      "Confusing -ing with -ang or -ong when reading quickly",
      "Dropping a consonant in beginning blends like 'sting' or 'swing'",
    ],
    relatedSlugs: ["ill-family", "ink-family", "ang-family"],
  },
  {
    slug: "ink-family",
    pattern: "ink",
    displayName: "-ink Word Family",
    category: "word-family",
    gradeLevel: "Grade 1",
    words: [
      "ink", "link", "pink", "rink", "sink", "wink", "blink",
      "drink", "think", "stink",
    ],
    sampleSentences: [
      "Think pink by the sink.",
      "Wink and blink at the rink.",
      "Link the ink to the drink.",
      "Do not stink at the rink.",
    ],
    teachingNotes: [
      "The -ink family pairs naturally with -ank as another nasalized ending, and comparing the two side by side ('bank' versus 'blink') helps children hear how the vowel changes the whole word even though the 'nk' ending chunk stays constant. 'Think' and 'drink' both start with digraphs or blends, so those are good words to practice once the simpler 'ink,' 'pink,' 'sink,' and 'wink' feel automatic.",
      "As with all the nasal endings, treat '-ink' as one connected unit rather than three separate letter sounds. If your child is stalling out between the vowel and the ending, have them practice saying just '-ink' by itself several times in a row before reattaching a beginning sound.",
    ],
    commonErrors: [
      "Splitting '-ink' into separate n and k sounds",
      "Confusing -ink with -ank when reading quickly",
      "Sounding out 'th' separately in 'think'",
    ],
    relatedSlugs: ["ing-family", "ank-family", "ist-family"],
  },
  {
    slug: "ist-family",
    pattern: "ist",
    displayName: "-ist Word Family",
    category: "word-family",
    gradeLevel: "Grade 1",
    words: ["fist", "list", "mist", "wrist", "twist"],
    sampleSentences: [
      "Make a list and a fist.",
      "The mist is on my wrist.",
      "Twist the list in the mist.",
      "My fist can twist a bit.",
    ],
    teachingNotes: [
      "The -ist family is small but useful, and it stacks the two-consonant 'st' ending on top of short i, the same ending pattern your child already met in -ast and -est with different vowels. Comparing 'fast,' 'fist,' and (informally) the sound pattern across these families reinforces that endings behave consistently no matter which vowel comes before them.",
      "'Wrist' is worth flagging specifically: like 'wreck,' it has a silent w before the r, so tell your child directly rather than expecting them to sound it out. This is good repeated exposure to the silent-w-before-r pattern that will help later with words like 'wrap' and 'wrong.'",
    ],
    commonErrors: [
      "Attempting to pronounce the silent w in 'wrist'",
      "Dropping the final t sound",
      "Confusing -ist with -est when reading quickly",
    ],
    relatedSlugs: ["ink-family", "ift-family", "est-family"],
  },
  {
    slug: "ift-family",
    pattern: "ift",
    displayName: "-ift Word Family",
    category: "word-family",
    gradeLevel: "Grade 1",
    words: ["gift", "lift", "rift", "sift", "drift", "shift", "swift"],
    sampleSentences: [
      "Lift the gift and sift it.",
      "The swift drift will shift.",
      "Sift the rift, then lift.",
      "A swift gift can shift.",
    ],
    teachingNotes: [
      "The -ift family combines a beginning consonant (or blend, in words like 'drift,' 'shift,' 'swift') with the two-consonant 'ft' ending, giving children practice blending sounds on both sides of the vowel in a single word. 'Gift' and 'lift' are the most familiar starting points and are common enough in everyday language to feel immediately useful.",
      "'Shift' and 'swift' both begin with a digraph or blend, so save those until the plainer -ift words are solid. As always with consonant-heavy endings, model saying '-ift' smoothly as a connected unit before attaching different beginning sounds.",
    ],
    commonErrors: [
      "Dropping the final t sound in the ft ending",
      "Struggling with the beginning blend in 'drift' or 'swift'",
      "Confusing -ift with -ist",
    ],
    relatedSlugs: ["ist-family", "ilt-family", "ick-family"],
  },
  {
    slug: "ilt-family",
    pattern: "ilt",
    displayName: "-ilt Word Family",
    category: "word-family",
    gradeLevel: "Grade 1",
    words: ["tilt", "wilt", "quilt", "guilt", "stilt"],
    sampleSentences: [
      "The quilt will tilt and wilt.",
      "Do not feel guilt on the stilt.",
      "Tilt the stilt a bit.",
      "The wilt is on the quilt.",
    ],
    teachingNotes: [
      "The -ilt family is small, and two of its five words — 'guilt' and 'quilt' — involve the tricky 'gu' and 'qu' spellings where the u is part of the consonant sound rather than a vowel to blend separately. Point this out directly: in 'quilt,' 'qu' makes one /kw/ sound before you get to the short-i vowel, and in 'guilt,' the u is silent and just tells you the g is hard rather than soft.",
      "Because this family is short and includes some irregular spellings, treat it as a quick, targeted lesson rather than a major unit, and focus most of your child's independent practice time on 'tilt' and 'wilt,' which are fully regular and predictable.",
    ],
    commonErrors: [
      "Misreading the 'qu' in 'quilt' as just a k sound",
      "Trying to sound out the silent u in 'guilt'",
      "Dropping the final t sound",
    ],
    relatedSlugs: ["ift-family", "ill-family", "imp-family"],
  },
  {
    slug: "imp-family",
    pattern: "imp",
    displayName: "-imp Word Family",
    category: "word-family",
    gradeLevel: "Grade 1",
    words: ["limp", "blimp", "shrimp", "skimp", "wimp"],
    sampleSentences: [
      "The limp blimp will not skimp.",
      "A shrimp is not a wimp.",
      "Skimp on the limp blimp.",
      "The wimp saw a shrimp.",
    ],
    teachingNotes: [
      "The -imp family is small and mostly made up of blend words, so it works best as a stretch challenge once your child is already comfortable with -amp and -ump — comparing all three side by side ('camp,' 'limp,' 'jump') shows how the same 'mp' ending pattern holds steady across every short vowel.",
      "'Shrimp' is a fun standout word for kids because it names a real animal and stacks an unusually long three-consonant beginning blend ('shr') in front of the ending — reading it successfully is a genuine milestone worth pointing out and celebrating.",
    ],
    commonErrors: [
      "Pausing awkwardly between the m and p instead of blending smoothly",
      "Dropping consonants in the beginning blend of 'shrimp' or 'blimp'",
      "Confusing -imp with -ump",
    ],
    relatedSlugs: ["ilt-family", "ump-family", "amp-family"],
  },

  // ============================================================
  // WORD FAMILIES — short O (part 1)
  // ============================================================
  {
    slug: "op-family",
    pattern: "op",
    displayName: "-op Word Family",
    category: "word-family",
    gradeLevel: "Kindergarten",
    words: [
      "hop", "mop", "pop", "top", "cop", "stop", "chop", "crop",
      "drop", "shop", "plop",
    ],
    sampleSentences: [
      "Hop to the shop and stop.",
      "Mop the top, then drop the mop.",
      "Chop the crop with a plop.",
      "Pop by the shop with the cop.",
    ],
    teachingNotes: [
      "The -op family is usually where short o is introduced, and it is worth taking a moment to contrast the short o sound /ɒ/ with the short a sound /æ/ your child already knows, since these two vowels are sometimes confused by beginning readers who have not yet built a strong ear for the difference. Have your child say 'hop' and 'hap'-sounding words back to back and notice how the mouth rounds more for the o sound.",
      "'Stop' and 'shop' are two of the most useful early sight-adjacent words in this family, appearing on street signs and in everyday errands, which gives you natural opportunities to point out and practice them outside of formal lesson time. 'Chop,' 'crop,' 'drop,' and 'plop' add beginning blends and are good next steps once the plainer -op words are solid.",
    ],
    commonErrors: [
      "Confusing short o and short a sounds",
      "Dropping a consonant in blends like 'stop' or 'drop'",
      "Guessing 'stop' for every word that starts with 's' in this family",
    ],
    relatedSlugs: ["ot-family", "ock-family", "og-family"],
  },
  {
    slug: "ot-family",
    pattern: "ot",
    displayName: "-ot Word Family",
    category: "word-family",
    gradeLevel: "Kindergarten",
    words: [
      "dot", "got", "hot", "jot", "lot", "not", "pot", "rot",
      "tot", "shot", "spot", "trot", "knot",
    ],
    sampleSentences: [
      "The hot pot has a spot.",
      "Got a lot? Jot it down.",
      "The tot will trot, not rot.",
      "Shot a dot, tied a knot.",
    ],
    teachingNotes: [
      "The -ot family includes 'not' and 'got,' two extremely common words your child will see on nearly every page of an early reader, so build in extra repetition here even after the family feels 'done.' 'Hot' and 'pot' are similarly frequent and concrete, giving an easy, motivating starting point.",
      "'Knot' is worth calling out directly: the k is silent before n at the beginning of a word, a spelling pattern that also shows up in 'know' and 'knee.' Rather than having your child try to sound out the k, simply tell them it is silent here — this is one of a small handful of silent-letter rules worth teaching explicitly rather than discovering through trial and error.",
    ],
    commonErrors: [
      "Attempting to pronounce the silent k in 'knot'",
      "Confusing short o and short u sounds",
      "Dropping a consonant in blends like 'spot' or 'trot'",
    ],
    relatedSlugs: ["op-family", "og-family", "ock-family"],
  },

  // ============================================================
  // WORD FAMILIES — short O (part 2)
  // ============================================================
  {
    slug: "og-family",
    pattern: "og",
    displayName: "-og Word Family",
    category: "word-family",
    gradeLevel: "Kindergarten",
    words: [
      "dog", "fog", "hog", "jog", "log", "cog", "frog", "clog",
      "smog",
    ],
    sampleSentences: [
      "The dog can jog in the fog.",
      "A frog sat on the log.",
      "The hog will clog the cog.",
      "Smog hides the frog in the fog.",
    ],
    teachingNotes: [
      "The -og family is anchored by 'dog' and 'frog,' two of the most beloved animal words in a young reader's vocabulary, which makes this family reliably fun to teach. Note that in many American dialects, -og words rhyme less exactly with -ot or -op words than the spelling suggests, so let your child's natural pronunciation guide them rather than forcing an unfamiliar 'textbook' vowel sound.",
      "'Frog' and 'clog' both start with beginning blends, so introduce 'dog,' 'fog,' 'hog,' 'jog,' and 'log' first. This is also a good family for a simple rhyming game: say 'log' and ask your child to think of as many real -og words as they can before checking against this list.",
    ],
    commonErrors: [
      "Dropping the beginning consonant in 'frog' or 'clog'",
      "Confusing -og with -ug due to similar vowel quality in fast speech",
      "Guessing 'dog' for any word that starts with a similar shape",
    ],
    relatedSlugs: ["op-family", "ot-family", "ock-family"],
  },
  {
    slug: "ob-family",
    pattern: "ob",
    displayName: "-ob Word Family",
    category: "word-family",
    gradeLevel: "Kindergarten",
    words: ["cob", "job", "mob", "rob", "sob", "blob", "knob", "slob", "snob"],
    sampleSentences: [
      "Rob got a job at the cob.",
      "The mob will sob at the blob.",
      "Turn the knob, not the slob.",
      "Do not rob the snob.",
    ],
    teachingNotes: [
      "The -ob family is small but includes 'job,' a genuinely high-frequency word children encounter often in classroom talk about chores and responsibilities. Most of the words here are plain and short, making this a good confidence-building family to complete quickly in a single sitting.",
      "'Knob' repeats the silent-k-before-n pattern your child may have already seen in 'knot,' so this is a good chance to reinforce that rule rather than introduce it fresh. If your child has not yet met 'knot,' simply tell them directly that the k is silent here.",
    ],
    commonErrors: [
      "Attempting to pronounce the silent k in 'knob'",
      "Confusing short o and short u sounds",
      "Dropping a consonant in blend words like 'blob' or 'slob'",
    ],
    relatedSlugs: ["og-family", "ot-family", "op-family"],
  },
  {
    slug: "ock-family",
    pattern: "ock",
    displayName: "-ock Word Family",
    category: "word-family",
    gradeLevel: "Kindergarten–Grade 1",
    words: [
      "dock", "lock", "rock", "sock", "clock", "block", "flock",
      "knock", "shock", "stock",
    ],
    sampleSentences: [
      "Lock the dock with a rock.",
      "The clock is on the block.",
      "Knock on the rock, not the sock.",
      "A flock gave the stock a shock.",
    ],
    teachingNotes: [
      "The -ock family completes the set of common 'ck' short-vowel families your child has now met across -ack, -eck, -ick, and -ock, so this is a great opportunity for a mixed review across all five vowels using the same ending pattern. If your child can move fluidly between 'back,' 'peck,' 'kick,' and 'rock' in the same session, that is strong evidence the 'ck' rule has truly generalized rather than being memorized family by family.",
      "'Knock' repeats the silent-k pattern, and 'clock,' 'block,' 'flock,' and 'stock' all add beginning blends. Sequence practice from the plainest words ('dock,' 'lock,' 'rock,' 'sock') up through the blend words for a natural difficulty progression within a single session.",
    ],
    commonErrors: [
      "Attempting to pronounce the silent k in 'knock'",
      "Trying to sound out 'c' and 'k' separately",
      "Dropping a consonant in blend words like 'block' or 'flock'",
    ],
    relatedSlugs: ["ack-family", "ick-family", "eck-family"],
  },
  {
    slug: "ong-family",
    pattern: "ong",
    displayName: "-ong Word Family",
    category: "word-family",
    gradeLevel: "Grade 1",
    words: ["song", "long", "gong", "strong", "wrong", "along"],
    sampleSentences: [
      "Sing a long song.",
      "The gong is strong, not wrong.",
      "Come along and sing a song.",
      "A long gong is strong.",
    ],
    teachingNotes: [
      "The -ong family completes the nasal-ending set alongside -ang, -ing, and -ung, and by this point your child should recognize the pattern: vowel plus 'ng' is read as one smooth chunk, never as separate letter sounds. 'Song' and 'long' are common, easy starting points before moving to 'strong' and 'wrong,' which both add beginning blends or the silent-w pattern.",
      "'Wrong' repeats the silent-w-before-r pattern from 'wreck' and 'wrist,' so use it as another chance to reinforce that rule by name rather than expecting your child to sound it out independently. 'Along' is a two-syllable word and a good stretch example that the -ong chunk works the same way even inside longer words.",
    ],
    commonErrors: [
      "Splitting '-ong' into separate n and g sounds",
      "Attempting to pronounce the silent w in 'wrong'",
      "Confusing -ong with -ang or -ing when reading quickly",
    ],
    relatedSlugs: ["ang-family", "ing-family", "ock-family"],
  },
  {
    slug: "ond-family",
    pattern: "ond",
    displayName: "-ond Word Family",
    category: "word-family",
    gradeLevel: "Grade 1",
    words: ["bond", "fond", "pond", "respond"],
    sampleSentences: [
      "The fond frog is in the pond.",
      "We have a bond by the pond.",
      "Respond if you are fond of the pond.",
      "A bond formed at the pond.",
    ],
    teachingNotes: [
      "The -ond family is one of the smallest on this list, and 'pond' is by far the most useful and familiar word for young readers, often connected to real experience with ducks, frogs, and nature walks. Because there are so few common -ond words, this is a quick, low-pressure family to add to a broader short-o review rather than a stand-alone lesson.",
      "'Respond' is a two-syllable bonus word that shows the -ond chunk works the same way even when it is not the very first sound in the word — useful for children who are starting to encounter longer, multisyllabic words in their reading.",
    ],
    commonErrors: [
      "Dropping the final d sound",
      "Struggling to blend the n and d together smoothly",
      "Confusing -ond with -and or -end",
    ],
    relatedSlugs: ["ong-family", "and-family", "end-family"],
  },
  {
    slug: "oss-family",
    pattern: "oss",
    displayName: "-oss Word Family",
    category: "word-family",
    gradeLevel: "Grade 1",
    words: ["boss", "loss", "toss", "cross", "floss", "gloss"],
    sampleSentences: [
      "Toss the ball to the boss.",
      "Cross and floss, do not fuss.",
      "The loss came with a toss.",
      "Gloss the cross with care.",
    ],
    teachingNotes: [
      "The -oss family introduces the doubled-consonant spelling rule your child has already seen with 'll' in -ell and -ill, now applied to 's': a short vowel followed by 'ss' at the end of a short word is extremely common in English ('boss,' 'loss,' 'toss'), and the double letter still makes just one /s/ sound.",
      "'Cross,' 'floss,' and 'gloss' all add a beginning blend, so start with 'boss,' 'loss,' and 'toss' first. This family also offers a nice everyday connection — brushing and flossing teeth — which can turn a routine moment into an easy, natural reading practice opportunity.",
    ],
    commonErrors: [
      "Trying to pronounce double s as two separate sounds",
      "Dropping a consonant in beginning blends like 'cross' or 'floss'",
      "Confusing -oss with -ost",
    ],
    relatedSlugs: ["ock-family", "oft-family", "ong-family"],
  },
  {
    slug: "oft-family",
    pattern: "oft",
    displayName: "-oft Word Family",
    category: "word-family",
    gradeLevel: "Grade 1",
    words: ["soft", "loft", "croft", "aloft"],
    sampleSentences: [
      "The soft cat sat in the loft.",
      "Fly aloft above the loft.",
      "A soft bed is in the loft.",
      "The croft has a soft roof.",
    ],
    teachingNotes: [
      "The -oft family is small, but 'soft' is a genuinely common and useful word that pairs well with sensory vocabulary lessons (soft versus hard, loud versus quiet) that many kindergarten and first-grade classrooms already teach. Because the word list is so short, treat this as a quick addition to a broader short-o review session.",
      "'Loft' is a good second word to teach, especially if your family lives in or has visited a home with a loft space — concrete, real-world connections make abstract phonics rules stick much better than word lists alone.",
    ],
    commonErrors: [
      "Dropping the final t sound in the ft ending",
      "Confusing -oft with -ost or -oss",
      "Rushing the blend between f and t",
    ],
    relatedSlugs: ["oss-family", "ift-family", "ond-family"],
  },
  {
    slug: "ox-family",
    pattern: "ox",
    displayName: "-ox Word Family",
    category: "word-family",
    gradeLevel: "Kindergarten",
    words: ["box", "fox", "ox", "pox", "lox"],
    sampleSentences: [
      "The fox sat by the box.",
      "An ox is in the box.",
      "The fox has a pox.",
      "Put the box by the ox.",
    ],
    teachingNotes: [
      "The -ox family is short and simple, and 'box' and 'fox' are both concrete, familiar words that most children already know from picture books and everyday life. Note that 'x' at the end of a word makes a /ks/ sound — two consonant sounds blended into one letter — which is worth pointing out explicitly since it is a slightly unusual case where a single letter represents two sounds.",
      "Because the list is short, use this family as a quick, satisfying win in the middle of a longer short-o practice session rather than a stand-alone lesson, and pair it with 'The Fox in Sox'-style rhyming books if you have access to them for extra reinforcement.",
    ],
    commonErrors: [
      "Reading x as only a /k/ sound and dropping the /s/",
      "Confusing short o with short u",
      "Guessing 'fox' for every word in this family",
    ],
    relatedSlugs: ["og-family", "ob-family", "ock-family"],
  },

  // ============================================================
  // WORD FAMILIES — short U
  // ============================================================
  {
    slug: "ug-family",
    pattern: "ug",
    displayName: "-ug Word Family",
    category: "word-family",
    gradeLevel: "Kindergarten",
    words: [
      "bug", "dug", "hug", "jug", "mug", "rug", "tug", "chug",
      "drug", "plug", "shrug", "slug", "snug",
    ],
    sampleSentences: [
      "The bug is on the rug.",
      "Hug the mug, then tug the jug.",
      "The slug gave a shrug.",
      "Plug it in, snug on the rug.",
    ],
    teachingNotes: [
      "The -ug family typically introduces short u, and 'bug,' 'hug,' 'mug,' and 'rug' are all common, concrete words that give an easy, motivating start. It is worth contrasting short u /ʌ/ directly against short o /ɒ/ and short a /æ/, since all three can blur together for a child whose ear is still developing — have them say 'bug,' 'bag,' and 'bog' in a row and listen for the difference.",
      "'Shrug' is a fun stretch word with a three-consonant beginning blend, and having your child physically shrug their shoulders after reading it gives a memorable, embodied connection to a word whose meaning is otherwise a little abstract for young children.",
    ],
    commonErrors: [
      "Confusing short u with short o or short a",
      "Dropping consonants in beginning blends like 'drug' or 'plug'",
      "Guessing 'bug' for every word that starts with a similar shape",
    ],
    relatedSlugs: ["un-family", "ut-family", "ub-family"],
  },
  {
    slug: "un-family",
    pattern: "un",
    displayName: "-un Word Family",
    category: "word-family",
    gradeLevel: "Kindergarten",
    words: ["bun", "fun", "gun", "nun", "pun", "run", "sun", "spun", "stun"],
    sampleSentences: [
      "Run in the sun for fun.",
      "The bun is in the sun.",
      "Spun a pun, had fun.",
      "The gun did stun the nun.",
    ],
    teachingNotes: [
      "The -un family includes two of the most common words in a young child's vocabulary, 'fun' and 'sun,' both frequently used in early readers and everyday conversation about weather and play. This makes -un a satisfying, quick-to-master family that builds real momentum early in short-u instruction.",
      "'Spun' and 'stun' both add a beginning blend, so introduce those after the simpler four-letter -un words feel comfortable. This family also works well for a simple listening game: say a list of words mixing -un and -an family words and have your child signal which vowel sound they heard.",
    ],
    commonErrors: [
      "Confusing short u with short a, mixing up -un and -an words",
      "Dropping a consonant in blends like 'spun' or 'stun'",
      "Skipping the final n sound in fast reading",
    ],
    relatedSlugs: ["ug-family", "ut-family", "up-family"],
  },
  {
    slug: "ut-family",
    pattern: "ut",
    displayName: "-ut Word Family",
    category: "word-family",
    gradeLevel: "Kindergarten",
    words: ["but", "cut", "gut", "hut", "jut", "nut", "shut", "strut"],
    sampleSentences: [
      "Cut the nut, but shut the hut.",
      "The hut had a jut and a gut.",
      "Strut to the hut, then shut it.",
      "But the nut is not cut.",
    ],
    teachingNotes: [
      "The -ut family includes 'but' and 'cut,' two very high-frequency words that appear on nearly every page of an early reader, so this family deserves extra repetition even after your child seems to have it down. 'Nut' and 'hut' are similarly common and concrete, giving an easy, motivating word list overall.",
      "One irregular word worth mentioning separately is 'put,' which looks like it belongs in this family but is actually pronounced with the 'oo' sound found in 'book' rather than the short u in 'but.' Point this out directly as an exception rather than letting your child discover the mismatch on their own and lose confidence in the pattern.",
    ],
    commonErrors: [
      "Applying the -ut sound to the irregular word 'put'",
      "Confusing short u with short o",
      "Dropping consonants in the blend word 'strut'",
    ],
    relatedSlugs: ["ug-family", "un-family", "uck-family"],
  },
  {
    slug: "ub-family",
    pattern: "ub",
    displayName: "-ub Word Family",
    category: "word-family",
    gradeLevel: "Kindergarten",
    words: ["cub", "hub", "rub", "sub", "tub", "club", "grub", "scrub", "stub"],
    sampleSentences: [
      "Rub the cub in the tub.",
      "The club has a grub.",
      "Scrub the tub, then the stub.",
      "A sub is in the hub.",
    ],
    teachingNotes: [
      "The -ub family is anchored by 'tub' and 'cub,' both concrete and easy for young children to picture, which makes for a quick, satisfying introduction to short u alongside -ug and -un. 'Club,' 'grub,' 'scrub,' and 'stub' all add beginning blends and are good next steps once the plain -ub words are solid.",
      "Bath time is a genuinely useful moment to reinforce this family in real life — pointing at the tub and sounding out the word together turns a routine activity into unplanned, low-pressure reading practice, which is often more effective than dedicated worksheet time for young or reluctant readers.",
    ],
    commonErrors: [
      "Confusing short u with short o",
      "Dropping a consonant in beginning blends like 'scrub' or 'club'",
      "Rushing through and dropping the final b sound",
    ],
    relatedSlugs: ["ug-family", "ut-family", "um-family"],
  },
  {
    slug: "um-family",
    pattern: "um",
    displayName: "-um Word Family",
    category: "word-family",
    gradeLevel: "Kindergarten",
    words: ["bum", "gum", "hum", "mum", "sum", "chum", "drum", "glum", "plum", "slum"],
    sampleSentences: [
      "Hum a tune, chew some gum.",
      "The drum has a sum.",
      "A plum makes me glum.",
      "Chum, do not hum in the slum.",
    ],
    teachingNotes: [
      "The -um family includes 'gum' and 'drum,' two words that connect easily to real objects a child can hold or point to, which supports the concrete, hands-on learning young children benefit from most. 'Sum' is worth a quick note since it sounds identical to 'some,' a common sight word spelled differently — a gentle early example of homophones your child will meet more of later.",
      "'Drum,' 'glum,' 'plum,' and 'slum' all add a beginning blend, so save those for after 'bum,' 'gum,' 'hum,' 'mum,' and 'sum' feel automatic. Try tapping out a rhythm on a real drum (or a table) each time your child successfully reads a new -um word for a bit of playful reinforcement.",
    ],
    commonErrors: [
      "Confusing 'sum' and 'some' due to identical pronunciation",
      "Dropping a consonant in blends like 'drum' or 'plum'",
      "Confusing short u with short o",
    ],
    relatedSlugs: ["ub-family", "ump-family", "uck-family"],
  },
  {
    slug: "uck-family",
    pattern: "uck",
    displayName: "-uck Word Family",
    category: "word-family",
    gradeLevel: "Kindergarten–Grade 1",
    words: [
      "buck", "duck", "luck", "muck", "puck", "suck", "tuck",
      "chuck", "cluck", "stuck", "truck", "struck",
    ],
    sampleSentences: [
      "The duck got stuck in the truck.",
      "Good luck, chuck the puck.",
      "Tuck the duck, hear it cluck.",
      "The truck struck some muck.",
    ],
    teachingNotes: [
      "The -uck family completes the full set of common 'ck' short-vowel families across all five vowels your child has now learned (-ack, -eck, -ick, -ock, -uck), making this an ideal moment for a comprehensive cross-vowel review of the 'ck' rule. 'Duck' and 'truck' are especially high-value words given how often vehicles and farm animals appear in early reading material.",
      "'Struck' is the most demanding word in this family, stacking a three-consonant beginning blend onto the 'uck' ending — a genuine milestone word rather than a starting point. Save it for after your child is fluent with the simpler words in this list.",
    ],
    commonErrors: [
      "Trying to sound out 'c' and 'k' separately",
      "Dropping consonants in blend words like 'truck' or 'struck'",
      "Confusing -uck with -ock",
    ],
    relatedSlugs: ["ock-family", "ick-family", "un-family"],
  },
  {
    slug: "ump-family",
    pattern: "ump",
    displayName: "-ump Word Family",
    category: "word-family",
    gradeLevel: "Grade 1",
    words: [
      "bump", "dump", "hump", "jump", "lump", "pump", "chump",
      "clump", "grump", "plump", "stump", "thump", "trump",
    ],
    sampleSentences: [
      "Jump over the bump and pump.",
      "The grump sat on a stump.",
      "Thump the plump lump.",
      "Dump the clump by the hump.",
    ],
    teachingNotes: [
      "The -ump family completes the set of 'mp' endings alongside -amp and -imp, and 'jump' is one of the most common action words a beginning reader learns, often paired with real movement in classroom games. As with other -mp endings, the key skill is blending /m/ and /p/ together smoothly rather than pausing awkwardly between them.",
      "Several -ump words carry a beginning blend ('chump,' 'clump,' 'grump,' 'plump,' 'stump,' 'thump,' 'trump'), so sequence practice from the plainer words toward these once your child is ready for a challenge. Physically jumping each time your child reads the word 'jump' successfully adds a fun, embodied cue that many young readers respond well to.",
    ],
    commonErrors: [
      "Pausing awkwardly between the m and p instead of blending smoothly",
      "Dropping consonants in beginning blends like 'stump' or 'thump'",
      "Confusing -ump with -amp or -imp",
    ],
    relatedSlugs: ["amp-family", "imp-family", "unk-family"],
  },
  {
    slug: "unk-family",
    pattern: "unk",
    displayName: "-unk Word Family",
    category: "word-family",
    gradeLevel: "Grade 1",
    words: [
      "bunk", "dunk", "hunk", "junk", "sunk", "chunk", "drunk",
      "skunk", "spunk", "trunk",
    ],
    sampleSentences: [
      "The skunk sat on a bunk.",
      "Dunk the trunk in the junk.",
      "A chunk of the sunk trunk.",
      "That skunk has spunk.",
    ],
    teachingNotes: [
      "The -unk family rounds out the nasal 'nk' endings your child has now seen across -ank and -ink, and 'skunk' and 'trunk' are two memorably concrete, fun words that tend to stick well for young readers. As with -ank and -ink, treat '-unk' as a single connected chunk rather than three separate letter sounds.",
      "'Skunk' stacks a beginning blend onto the ending, making it a slightly more demanding word than 'bunk' or 'junk' — introduce it once your child is comfortable with the simpler words in this list, and consider it a good stopping point for a session focused purely on nasal endings.",
    ],
    commonErrors: [
      "Splitting '-unk' into separate n and k sounds",
      "Dropping the s in the beginning blend of 'skunk'",
      "Confusing -unk with -ank or -ink",
    ],
    relatedSlugs: ["ank-family", "ink-family", "ump-family"],
  },
  {
    slug: "ust-family",
    pattern: "ust",
    displayName: "-ust Word Family",
    category: "word-family",
    gradeLevel: "Grade 1",
    words: ["bust", "dust", "gust", "just", "must", "rust", "crust", "trust"],
    sampleSentences: [
      "You must dust the crust.",
      "A gust blew the rust away.",
      "Just trust the bust.",
      "The crust has dust and rust.",
    ],
    teachingNotes: [
      "The -ust family finishes the trio of 'st'-ending families your child has met across -ast, -ist, and -ust, and 'must' and 'just' are two very high-frequency words that will appear constantly in the sentences and instructions your child reads going forward. Reviewing all three st-ending families together in one sitting is a strong way to confirm the pattern has fully generalized.",
      "'Crust' and 'trust' both add a beginning blend, so save those until 'bust,' 'dust,' 'gust,' 'just,' 'must,' and 'rust' are automatic. This is also a good family to introduce the idea of using context to double-check a decoded word: if a sentence is about a pie, 'crust' makes more sense than a similar-looking word, and confirming meaning is part of real reading, not just sounding out letters.",
    ],
    commonErrors: [
      "Dropping the final t sound",
      "Struggling with beginning blends in 'crust' or 'trust'",
      "Confusing -ust with -ost or -ist",
    ],
    relatedSlugs: ["ist-family", "ast-family", "unch-family"],
  },
  {
    slug: "uff-family",
    pattern: "uff",
    displayName: "-uff Word Family",
    category: "word-family",
    gradeLevel: "Grade 1",
    words: ["cuff", "huff", "muff", "puff", "buff", "bluff", "fluff", "gruff", "scuff", "stuff"],
    sampleSentences: [
      "Puff and huff, do not scuff.",
      "The fluff is on the cuff.",
      "A gruff voice said 'stuff it.'",
      "Bluff with a puff of fluff.",
    ],
    teachingNotes: [
      "The -uff family introduces another doubled-consonant ending, this time 'ff' instead of 'ss' or 'll,' following the exact same short-vowel-plus-doubled-letter rule your child has now seen three times over. 'Puff' and 'stuff' are common enough words to anchor the family, and pointing out the repeating pattern across -ell, -oss, and -uff helps children see doubled endings as one predictable spelling rule rather than three separate ones to memorize.",
      "'Bluff,' 'fluff,' 'gruff,' 'scuff,' and 'stuff' all add beginning blends, so this family offers solid blend practice once your child is past the plainer four-letter words. The classic story reference of the wolf huffing and puffing gives a natural, memorable hook for 'huff' and 'puff' specifically.",
    ],
    commonErrors: [
      "Trying to pronounce double f as two separate sounds",
      "Dropping a consonant in beginning blends like 'bluff' or 'scuff'",
      "Confusing -uff with -off",
    ],
    relatedSlugs: ["oss-family", "ell-family", "ill-family"],
  },
  {
    slug: "unch-family",
    pattern: "unch",
    displayName: "-unch Word Family",
    category: "word-family",
    gradeLevel: "Grade 1",
    words: ["bunch", "hunch", "lunch", "munch", "punch", "crunch"],
    sampleSentences: [
      "Munch your lunch, then punch.",
      "A bunch had a hunch.",
      "Crunch the punch at lunch.",
      "Have a hunch about the bunch.",
    ],
    teachingNotes: [
      "The -unch family combines the nasal 'n' sound with the digraph 'ch,' so it is best taught after your child already knows 'ch' as a single sound — otherwise they may try to read the ending as three separate pieces instead of the connected 'unch' chunk. 'Lunch' is by far the most familiar and frequently used word here, tied to an everyday routine most children can relate to immediately.",
      "'Crunch' adds a beginning blend on top of everything else, making it the most demanding word in this short list — a good final challenge word once 'bunch,' 'hunch,' 'lunch,' 'munch,' and 'punch' are all comfortable.",
    ],
    commonErrors: [
      "Sounding out 'ch' as two separate letters instead of one unit",
      "Splitting the nasal n from the rest of the ending",
      "Dropping the beginning blend consonant in 'crunch'",
    ],
    relatedSlugs: ["ch-digraph", "ust-family", "unk-family"],
  },
  {
    slug: "up-family",
    pattern: "up",
    displayName: "-up Word Family",
    category: "word-family",
    gradeLevel: "Kindergarten",
    words: ["cup", "pup", "up", "sup"],
    sampleSentences: [
      "Fill the cup up.",
      "The pup looks up.",
      "Sup with the pup.",
      "Up in the cup.",
    ],
    teachingNotes: [
      "The -up family is one of the smallest and simplest on this list, built around the very common words 'up,' 'cup,' and 'pup,' all of which a child likely already recognizes in speech well before they can read them in print. Because the list is so short, this is an easy, quick win to close out a short-u review session on a confident note.",
      "Since 'up' is also an extremely common standalone sight word, use this family to reinforce that it decodes just like 'cup' and 'pup' rather than being a special exception — a small but meaningful realization that builds trust in the whole phonics system for a beginning reader.",
    ],
    commonErrors: [
      "Treating 'up' as a memorized sight word rather than a decodable one",
      "Confusing short u with short o",
      "Skipping the final p sound in fast, casual reading",
    ],
    relatedSlugs: ["ug-family", "un-family", "ub-family"],
  },

  // ============================================================
  // DIGRAPHS
  // ============================================================
  {
    slug: "sh-digraph",
    pattern: "sh",
    displayName: "SH Digraph",
    category: "digraph",
    gradeLevel: "Kindergarten–Grade 1",
    words: [
      "ship", "shop", "shed", "shell", "shine", "share", "fish",
      "wish", "dish", "cash", "wash", "brush", "crash", "flash",
    ],
    sampleSentences: [
      "The ship will shop for a shell.",
      "Wish for fish in the dish.",
      "Wash the cash and brush.",
      "Share the shine, then crash.",
    ],
    teachingNotes: [
      "The digraph 'sh' is usually the very first two-letter-one-sound combination a child learns, and it is worth being explicit about what makes it different from a blend: in a blend like 'st,' you can still hear both the /s/ and the /t/, but in 'sh,' the s and h disappear completely into one brand-new sound that neither letter makes on its own. Say 'sh' by itself, finger to lips, and have your child feel that it is a single continuous sound rather than two clicks.",
      "'Sh' shows up at the beginning ('ship,' 'shop'), the end ('fish,' 'wish'), and occasionally in the middle of words, so give your child practice spotting it in all three positions rather than only at the start of a word. A quick sorting game — cards with 'sh' at the beginning versus the end — helps children notice the digraph regardless of where it lands.",
    ],
    commonErrors: [
      "Trying to sound out 's' and 'h' as two separate sounds",
      "Confusing 'sh' with 'ch' since both are common early digraphs",
      "Missing 'sh' when it appears at the end of a word instead of the beginning",
    ],
    relatedSlugs: ["ch-digraph", "ash-family", "th-digraph"],
  },
  {
    slug: "ch-digraph",
    pattern: "ch",
    displayName: "CH Digraph",
    category: "digraph",
    gradeLevel: "Kindergarten–Grade 1",
    words: [
      "chip", "chin", "chat", "chop", "cheese", "chair", "teach",
      "beach", "peach", "lunch", "bench", "much", "such", "church",
    ],
    sampleSentences: [
      "Chip and chat by the chair.",
      "Teach me to reach the peach.",
      "Much cheese is on the bench.",
      "Church bells ring at lunch.",
    ],
    teachingNotes: [
      "Like 'sh,' the digraph 'ch' makes one completely new sound when the two letters combine, and it is a good idea to directly compare 'sh' and 'ch' side by side once your child knows both, since they are visually similar and easy to mix up under time pressure. Have your child say 'ship' and 'chip' back to back and notice how the ch sound has a slight puff or click at the start that sh does not.",
      "'Ch' also appears at the end of words ('much,' 'such,' 'lunch,' 'bench'), not just the beginning, so make sure practice includes both positions. A small number of 'ch' words, mostly borrowed from other languages, are pronounced like 'sh' (as in 'chef') or like 'k' (as in 'school'), but these are rare enough at this stage to set aside until your child is a more advanced reader.",
    ],
    commonErrors: [
      "Confusing 'ch' with 'sh' when reading quickly",
      "Trying to sound out 'c' and 'h' as two separate sounds",
      "Missing 'ch' at the end of a word like 'lunch' or 'bench'",
    ],
    relatedSlugs: ["sh-digraph", "unch-family", "atch-family"],
  },
  {
    slug: "th-digraph",
    pattern: "th",
    displayName: "TH Digraph",
    category: "digraph",
    gradeLevel: "Kindergarten–Grade 1",
    words: [
      "this", "that", "then", "thin", "bath", "math", "with",
      "teeth", "three", "thumb", "think", "cloth", "moth", "path",
    ],
    sampleSentences: [
      "This bath is with three.",
      "Think about the thin moth.",
      "That math path has a thumb.",
      "Brush your teeth, then bathe.",
    ],
    teachingNotes: [
      "The digraph 'th' is unusual because it actually represents two different sounds in English, and children need to hear both: a 'voiced' th where the vocal cords buzz (as in 'this,' 'that,' 'then') and an 'unvoiced' th with no buzz (as in 'thin,' 'bath,' 'three'). You do not need to teach the technical labels — just have your child put a hand on their throat while saying 'this' and then 'thin' and notice the difference in vibration.",
      "Because 'th' words are so frequent — 'this,' 'that,' 'then,' and 'with' are among the most common words in English — accuracy here matters more than almost any other digraph. If your child substitutes an 'f' or 'd' sound for 'th' (a common developmental pattern, saying 'dis' for 'this' or 'baf' for 'bath'), that is often just a normal articulation stage that resolves with age, but mention it to a speech-language professional if it persists much past age seven.",
    ],
    commonErrors: [
      "Substituting an f or d sound for th",
      "Not distinguishing between the voiced and unvoiced versions of th",
      "Trying to sound out 't' and 'h' as two separate sounds",
    ],
    relatedSlugs: ["wh-digraph", "sh-digraph", "ent-family"],
  },
  {
    slug: "wh-digraph",
    pattern: "wh",
    displayName: "WH Digraph",
    category: "digraph",
    gradeLevel: "Kindergarten–Grade 1",
    words: [
      "what", "when", "where", "why", "white", "wheel", "whale",
      "whisk", "whisper", "which",
    ],
    sampleSentences: [
      "What is white and where?",
      "When will the whale whisper?",
      "Why is the wheel here?",
      "Whisk the batter, then ask which.",
    ],
    teachingNotes: [
      "The digraph 'wh' makes a sound very close to a plain 'w' in most American English dialects — 'what' and a hypothetical 'wat' sound almost identical — so this is one digraph where the visual spelling matters more than a dramatically different sound. Still, teaching it as its own two-letter unit matters because so many question words start this way: 'what,' 'when,' 'where,' 'why,' and 'which' are the backbone of how children ask questions in both speech and early writing.",
      "Because the 'wh' question words are used so often in classroom instructions ('When do we...', 'Where is the...'), fluent, instant recognition of this digraph pays off well beyond phonics practice — it directly supports following along with spoken and written directions at school.",
    ],
    commonErrors: [
      "Confusing 'wh' words with plain 'w' words when reading quickly",
      "Trying to sound out 'w' and 'h' as two separate sounds",
      "Mixing up similar-looking question words like 'when' and 'where'",
    ],
    relatedSlugs: ["th-digraph", "ent-family", "ip-family"],
  },
  {
    slug: "ph-digraph",
    pattern: "ph",
    displayName: "PH Digraph",
    category: "digraph",
    gradeLevel: "Grade 1–Grade 2",
    words: [
      "phone", "photo", "graph", "dolphin", "alphabet", "elephant",
      "trophy", "nephew", "phonics",
    ],
    sampleSentences: [
      "The phone has a photo.",
      "Draw a graph of the dolphin.",
      "Learn the alphabet with an elephant.",
      "The trophy went to my nephew.",
    ],
    teachingNotes: [
      "The digraph 'ph' makes an /f/ sound and almost always shows up in words that originally came into English from Greek — 'phone,' 'photo,' 'graph,' 'alphabet,' and even the word 'phonics' itself all trace back to Greek roots. This is a nice moment to plant an early seed about word origins: telling a child 'ph makes an f sound because these words came from Greek a long time ago' gives them a memorable hook rather than an arbitrary spelling rule to memorize.",
      "'Ph' is less frequent than 'sh,' 'ch,' 'th,' or 'wh,' so it is typically introduced a bit later, often in first or second grade once a child has a solid handle on the more common digraphs. Because it always makes the same /f/ sound as the letter f, some children find it easier to grasp than digraphs that make an entirely new sound, once they know to expect it.",
    ],
    commonErrors: [
      "Trying to sound out 'p' and 'h' as two separate sounds",
      "Confusing ph words with plain f-spelled words in writing",
      "Not recognizing ph in the middle of longer words like 'elephant' or 'alphabet'",
    ],
    relatedSlugs: ["th-digraph", "sh-digraph", "ock-family"],
  },
  {
    slug: "ck-digraph",
    pattern: "ck",
    displayName: "CK Digraph",
    category: "digraph",
    gradeLevel: "Kindergarten–Grade 1",
    words: [
      "back", "sock", "duck", "pick", "rock", "neck", "kick",
      "luck", "deck", "truck", "black", "clock", "stick", "trick",
    ],
    sampleSentences: [
      "Kick the sock, pick the rock.",
      "The duck has luck by the deck.",
      "A black truck hit the stick.",
      "Trick the clock, then kick back.",
    ],
    teachingNotes: [
      "'Ck' is a spelling-only digraph: it makes exactly the same /k/ sound as a plain letter k, but English uses 'ck' instead of 'k' specifically right after a short vowel at the end of a one-syllable word. This rule is genuinely predictable and worth stating outright — 'short vowel, then ck' — rather than leaving your child to notice it purely through repeated exposure across all the individual word families.",
      "By the time a child has worked through -ack, -eck, -ick, -ock, and -uck as separate word families, this entry is a good chance to step back and confirm the rule has generalized across all five vowels at once — mix words from every vowel together in a single practice list and see if your child reads them with equal ease, regardless of which vowel comes before the 'ck.'",
    ],
    commonErrors: [
      "Trying to sound out 'c' and 'k' as two separate sounds",
      "Using 'ck' after a long vowel or consonant, where it does not belong",
      "Confusing which vowel comes before ck in similar-looking words",
    ],
    relatedSlugs: ["ack-family", "ock-family", "uck-family"],
  },
  {
    slug: "ng-digraph",
    pattern: "ng",
    displayName: "NG Digraph",
    category: "digraph",
    gradeLevel: "Grade 1",
    words: [
      "king", "song", "ring", "hang", "sing", "long", "bang",
      "wing", "gong", "rang", "strong", "swing",
    ],
    sampleSentences: [
      "The king can sing a long song.",
      "Ring the gong, hear it bang.",
      "A strong wing can swing.",
      "Hang the ring, then sing.",
    ],
    teachingNotes: [
      "Like 'ck,' the digraph 'ng' is best understood after your child has already met it inside individual word families like -ang, -ing, -ong, and -ung — this entry is the chance to name the pattern explicitly and confirm it transfers across every vowel. 'Ng' makes a single nasal sound (air moving through the nose) that is genuinely different from either 'n' or 'g' said alone, which is why trying to sound it out letter by letter never quite works.",
      "A simple physical check: have your child hold their nose lightly while saying a word like 'sing' — they should feel the sound change or get blocked, since 'ng' is a nasal sound made partly through the nose. This kind of concrete, physical demonstration often does more to cement the concept than verbal explanation alone.",
    ],
    commonErrors: [
      "Splitting 'ng' into separate n and g sounds",
      "Confusing -ang, -ing, -ong, and -ung endings when reading quickly",
      "Dropping the nasal quality and reading it as a plain g sound",
    ],
    relatedSlugs: ["ing-family", "ang-family", "ong-family"],
  },

  // ============================================================
  // BLENDS — L-blends
  // ============================================================
  {
    slug: "bl-blend",
    pattern: "bl",
    displayName: "BL Blend",
    category: "blend",
    gradeLevel: "Grade 1",
    words: [
      "black", "blue", "blob", "block", "blend", "blank", "bloom",
      "blast", "blink", "blade", "bless", "bloat",
    ],
    sampleSentences: [
      "The black blob will bloom.",
      "Blend the blue blank paper.",
      "Blink at the blade, then bless.",
      "A blast made the block bloat.",
    ],
    teachingNotes: [
      "'Bl' is a true consonant blend, which means both the /b/ and the /l/ sounds are still audible when said together quickly — this is the key difference from a digraph like 'sh,' where the individual letter sounds disappear entirely. Have your child say /b/ and /l/ slowly and separately first, then speed them up until they naturally glide into 'bl,' rather than jumping straight to the fast version.",
      "Color words ('black,' 'blue') and common classroom vocabulary ('block,' 'blend') make this blend easy to fold into everyday conversation well before a dedicated worksheet session — pointing at a blue block and sounding out both words together is genuine, low-pressure practice.",
    ],
    commonErrors: [
      "Dropping the l and reading 'black' as 'back'",
      "Inserting an extra vowel sound between b and l",
      "Confusing 'bl' with 'br' words",
    ],
    relatedSlugs: ["cl-blend", "fl-blend", "gl-blend"],
  },
  {
    slug: "cl-blend",
    pattern: "cl",
    displayName: "CL Blend",
    category: "blend",
    gradeLevel: "Grade 1",
    words: [
      "clap", "clip", "clock", "class", "clean", "cloud", "climb",
      "close", "club", "clown", "clay", "cling",
    ],
    sampleSentences: [
      "Clap and clip by the clock.",
      "Clean the cloud-gray class.",
      "The clown will climb and cling.",
      "Close the club near the clay.",
    ],
    teachingNotes: [
      "'Cl' blends the /k/ sound of c with /l/, and it is worth noting that this is the same /k/ sound spelled with a plain c, not the 'ck' spelling your child has seen in word families — c at the start of a blend never takes the extra k. As with all blends, both sounds stay audible: a child who reads 'clap' as 'cap' is skipping the l, which is the single most common blend error at this stage.",
      "'Climb' is worth a special note: the b at the end is completely silent, a leftover from older English spelling that did not simplify over time. Simply tell your child directly that the b is silent here rather than expecting them to discover it — a small number of English words like this are genuinely irregular and are best taught as direct exceptions.",
    ],
    commonErrors: [
      "Dropping the l and reading 'clap' as 'cap'",
      "Trying to pronounce the silent b in 'climb'",
      "Confusing 'cl' with 'cr' words",
    ],
    relatedSlugs: ["bl-blend", "fl-blend", "sl-blend"],
  },
  {
    slug: "fl-blend",
    pattern: "fl",
    displayName: "FL Blend",
    category: "blend",
    gradeLevel: "Grade 1",
    words: [
      "flag", "flat", "flip", "flop", "fly", "flame", "float",
      "flash", "fluff", "flute", "flew", "flock",
    ],
    sampleSentences: [
      "The flag is flat, but it can fly.",
      "Flip and flop by the flame.",
      "Float the flute in a flash.",
      "The flock flew with fluff.",
    ],
    teachingNotes: [
      "'Fl' combines /f/ and /l/, two sounds that are both made with the tongue and lips in fairly relaxed positions, which usually makes this blend a little easier for children to produce smoothly than blends involving a hard stop consonant like /b/ or /k/. Even so, watch for children who drop the l and read 'flag' as 'fag' or 'flat' as 'fat' — the fix is the same as with every blend: slow down and practice both sounds together before speeding up.",
      "This blend includes 'fly' and 'flew,' two forms of the same irregular verb, which is a nice opportunity to point out that spelling and sound stay consistent even when grammar gets more complicated — 'fly' and 'flew' both clearly start with the fl blend even though one is present tense and one is past.",
    ],
    commonErrors: [
      "Dropping the l and reading 'flag' as 'fag' or 'flat' as 'fat'",
      "Confusing 'fl' with 'fr' words",
      "Rushing the blend and swallowing the vowel that follows",
    ],
    relatedSlugs: ["bl-blend", "cl-blend", "gl-blend"],
  },
  {
    slug: "gl-blend",
    pattern: "gl",
    displayName: "GL Blend",
    category: "blend",
    gradeLevel: "Grade 1",
    words: [
      "glad", "glass", "glow", "glue", "globe", "gleam", "glide",
      "glitter", "gloom", "glare",
    ],
    sampleSentences: [
      "I am glad about the glass.",
      "The globe will glow and gleam.",
      "Glue the glitter, then glide.",
      "A glare cuts through the gloom.",
    ],
    teachingNotes: [
      "'Gl' blends /g/ and /l/, and because g can also sometimes make a soft /j/ sound in other words (as in 'giant'), it is worth confirming your child knows that g is always hard (as in 'go') at the start of a blend like this — soft g essentially never appears before a consonant. 'Glad' is a common, useful feeling word that makes an easy, motivating entry point into this blend.",
      "Several -gl words describe light or shine ('glow,' 'gleam,' 'glitter,' 'glare'), which gives a nice opportunity for a themed practice session — talk about all the ways things can shine while practicing the words that describe it, tying vocabulary building directly to the phonics lesson.",
    ],
    commonErrors: [
      "Dropping the l and reading 'glad' as 'gad'",
      "Confusing 'gl' with 'gr' words",
      "Applying a soft g sound instead of the correct hard g",
    ],
    relatedSlugs: ["bl-blend", "cl-blend", "gr-blend"],
  },
  {
    slug: "pl-blend",
    pattern: "pl",
    displayName: "PL Blend",
    category: "blend",
    gradeLevel: "Grade 1",
    words: [
      "plan", "play", "plug", "plum", "plane", "plant", "plate",
      "please", "plow", "plot", "plus", "plump",
    ],
    sampleSentences: [
      "Plan to play with a plum.",
      "Plant the plate, please.",
      "The plane will plow and plot.",
      "Plus, plug in the plump one.",
    ],
    teachingNotes: [
      "'Pl' blends /p/ and /l/, and 'play' is one of the most emotionally motivating words in a young child's vocabulary — most kids will happily practice reading and writing a word connected so directly to something they love doing. Use that built-in motivation as a launching point before moving through the rest of the list.",
      "'Please' is worth a small note since the 'ea' inside it makes a long e sound rather than following a pattern your child has learned yet — treat it as a sight word for now if vowel teams have not been covered, and revisit it once the 'ea' vowel team is formally introduced.",
    ],
    commonErrors: [
      "Dropping the l and reading 'plan' as 'pan'",
      "Confusing 'pl' with 'pr' words",
      "Misreading the vowel team in 'please' before it has been taught",
    ],
    relatedSlugs: ["bl-blend", "cl-blend", "sl-blend"],
  },
  {
    slug: "sl-blend",
    pattern: "sl",
    displayName: "SL Blend",
    category: "blend",
    gradeLevel: "Grade 1",
    words: [
      "sled", "slip", "slide", "sleep", "slow", "slot", "slam",
      "sly", "slug", "sleeve", "slice", "slim",
    ],
    sampleSentences: [
      "Slide down slow, then sleep.",
      "Slip the slug in the slot.",
      "Slam the sleeve, slice it thin.",
      "A sly slug is slim.",
    ],
    teachingNotes: [
      "'Sl' blends /s/ and /l/, both sounds that are relatively easy for young children to sustain and hear clearly, which usually makes this one of the more approachable s-blends to teach. 'Slide' and 'sled' both connect to playground and winter activities that most children have real experience with, giving an easy hook into the lesson.",
      "As with every s-blend, if your child is dropping the second consonant (saying 'sip' for 'slip'), have them practice holding the /s/ sound a beat longer than usual before releasing into the rest of the word — exaggerating the first sound briefly often makes the second consonant easier to hear and include.",
    ],
    commonErrors: [
      "Dropping the l and reading 'slip' as 'sip'",
      "Confusing 'sl' with 'sw' or 'st' words",
      "Rushing through and losing the second consonant sound",
    ],
    relatedSlugs: ["bl-blend", "sp-blend", "st-blend"],
  },

  // ============================================================
  // BLENDS — R-blends
  // ============================================================
  {
    slug: "br-blend",
    pattern: "br",
    displayName: "BR Blend",
    category: "blend",
    gradeLevel: "Grade 1",
    words: [
      "brag", "brush", "brown", "bread", "brick", "bring", "broom",
      "brave", "break", "bridge", "branch", "bright",
    ],
    sampleSentences: [
      "Brag about the brown brick.",
      "Bring the broom, then brush.",
      "Break the bread, be brave.",
      "The bright bridge has a branch.",
    ],
    teachingNotes: [
      "'Br' is an r-blend, a category that tends to be harder for children than l-blends because the American English r sound involves a distinctive tongue curl that many kids are still refining well into first grade. If your child is substituting a /w/ sound for r (a very common and normal developmental pattern, saying 'bwown' for 'brown'), that usually resolves naturally with age and does not need special phonics intervention.",
      "'Bread' and 'break' both use the 'ea' vowel team with an unexpected short-e sound rather than the more common long-e sound, so treat those two as slight exceptions until vowel teams are covered in more depth. Focus most of your practice time on the fully regular words in this list: 'brag,' 'brick,' 'bring,' and 'brown.'",
    ],
    commonErrors: [
      "Substituting a w sound for r, saying 'bwown' for 'brown'",
      "Dropping the r and reading 'brag' as 'bag'",
      "Confusing 'br' with 'bl' words",
    ],
    relatedSlugs: ["cr-blend", "dr-blend", "gr-blend"],
  },
  {
    slug: "cr-blend",
    pattern: "cr",
    displayName: "CR Blend",
    category: "blend",
    gradeLevel: "Grade 1",
    words: [
      "crab", "crib", "crop", "cry", "crown", "cream", "crawl",
      "crash", "crisp", "cradle", "crack", "creek",
    ],
    sampleSentences: [
      "The crab will crawl and cry.",
      "Crash the crop by the crib.",
      "Cream is crisp near the creek.",
      "A crown sits in the cradle.",
    ],
    teachingNotes: [
      "'Cr' blends the hard /k/ sound of c with r, and like every r-blend it is common for young children to soften the r or replace it with a w-like glide while their speech sounds are still developing — this is typically a normal articulation stage rather than a reading problem. 'Crab' is an especially motivating word for this blend given how popular sea-creature vocabulary tends to be with young children.",
      "'Crash' combines this blend with the digraph 'sh' at the end, so it is a good integrated practice word once both patterns have been taught separately. If your child struggles specifically with 'crash' but not with simpler cr-words, the breakdown is likely at the ending digraph rather than the beginning blend.",
    ],
    commonErrors: [
      "Substituting a w sound for r",
      "Dropping the r and reading 'crab' as 'cab'",
      "Confusing 'cr' with 'cl' words",
    ],
    relatedSlugs: ["br-blend", "dr-blend", "tr-blend"],
  },
  {
    slug: "dr-blend",
    pattern: "dr",
    displayName: "DR Blend",
    category: "blend",
    gradeLevel: "Grade 1",
    words: [
      "drum", "drop", "dress", "draw", "dream", "drive", "drink",
      "drag", "dry", "drift", "drain", "drip",
    ],
    sampleSentences: [
      "Drum and drop the dress.",
      "Draw a dream, then drive.",
      "Drink and drag it dry.",
      "The drain will drift and drip.",
    ],
    teachingNotes: [
      "'Dr' is unusual among the r-blends because in fast, natural speech it often sounds closer to a 'j' or 'jr' sound than a crisp /d/ plus /r/ — say 'drum' and 'jrum' side by side and notice how similar they can sound. This is completely normal English pronunciation, not a mistake, so do not correct a child who reads it this way as long as the meaning and spelling connection stay intact.",
      "Because that natural sound shift can confuse the spelling-to-sound connection, it helps to point at the letters while sounding out dr-words slowly during practice, reminding your child that even though it can sound like 'jr' when spoken quickly, it is always spelled with d and r together.",
    ],
    commonErrors: [
      "Confusing the natural dr-to-jr sound shift with a spelling error",
      "Dropping the r and reading 'drum' as 'dum'",
      "Confusing 'dr' with 'tr' words",
    ],
    relatedSlugs: ["cr-blend", "tr-blend", "fr-blend"],
  },
  {
    slug: "fr-blend",
    pattern: "fr",
    displayName: "FR Blend",
    category: "blend",
    gradeLevel: "Grade 1",
    words: [
      "frog", "from", "fresh", "free", "fry", "front", "frown",
      "friend", "fruit", "frost", "freeze", "fright",
    ],
    sampleSentences: [
      "The frog is free and fresh.",
      "My friend will fry the fruit.",
      "Frost is in front, do not frown.",
      "Freeze, then fright will pass.",
    ],
    teachingNotes: [
      "'Fr' blends /f/ and r, and 'frog' tends to be one of the most eagerly practiced words in this list for the same reason -og and -ig family words are popular: animals capture attention. 'From' and 'friend' are both extremely high-frequency words that will appear constantly in your child's early reading, so give them extra repetition even though 'from' in particular has a slightly less obvious vowel sound than the spelling suggests.",
      "'Friend' is a genuinely irregular word — the 'ie' does not follow the usual vowel-team rules your child will learn later — so it is best taught as a memorized sight word rather than something to sound out from first principles. Point that out directly so your child does not get frustrated trying to apply phonics rules that do not quite apply here.",
    ],
    commonErrors: [
      "Dropping the r and reading 'frog' as 'fog'",
      "Trying to sound out 'friend' with regular vowel-team rules",
      "Confusing 'fr' with 'fl' words",
    ],
    relatedSlugs: ["br-blend", "gr-blend", "og-family"],
  },
  {
    slug: "gr-blend",
    pattern: "gr",
    displayName: "GR Blend",
    category: "blend",
    gradeLevel: "Grade 1",
    words: [
      "grab", "grass", "green", "grow", "grin", "grape", "great",
      "grip", "grand", "groan", "grill", "ground",
    ],
    sampleSentences: [
      "Grab the green grass.",
      "Grow a grape, then grin.",
      "The grand grill is on the ground.",
      "Grip it, do not groan.",
    ],
    teachingNotes: [
      "'Gr' blends the hard /g/ sound with r, and 'green' and 'grass' are both concrete, everyday words that connect easily to time spent outside, which makes for natural, low-pressure practice opportunities beyond a worksheet. As with all r-blends, be patient with children who soften or substitute the r sound, since full mastery of r articulation is still developing for many kids at this age.",
      "'Great' is worth a quick note since its vowel team 'ea' makes a long-a sound here rather than the more common long-e sound found in words like 'read' — an irregular pronunciation worth flagging directly rather than expecting your child to sound it out correctly on the first try.",
    ],
    commonErrors: [
      "Dropping the r and reading 'grab' as 'gab'",
      "Misreading the vowel team in 'great' as a long-e sound",
      "Confusing 'gr' with 'gl' words",
    ],
    relatedSlugs: ["br-blend", "cr-blend", "fr-blend"],
  },
  {
    slug: "pr-blend",
    pattern: "pr",
    displayName: "PR Blend",
    category: "blend",
    gradeLevel: "Grade 1",
    words: [
      "pretty", "press", "prize", "print", "proud", "prince",
      "promise", "practice", "pray", "prep",
    ],
    sampleSentences: [
      "Press print to see the prize.",
      "The proud prince made a promise.",
      "Practice makes you pretty good.",
      "Pray and prep for the prize.",
    ],
    teachingNotes: [
      "'Pr' blends /p/ and r, and it appears in several longer, multisyllable words your child may already recognize by sight from school routines — 'practice,' 'promise,' and 'proud' are common in classroom and storybook vocabulary well before formal decoding of every syllable is expected. Focus on the clean, single-syllable words first ('press,' 'print,' 'prize') to build the blend itself before tackling the longer words.",
      "'Pretty' is a genuinely irregular word — the second syllable does not sound the way its spelling suggests — so treat it as a sight word exception rather than a decoding example, and reassure your child that it is fine to simply memorize a small number of words like this rather than sound out every single one.",
    ],
    commonErrors: [
      "Dropping the r and reading 'press' as 'pess'",
      "Trying to fully sound out the irregular word 'pretty'",
      "Confusing 'pr' with 'pl' words",
    ],
    relatedSlugs: ["tr-blend", "gr-blend", "cr-blend"],
  },
  {
    slug: "tr-blend",
    pattern: "tr",
    displayName: "TR Blend",
    category: "blend",
    gradeLevel: "Grade 1",
    words: [
      "trip", "tree", "truck", "train", "trap", "try", "track",
      "trail", "treat", "trust", "trick", "trot",
    ],
    sampleSentences: [
      "The truck will trip on the track.",
      "Try to trap the trail.",
      "A treat is on the tree.",
      "Trust the trick, then trot.",
    ],
    teachingNotes: [
      "'Tr' is another r-blend that, like 'dr,' often shifts toward a 'ch' or 'chr'-like sound in fast natural speech — say 'truck' and 'chruck' side by side and notice the similarity. This is completely normal spoken English, and pointing at the letters while sounding words out slowly helps your child keep the spelling-sound connection clear even as their natural speech shifts the sound slightly.",
      "'Truck,' 'train,' and 'tree' are all common vehicle and nature words that tend to be highly motivating for young readers, making this one of the more reliably engaging blends to practice. Once your child can read the whole list fluently, try a simple sorting activity: things that move (truck, train, trip) versus things that grow (tree, trail).",
    ],
    commonErrors: [
      "Confusing the natural tr-to-chr sound shift with a spelling error",
      "Dropping the r and reading 'truck' as 'tuck'",
      "Confusing 'tr' with 'dr' words",
    ],
    relatedSlugs: ["dr-blend", "cr-blend", "pr-blend"],
  },

  // ===END-BATCH-4===

  // ===BATCH-5: vowel teams===
  {
    slug: "ai-vowel-team",
    pattern: "ai",
    displayName: "AI Vowel Team",
    category: "vowel-team",
    gradeLevel: "Grade 1",
    words: [
      "rain", "main", "pain", "gain", "train", "brain", "chain",
      "plain", "mail", "tail", "sail", "nail", "paint", "faint", "wait",
    ],
    sampleSentences: [
      "The train has rain on the tail.",
      "Wait for the mail in the pail.",
      "Paint the plain chain.",
      "My brain feels faint.",
    ],
    teachingNotes: [
      "'Ai' is the clearest example of the rule most children learn as 'two vowels go walking, the first one does the talking' - the a says its own name and the i stays silent. It is one of the more reliable vowel teams in English, which is why it is usually taught first, and it gives a child an early win after the messiness of short vowels.",
      "The important limitation to teach alongside it: 'ai' almost never appears at the end of a word. English uses 'ay' there instead, which is why it is 'rain' but 'play.' If your child writes 'plai,' they have understood the sound correctly and only missed the position rule, so praise the sound and correct the placement rather than treating it as a spelling failure.",
    ],
    commonErrors: [
      "Sounding out both letters as 'ah-ee' instead of one long A",
      "Writing 'ai' at the end of a word where 'ay' belongs",
      "Confusing 'ai' with 'ea', since both can make a long vowel sound",
    ],
    relatedSlugs: ["ay-vowel-team", "ea-vowel-team", "ee-vowel-team"],
  },
  {
    slug: "ay-vowel-team",
    pattern: "ay",
    displayName: "AY Vowel Team",
    category: "vowel-team",
    gradeLevel: "Grade 1",
    words: [
      "day", "may", "say", "way", "play", "stay", "gray",
      "tray", "clay", "pray", "spray", "today", "away", "delay",
    ],
    sampleSentences: [
      "We play in the gray clay today.",
      "Stay away and say the way.",
      "May I spray the tray?",
      "The delay lasted all day.",
    ],
    teachingNotes: [
      "'Ay' makes exactly the same long A sound as 'ai,' so the sound itself is not the lesson - the position is. 'Ay' lives at the end of a word or syllable, 'ai' lives in the middle. Teaching these two together as a pair, rather than weeks apart, is what makes the rule stick, because the whole point of each is where the other cannot go.",
      "Because 'ay' words are so common in everyday speech ('day,' 'play,' 'say'), many children already recognise several by sight before they can decode them. Use that: ask which part of 'play' makes the /ay/ sound, and let them discover the team inside a word they already know rather than introducing it cold.",
    ],
    commonErrors: [
      "Writing 'ai' at the end of a word instead of 'ay'",
      "Reading the y as a separate consonant sound",
      "Assuming every word ending in y uses the long A sound",
    ],
    relatedSlugs: ["ai-vowel-team", "oy-vowel-team", "ee-vowel-team"],
  },
  {
    slug: "ee-vowel-team",
    pattern: "ee",
    displayName: "EE Vowel Team",
    category: "vowel-team",
    gradeLevel: "Grade 1",
    words: [
      "see", "bee", "tree", "free", "three", "green", "seen",
      "keep", "sleep", "sheep", "deep", "feet", "meet", "street", "week",
    ],
    sampleSentences: [
      "Three green sheep sleep in the tree.",
      "I see a bee on my feet.",
      "Keep the street free this week.",
      "We meet in the deep green.",
    ],
    teachingNotes: [
      "'Ee' is the most dependable vowel team in English. It says long E essentially every time, with no meaningful exceptions a young reader will encounter, which makes it an excellent confidence builder right after the short vowels. If a child is discouraged by how irregular English feels, this is a good pattern to spend a week on.",
      "It also combines readily with digraphs and blends the child already knows - 'sheep' needs 'sh' plus 'ee' plus 'p,' 'street' needs 'str' plus 'ee' plus 't.' Once 'ee' is solid, use it as the vowel in blending practice so the child is only juggling one new element at a time.",
    ],
    commonErrors: [
      "Reading 'ee' as two separate short E sounds",
      "Confusing 'ee' with 'ea', which shares the sound but is far less predictable",
      "Dropping one e when spelling, writing 'sen' for 'seen'",
    ],
    relatedSlugs: ["ea-vowel-team", "ie-vowel-team", "ai-vowel-team"],
  },
  {
    slug: "ea-vowel-team",
    pattern: "ea",
    displayName: "EA Vowel Team",
    category: "vowel-team",
    gradeLevel: "Grade 1–2",
    words: [
      "eat", "sea", "tea", "read", "beach", "teach", "clean",
      "dream", "cream", "bread", "head", "ready", "heavy", "great", "break",
    ],
    sampleSentences: [
      "We eat bread by the sea.",
      "Clean the beach, then read.",
      "I dream of cream and tea.",
      "Get ready for a great break.",
    ],
    teachingNotes: [
      "'Ea' is where the 'two vowels go walking' rule starts to break down, and it is better to tell a child that directly than to let them discover it as a failure. It makes long E most of the time ('eat,' 'dream'), short E fairly often ('bread,' 'head'), and long A in a small stubborn group ('great,' 'break,' 'steak').",
      "The practical strategy is flexing: try the long E first because it is most common, and if the word does not sound like a real word you know, try short E instead. Model this out loud - read 'bread' as /breed/, pause, say that is not a word, then switch. Watching an adult flex without embarrassment is what teaches a child that self-correction is normal reading rather than a mistake.",
    ],
    commonErrors: [
      "Reading every 'ea' as long E and giving up when the word sounds wrong",
      "Not knowing to try a second sound when the first attempt fails",
      "Confusing 'ea' and 'ee' when spelling, since they can sound identical",
    ],
    relatedSlugs: ["ee-vowel-team", "ai-vowel-team", "oa-vowel-team"],
  },
  {
    slug: "ie-vowel-team",
    pattern: "ie",
    displayName: "IE Vowel Team",
    category: "vowel-team",
    gradeLevel: "Grade 1–2",
    words: [
      "pie", "tie", "lie", "die", "cried", "tried", "dried",
      "fried", "field", "chief", "brief", "thief", "piece", "believe",
    ],
    sampleSentences: [
      "I tried the pie in the field.",
      "The chief tied a brief knot.",
      "He cried, then fried a piece.",
      "Do not lie to the thief.",
    ],
    teachingNotes: [
      "'Ie' has two jobs and they split fairly cleanly by position. At the end of a short word it says long I ('pie,' 'tie,' 'cried'). In the middle of a word it usually says long E ('field,' 'chief,' 'piece'). Teaching the two groups as separate word sets, rather than as one confusing team, keeps a child from feeling the pattern is arbitrary.",
      "This is also the pattern behind the old 'i before e except after c' rhyme, which is worth mentioning but not leaning on - it has enough exceptions that it misleads as often as it helps. A child who has practiced the two positional groups will decode these words more reliably than one relying on the rhyme.",
    ],
    commonErrors: [
      "Applying the long I sound to middle-of-word 'ie' words like 'field'",
      "Reading 'ie' as two separate vowel sounds",
      "Over-applying the 'i before e' rhyme to words where it does not hold",
    ],
    relatedSlugs: ["ee-vowel-team", "ea-vowel-team", "oe-vowel-team"],
  },
  {
    slug: "oa-vowel-team",
    pattern: "oa",
    displayName: "OA Vowel Team",
    category: "vowel-team",
    gradeLevel: "Grade 1",
    words: [
      "boat", "coat", "goat", "float", "throat", "road", "load",
      "toad", "soap", "soak", "coach", "roast", "toast", "coal", "foam",
    ],
    sampleSentences: [
      "The goat rode a boat down the road.",
      "Soak the coat in soap.",
      "We roast toast for the coach.",
      "A toad can float on foam.",
    ],
    teachingNotes: [
      "'Oa' behaves almost as reliably as 'ee' - it says long O nearly every time a beginning reader will meet it. Like 'ai,' it sits in the middle of words and effectively never at the end, where English switches to 'ow' or 'oe' instead. That parallel is worth pointing out explicitly if your child already knows the ai/ay pair, because it is the same rule with different letters.",
      "'Oa' words also happen to be unusually easy to picture - boat, goat, coat, toad, soap - which makes them good candidates for drawing or acting out. For a child who is decoding accurately but not yet reading for meaning, pairing each word with an image helps close that gap.",
    ],
    commonErrors: [
      "Sounding out both letters as 'oh-ah'",
      "Writing 'oa' at the end of a word where 'ow' or 'oe' belongs",
      "Confusing 'oa' with 'ou', which looks similar but sounds nothing alike",
    ],
    relatedSlugs: ["oe-vowel-team", "ow-vowel-team", "ea-vowel-team"],
  },
  {
    slug: "oe-vowel-team",
    pattern: "oe",
    displayName: "OE Vowel Team",
    category: "vowel-team",
    gradeLevel: "Grade 1–2",
    words: [
      "toe", "hoe", "doe", "foe", "woe", "roe", "goes",
      "toes", "hoes", "does", "aloe", "tiptoe", "oboe",
    ],
    sampleSentences: [
      "The doe has a sore toe.",
      "He goes to hoe the row.",
      "Ten toes tiptoe past.",
      "Aloe helps a sore toe.",
    ],
    teachingNotes: [
      "'Oe' is a small team - there are not many words - but it fills a specific gap: it is one of the ways English spells long O at the end of a word, where 'oa' cannot go. Because the set is short, it is realistic to simply learn the handful of words rather than drill a rule.",
      "Watch for 'does,' which looks like it belongs here and does not - it is pronounced /duz/ and is a high-frequency sight word. Point that out as an exception the first time it appears rather than letting a child repeatedly try to decode it with the long O sound.",
    ],
    commonErrors: [
      "Trying to decode 'does' with the long O sound",
      "Confusing 'oe' with 'oa' when spelling end-of-word long O",
      "Reading the e as a separate syllable",
    ],
    relatedSlugs: ["oa-vowel-team", "ow-vowel-team", "ue-vowel-team"],
  },
  {
    slug: "ue-vowel-team",
    pattern: "ue",
    displayName: "UE Vowel Team",
    category: "vowel-team",
    gradeLevel: "Grade 1–2",
    words: [
      "blue", "clue", "glue", "true", "due", "sue", "cue",
      "hue", "value", "rescue", "tissue", "statue", "argue", "continue",
    ],
    sampleSentences: [
      "The blue glue is true.",
      "I found a clue in the tissue.",
      "The statue is due for rescue.",
      "Do not argue about the value.",
    ],
    teachingNotes: [
      "'Ue' makes two closely related sounds: a plain /oo/ in 'blue' and 'glue,' and a /yoo/ in 'cue,' 'hue,' and 'rescue.' Most children slide between the two without noticing, and for reading purposes that is fine - the distinction matters more for spelling and pronunciation precision than for decoding.",
      "Like 'oe,' this team lives at the end of words and syllables. It also shows up as the final piece of many longer words a child meets in second grade and beyond ('value,' 'continue,' 'argue'), so it is worth practicing in multisyllabic words rather than only in short ones.",
    ],
    commonErrors: [
      "Reading 'ue' as two separate vowel sounds",
      "Confusing 'ue' with 'ui', which looks similar and often sounds the same",
      "Missing 'ue' at the end of longer words like 'continue'",
    ],
    relatedSlugs: ["ui-vowel-team", "oo-vowel-team", "oe-vowel-team"],
  },
  {
    slug: "ui-vowel-team",
    pattern: "ui",
    displayName: "UI Vowel Team",
    category: "vowel-team",
    gradeLevel: "Grade 2",
    words: [
      "fruit", "suit", "juice", "cruise", "bruise", "suitcase",
      "recruit", "pursuit", "nuisance", "build", "built", "guilt", "guitar",
    ],
    sampleSentences: [
      "The fruit juice is in the suitcase.",
      "He built a suit for the cruise.",
      "A bruise is a nuisance.",
      "She built a guitar.",
    ],
    teachingNotes: [
      "'Ui' is a small and genuinely tricky team. In its main group it says /oo/ - 'fruit,' 'juice,' 'suit' - which is the same sound as 'ue' and 'oo,' so it is really a spelling pattern to memorise rather than a decoding rule to apply.",
      "There is a second group where the u is silent and the i says short i: 'build,' 'built,' 'guilt,' 'guitar.' These are common enough words that a child will hit them early, and the honest framing is that the u is doing a job left over from older spellings rather than making a sound. Treat this second group as sight words and the pattern gets much less frustrating.",
    ],
    commonErrors: [
      "Trying to make the u audible in 'build' and 'guitar'",
      "Confusing 'ui' with 'ue' when spelling the /oo/ sound",
      "Sounding out both letters separately",
    ],
    relatedSlugs: ["ue-vowel-team", "oo-vowel-team", "oi-vowel-team"],
  },
  {
    slug: "oo-vowel-team",
    pattern: "oo",
    displayName: "OO Vowel Team",
    category: "vowel-team",
    gradeLevel: "Grade 1",
    words: [
      "moon", "soon", "food", "room", "pool", "cool", "tool",
      "zoo", "book", "look", "took", "cook", "good", "wood", "foot",
    ],
    sampleSentences: [
      "Look at the good book in the room.",
      "Soon we cook food by the pool.",
      "The moon is cool at the zoo.",
      "He took a tool made of wood.",
    ],
    teachingNotes: [
      "'Oo' has two sounds and no rule tells you which is which: the long /oo/ in 'moon' and 'food,' and the short /oo/ in 'book' and 'good.' This is one of the first places a child meets genuine ambiguity in English, and how you frame it matters. Presented as a rule with exceptions it feels unfair; presented as a team with two jobs it feels manageable.",
      "Teach flexing explicitly here. Try the 'moon' sound first, and if the result is not a real word, try the 'book' sound. Sorting activities work especially well for this pattern - two columns, moon and book at the top, and the child files each new word by ear. That is far more effective than trying to memorise which words belong to which group.",
    ],
    commonErrors: [
      "Using the 'moon' sound for every 'oo' word and reading 'book' as /booke/",
      "Not attempting the second sound when the first one produces a non-word",
      "Confusing 'oo' with 'ou' when spelling",
    ],
    relatedSlugs: ["ue-vowel-team", "ui-vowel-team", "ou-vowel-team"],
  },
  {
    slug: "ow-vowel-team",
    pattern: "ow",
    displayName: "OW Vowel Team",
    category: "vowel-team",
    gradeLevel: "Grade 1–2",
    words: [
      "cow", "how", "now", "wow", "down", "town", "brown",
      "crown", "clown", "snow", "slow", "grow", "show", "know", "yellow",
    ],
    sampleSentences: [
      "The brown cow is in town now.",
      "Snow will grow slow.",
      "Show me how the clown sat down.",
      "I know the yellow crown.",
    ],
    teachingNotes: [
      "'Ow' is the other two-sound team, and it splits between the /ow/ in 'cow' and the long O in 'snow.' Unlike 'oo,' there is a weak positional tendency worth knowing: 'ow' at the end of a word more often says long O ('snow,' 'grow,' 'yellow'), while 'ow' in the middle more often says /ow/ ('down,' 'brown'). It is a tendency, not a rule, but it gives a child a sensible first guess.",
      "Rhyming pairs make the ambiguity concrete rather than confusing. Put 'cow' and 'snow' side by side, or 'now' and 'know,' and have your child read both aloud. Seeing that identical letters can behave differently, in a controlled pair rather than mid-sentence, takes the surprise out of it.",
    ],
    commonErrors: [
      "Reading every 'ow' as the /ow/ in 'cow', so 'snow' becomes /snau/",
      "Not flexing to the second sound when the word does not make sense",
      "Confusing 'ow' with 'ou', which shares the /ow/ sound",
    ],
    relatedSlugs: ["ou-vowel-team", "oa-vowel-team", "oe-vowel-team"],
  },
  {
    slug: "ou-vowel-team",
    pattern: "ou",
    displayName: "OU Vowel Team",
    category: "vowel-team",
    gradeLevel: "Grade 1–2",
    words: [
      "out", "loud", "cloud", "proud", "found", "round", "sound",
      "ground", "mouth", "south", "house", "mouse", "count", "shout", "about",
    ],
    sampleSentences: [
      "A loud mouse ran out of the house.",
      "We found a round cloud.",
      "Shout about the sound.",
      "The proud crowd sat on the ground.",
    ],
    teachingNotes: [
      "'Ou' most often makes the /ow/ sound - the noise you make when you stub a toe - which is a useful hook because children remember it physically. 'Out,' 'loud,' 'house,' and 'shout' all follow it, and that covers the large majority of 'ou' words a beginning reader meets.",
      "It shares that sound with 'ow,' which creates a spelling problem rather than a reading one: a child who hears /ow/ has to choose between two spellings. The rough guide is that 'ou' sits inside a word and 'ow' finishes it, which handles 'house' versus 'cow' correctly most of the time. There are other 'ou' sounds in words like 'you,' 'soup,' and 'touch,' but those are better handled as sight words for now.",
    ],
    commonErrors: [
      "Sounding out o and u separately",
      "Choosing 'ow' when spelling a middle-of-word /ow/ sound",
      "Being thrown by irregulars like 'you' and 'touch'",
    ],
    relatedSlugs: ["ow-vowel-team", "oo-vowel-team", "oi-vowel-team"],
  },
  {
    slug: "oi-vowel-team",
    pattern: "oi",
    displayName: "OI Vowel Team",
    category: "vowel-team",
    gradeLevel: "Grade 1–2",
    words: [
      "oil", "boil", "coil", "soil", "spoil", "coin", "join",
      "point", "joint", "noise", "voice", "choice", "moist", "avoid",
    ],
    sampleSentences: [
      "The coin fell in the soil.",
      "Boil the oil, then join in.",
      "Point at the loud noise.",
      "Avoid a moist joint.",
    ],
    teachingNotes: [
      "'Oi' is a diphthong, which means the mouth actually moves during the sound - it starts near 'oh' and glides toward 'ee.' Having a child say it slowly and feel their lips change shape makes it stick better than treating it as a single fixed sound, because the movement is the sound.",
      "Usefully, 'oi' is reliable: it makes this one sound essentially every time, with no second job to flex to. After the ambiguity of 'oo,' 'ow,' and 'ea,' this pattern and its partner 'oy' are a relief, and they are worth teaching right after those harder teams for exactly that reason.",
    ],
    commonErrors: [
      "Reading 'oi' as a long O followed by a short i",
      "Writing 'oi' at the end of a word where 'oy' belongs",
      "Confusing 'oi' with 'ou'",
    ],
    relatedSlugs: ["oy-vowel-team", "ou-vowel-team", "ui-vowel-team"],
  },
  {
    slug: "oy-vowel-team",
    pattern: "oy",
    displayName: "OY Vowel Team",
    category: "vowel-team",
    gradeLevel: "Grade 1–2",
    words: [
      "boy", "toy", "joy", "soy", "coy", "ploy", "enjoy",
      "annoy", "employ", "destroy", "royal", "loyal", "voyage", "oyster",
    ],
    sampleSentences: [
      "The boy found joy in a toy.",
      "Do not annoy the loyal boy.",
      "I enjoy the royal voyage.",
      "Soy will not destroy it.",
    ],
    teachingNotes: [
      "'Oy' is the end-of-word partner to 'oi,' exactly as 'ay' partners 'ai' and 'ow' partners 'ou.' Same sound, different position. By the time a child reaches this team they have usually met that pattern twice already, so naming it out loud - 'this is the same trick again' - turns a new item into a familiar structure.",
      "Because 'boy,' 'toy,' and 'joy' are among the first words many children can read, this team is a good place to practice reading longer words. 'Enjoy,' 'annoy,' and 'destroy' are simply a familiar chunk with a syllable in front, which is a gentle introduction to multisyllabic decoding.",
    ],
    commonErrors: [
      "Writing 'oi' at the end of a word instead of 'oy'",
      "Reading the y as a consonant",
      "Missing 'oy' inside longer words such as 'employ'",
    ],
    relatedSlugs: ["oi-vowel-team", "ay-vowel-team", "ou-vowel-team"],
  },
  {
    slug: "au-vowel-team",
    pattern: "au",
    displayName: "AU Vowel Team",
    category: "vowel-team",
    gradeLevel: "Grade 2",
    words: [
      "haul", "maul", "author", "autumn", "auto", "August",
      "sauce", "cause", "pause", "launch", "laundry", "haunt", "fault", "vault",
    ],
    sampleSentences: [
      "The author will pause in August.",
      "Haul the laundry to the vault.",
      "The sauce was not my fault.",
      "Autumn winds haunt the launch.",
    ],
    teachingNotes: [
      "'Au' makes the /aw/ sound heard in 'haul' and 'sauce.' Depending on regional accent this may sound identical to the short o in 'hot' or noticeably different, and both are correct - if your family says 'caught' and 'cot' the same way, do not try to teach a distinction your child does not hear.",
      "'Au' sits at the beginning or middle of words and hands off to 'aw' at the end, which is the same positional pairing seen in ai/ay and oi/oy. Since this is the fourth time that structure appears, most children can predict the rule before being told, and asking them to guess is a better use of the moment than explaining it.",
    ],
    commonErrors: [
      "Sounding out a and u separately",
      "Writing 'au' at the end of a word instead of 'aw'",
      "Confusing 'au' with 'ou'",
    ],
    relatedSlugs: ["aw-vowel-team", "ou-vowel-team", "oi-vowel-team"],
  },
  {
    slug: "aw-vowel-team",
    pattern: "aw",
    displayName: "AW Vowel Team",
    category: "vowel-team",
    gradeLevel: "Grade 1–2",
    words: [
      "saw", "paw", "jaw", "law", "raw", "claw", "draw",
      "straw", "yawn", "lawn", "dawn", "crawl", "shawl", "hawk", "awful",
    ],
    sampleSentences: [
      "I saw a hawk on the lawn.",
      "The cat has a raw paw and a claw.",
      "Draw a straw at dawn.",
      "He let out an awful yawn.",
    ],
    teachingNotes: [
      "'Aw' is the end-of-word partner to 'au' and makes the same /aw/ sound. It is the more common of the two in words young children actually use - 'saw,' 'paw,' 'draw' - so many children learn 'aw' first and meet 'au' later, which is a sensible order.",
      "Note that 'aw' also appears before l and n inside words ('crawl,' 'lawn,' 'yawn'), so the end-of-word guideline is a tendency rather than an absolute. If your child is confidently decoding 'saw' but stumbling on 'crawl,' the issue is usually the blend at the front rather than the vowel team.",
    ],
    commonErrors: [
      "Reading the w as a consonant sound",
      "Writing 'au' at the end of a word instead of 'aw'",
      "Struggling with 'aw' before l and n as in 'crawl' and 'lawn'",
    ],
    relatedSlugs: ["au-vowel-team", "ow-vowel-team", "ou-vowel-team"],
  },
  // ===END-BATCH-5===

  // ===BATCH-6: s-blends and tw===
  {
    slug: "st-blend",
    pattern: "st",
    displayName: "ST Blend",
    category: "blend",
    gradeLevel: "Kindergarten–Grade 1",
    words: [
      "stop", "step", "stem", "stick", "still", "sting", "star",
      "start", "stand", "storm", "stone", "fast", "last", "nest", "best",
    ],
    sampleSentences: [
      "Stop and stand by the stone.",
      "The best nest is on a stick.",
      "Run fast past the last star.",
      "A storm will start still.",
    ],
    teachingNotes: [
      "'St' is one of the most useful blends to teach early because it appears at both ends of words. A child meets it at the start in 'stop' and 'star,' and at the end in 'fast,' 'nest,' and 'best.' Practising both positions in the same session prevents the common situation where a child decodes 'stop' fluently but stalls on 'best.'",
      "Because both letters keep their sounds, the work is purely about saying them quickly enough that they feel like one motion. If your child inserts a vowel and says 'suh-top,' slow the word down, then speed it up gradually rather than correcting the vowel directly. The extra sound disappears on its own once the blend is fast enough.",
    ],
    commonErrors: [
      "Adding a vowel between the sounds, saying 'suh-top' for 'stop'",
      "Dropping the s and reading 'stop' as 'top'",
      "Missing the blend when it lands at the end of a word like 'nest'",
    ],
    relatedSlugs: ["sp-blend", "sk-blend", "sn-blend"],
  },
  {
    slug: "sp-blend",
    pattern: "sp",
    displayName: "SP Blend",
    category: "blend",
    gradeLevel: "Kindergarten–Grade 1",
    words: [
      "spin", "spot", "spun", "spell", "spend", "speak", "spoon",
      "sport", "space", "spider", "wasp", "gasp", "crisp", "grasp",
    ],
    sampleSentences: [
      "The spider spun in a spot.",
      "Spend a spoon on space.",
      "I gasp at the crisp wasp.",
      "Speak and spell the sport.",
    ],
    teachingNotes: [
      "'Sp' works exactly like 'st': two sounds, both audible, said quickly. It also appears at the end of words, though less often - 'wasp,' 'gasp,' 'crisp.' Children who have already mastered 'st' usually pick this up in a single session, so it is a good one to pair with 'st' rather than teach separately.",
      "Watch for the p sound getting swallowed. In casual speech the p in 'sp' is unaspirated, meaning it comes out softer than the p in 'pig,' and some children hear it as a b. If your child writes 'sbin' for 'spin,' their ear is working correctly and the spelling convention is what needs teaching.",
    ],
    commonErrors: [
      "Writing b for the p sound, as in 'sbin' for 'spin'",
      "Inserting a vowel, saying 'suh-pin'",
      "Missing 'sp' at the end of words like 'crisp'",
    ],
    relatedSlugs: ["st-blend", "sk-blend", "sm-blend"],
  },
  {
    slug: "sk-blend",
    pattern: "sk",
    displayName: "SK Blend",
    category: "blend",
    gradeLevel: "Kindergarten–Grade 1",
    words: [
      "skip", "skin", "skid", "sky", "skate", "skunk", "skill",
      "skirt", "ask", "desk", "mask", "task", "risk", "dusk", "whisk",
    ],
    sampleSentences: [
      "Skip past the desk at dusk.",
      "The skunk has thin skin.",
      "Ask about the mask and the task.",
      "I skate in the sky with skill.",
    ],
    teachingNotes: [
      "'Sk' is worth teaching alongside the spelling 'sc,' which makes the identical sound in 'scat' and 'scar.' A child does not need a rule for choosing between them at this stage; they need to know that two spellings can produce the same blend, so neither one surprises them mid-word.",
      "End-position 'sk' is very common and often harder than the start: 'ask,' 'desk,' 'mask,' 'task.' 'Ask' in particular is a word many children reverse to 'aks,' which is a normal developmental pattern rather than a reading problem. Point at the letters in order and blend slowly, without making it a correction.",
    ],
    commonErrors: [
      "Reversing 'ask' to 'aks'",
      "Not recognising that 'sc' can make the same sound",
      "Dropping the k at the end of words like 'desk'",
    ],
    relatedSlugs: ["st-blend", "sp-blend", "sn-blend"],
  },
  {
    slug: "sm-blend",
    pattern: "sm",
    displayName: "SM Blend",
    category: "blend",
    gradeLevel: "Kindergarten–Grade 1",
    words: [
      "smell", "small", "smart", "smash", "smile", "smoke",
      "smock", "smooth", "smug", "smudge", "smoothie",
    ],
    sampleSentences: [
      "The small smile is smart.",
      "I smell smoke.",
      "Smash the smock, then smile.",
      "That stone is smooth.",
    ],
    teachingNotes: [
      "'Sm' is a small set and only appears at the beginning of words, which makes it one of the easier blends to master. Both sounds are continuants, meaning you can hold each one out, so this is a good blend for a child who struggles to hear the two parts - stretch it into 'ssssmmm' and the seam is obvious.",
      "Because there are only a handful of 'sm' words, most of them common, this is a pattern a child can genuinely finish rather than sample. Reading the whole list in one sitting and knowing you have covered it is motivating in a way that endless practice is not.",
    ],
    commonErrors: [
      "Dropping the s and reading 'small' as 'mall'",
      "Inserting a vowel between the sounds",
      "Confusing 'sm' with 'sn' since both start the same way",
    ],
    relatedSlugs: ["sn-blend", "sp-blend", "sl-blend"],
  },
  {
    slug: "sn-blend",
    pattern: "sn",
    displayName: "SN Blend",
    category: "blend",
    gradeLevel: "Kindergarten–Grade 1",
    words: [
      "snap", "snip", "snug", "snack", "sneak", "sniff", "snow",
      "snail", "snake", "sneeze", "snore", "snout",
    ],
    sampleSentences: [
      "The snake will sneak in the snow.",
      "Snap a snack and sniff.",
      "A snug snail can snore.",
      "I sneeze at the snout.",
    ],
    teachingNotes: [
      "'Sn' pairs naturally with 'sm' - same starting sound, different second letter, both nasal. Teaching them back to back and asking a child to sort words by ear into two piles builds the discrimination faster than teaching either one alone.",
      "There is a nice hook available here: a striking number of 'sn' words involve the nose. Snout, sniff, sneeze, snore, snot. Children find this genuinely funny, and the association makes the blend memorable in a way that drilling does not.",
    ],
    commonErrors: [
      "Confusing 'sn' with 'sm'",
      "Dropping the s and reading 'snap' as 'nap'",
      "Inserting a vowel, saying 'suh-nap'",
    ],
    relatedSlugs: ["sm-blend", "st-blend", "sk-blend"],
  },
  {
    slug: "sw-blend",
    pattern: "sw",
    displayName: "SW Blend",
    category: "blend",
    gradeLevel: "Kindergarten–Grade 1",
    words: [
      "swim", "swam", "swing", "sweet", "sweep", "sweat", "swift",
      "switch", "swan", "sword", "swirl", "sweater",
    ],
    sampleSentences: [
      "The swan can swim and swing.",
      "Sweep the sweet swirl.",
      "I swam swift in a sweater.",
      "Flip the switch.",
    ],
    teachingNotes: [
      "'Sw' only appears at the start of words. The one thing to flag is 'sword,' where the w is silent - it is pronounced 'sord.' That is a genuine exception rather than a pattern, so name it as one odd word instead of letting a child conclude the blend is unreliable.",
      "'Swim,' 'swing,' and 'sweet' are high-frequency and physically actable. For a child who loses focus during word lists, having them do the action while reading the word keeps attention on the page longer than a seated drill does.",
    ],
    commonErrors: [
      "Trying to pronounce the w in 'sword'",
      "Dropping the w and reading 'swim' as 'sim'",
      "Confusing 'sw' with 'st' at a glance",
    ],
    relatedSlugs: ["st-blend", "sp-blend", "tw-blend"],
  },
  {
    slug: "sc-blend",
    pattern: "sc",
    displayName: "SC Blend",
    category: "blend",
    gradeLevel: "Grade 1",
    words: [
      "scat", "scan", "scab", "scar", "scarf", "scale", "scoop",
      "scoot", "score", "scout", "scare", "scream", "screen", "scratch",
    ],
    sampleSentences: [
      "The scout has a scar and a scarf.",
      "Scan the score, then scoop.",
      "Do not scream at the screen.",
      "A scab can scare you.",
    ],
    teachingNotes: [
      "'Sc' makes the same sound as 'sk' when followed by a, o, or u. Before e, i, or y the c goes soft and the pair makes an /s/ sound instead, as in 'science' and 'scene' - but those words are rare enough at this level that the practical rule is simply 'sc sounds like sk.'",
      "'Sc' also opens the three-letter blends 'scr' in 'scream,' 'screen,' and 'scratch.' Those are a genuine step up in difficulty, so introduce them only once two-letter 'sc' is automatic, and treat 'scr' as 's' plus the already-known 'cr' rather than as a brand-new unit.",
    ],
    commonErrors: [
      "Not connecting 'sc' to the identical sound in 'sk'",
      "Struggling with the three-letter jump to 'scr'",
      "Dropping the s and reading 'scat' as 'cat'",
    ],
    relatedSlugs: ["sk-blend", "st-blend", "cr-blend"],
  },
  {
    slug: "tw-blend",
    pattern: "tw",
    displayName: "TW Blend",
    category: "blend",
    gradeLevel: "Kindergarten–Grade 1",
    words: [
      "two", "twin", "twig", "twist", "twelve", "twenty",
      "tweet", "twirl", "twice", "twinkle", "tweeze",
    ],
    sampleSentences: [
      "The twin found a twig.",
      "Twist twice and twirl.",
      "I see twelve stars twinkle.",
      "Birds tweet at twenty past.",
    ],
    teachingNotes: [
      "'Tw' is a small set, and almost every word in it relates to the number two - twin, twice, twelve, twenty, twist. Pointing that out gives a child a reason the words look alike, which is more memorable than treating them as an arbitrary list.",
      "The catch is 'two' itself, where the w is silent. It is one of the most common words in English and a child will meet it constantly, so teach it as a sight word early and treat the rest of the blend as the regular pattern.",
    ],
    commonErrors: [
      "Trying to pronounce the w in 'two'",
      "Dropping the w and reading 'twin' as 'tin'",
      "Confusing 'tw' with 'th' at a glance",
    ],
    relatedSlugs: ["sw-blend", "st-blend", "tr-blend"],
  },
  // ===END-BATCH-6===

  // ===BATCH-7: r-controlled vowels===
  {
    slug: "ar-r-controlled",
    pattern: "ar",
    displayName: "AR (Bossy R)",
    category: "r-controlled",
    gradeLevel: "Grade 1",
    words: [
      "car", "far", "jar", "bar", "star", "park", "dark",
      "bark", "shark", "sharp", "farm", "arm", "hard", "card", "yard",
    ],
    sampleSentences: [
      "The car is far from the farm.",
      "A shark swims in the dark.",
      "Park the cart in the yard.",
      "That card is hard and sharp.",
    ],
    teachingNotes: [
      "'Ar' is the most distinctive of the r-controlled vowels and the easiest place to start. The sound is unmistakable - it is the 'arrr' of a pirate - and unlike 'er,' 'ir,' and 'ur,' it does not share its sound with any other spelling. That makes it a clean first lesson before the harder three.",
      "The core idea to teach is that the r takes over. A child who has learned that a says /a/ in 'cat' has to accept that in 'car' the a no longer says that at all, and the r is why. Calling it 'bossy R' is a cliché precisely because it works - it gives a five-year-old a reason the rule they just learned has stopped applying.",
    ],
    commonErrors: [
      "Trying to use the short a sound, reading 'car' as /kaa-r/",
      "Separating the vowel and r into two sounds",
      "Confusing 'ar' with 'or' when spelling",
    ],
    relatedSlugs: ["or-r-controlled", "er-r-controlled", "ir-r-controlled"],
  },
  {
    slug: "or-r-controlled",
    pattern: "or",
    displayName: "OR (Bossy R)",
    category: "r-controlled",
    gradeLevel: "Grade 1",
    words: [
      "for", "or", "corn", "born", "torn", "horn", "storm",
      "short", "sport", "north", "fork", "pork", "sort", "port", "story",
    ],
    sampleSentences: [
      "The horn is short and torn.",
      "Corn grows north of the port.",
      "Sort the fork for the storm.",
      "Tell a short sport story.",
    ],
    teachingNotes: [
      "'Or' is the second clean r-controlled sound and, like 'ar,' it is mostly unambiguous. Teaching 'ar' and 'or' together as the two distinct ones, before the three that sound alike, gives a child two solid wins and a clear sense that this family is learnable.",
      "One wrinkle: after a w, 'or' often shifts to sound like 'er' - 'work,' 'word,' 'world,' 'worm.' Those are common words, so flag them as a small group where the w changes things, rather than leaving a child to wonder why 'word' does not rhyme with 'ford.'",
    ],
    commonErrors: [
      "Reading 'work' and 'word' with the 'or' sound",
      "Confusing 'or' with 'ar'",
      "Separating the o and r into two sounds",
    ],
    relatedSlugs: ["ar-r-controlled", "er-r-controlled", "ur-r-controlled"],
  },
  {
    slug: "er-r-controlled",
    pattern: "er",
    displayName: "ER (Bossy R)",
    category: "r-controlled",
    gradeLevel: "Grade 1–2",
    words: [
      "her", "herd", "germ", "term", "fern", "verb", "clerk",
      "person", "winter", "summer", "sister", "brother", "water", "under", "letter",
    ],
    sampleSentences: [
      "Her sister sat under the fern.",
      "Winter water is colder.",
      "The person sent a letter.",
      "My brother knows the term.",
    ],
    teachingNotes: [
      "'Er,' 'ir,' and 'ur' all make the same sound, which is the single most important thing to tell a child about them. Presented as three separate lessons they feel like three arbitrary rules; presented as triplets that sound identical but are spelled differently, they become one fact with three cases.",
      "'Er' is by far the most common of the three, especially at the end of words, where it does grammatical work - it turns a verb into a doer ('teach' to 'teacher') and makes comparisons ('cold' to 'colder'). Pointing that out gives a child a way to predict the spelling rather than guess, which is where most of the difficulty in this family actually sits.",
    ],
    commonErrors: [
      "Guessing between 'er', 'ir', and 'ur' when spelling",
      "Missing unstressed 'er' at the end of longer words",
      "Trying to sound out e and r separately",
    ],
    relatedSlugs: ["ir-r-controlled", "ur-r-controlled", "ar-r-controlled"],
  },
  {
    slug: "ir-r-controlled",
    pattern: "ir",
    displayName: "IR (Bossy R)",
    category: "r-controlled",
    gradeLevel: "Grade 1–2",
    words: [
      "bird", "girl", "first", "third", "shirt", "skirt", "dirt",
      "stir", "sir", "firm", "birth", "thirty", "circle", "circus",
    ],
    sampleSentences: [
      "The first girl wore a shirt.",
      "A bird sat in the dirt.",
      "Stir the third circle.",
      "Thirty went to the circus.",
    ],
    teachingNotes: [
      "'Ir' sounds exactly like 'er' and 'ur,' so it cannot be told apart by ear. What makes it learnable is that the 'ir' group is relatively small and full of very common words - bird, girl, first, third, shirt. Learning those specific words as a set is more efficient than trying to derive which spelling a word uses.",
      "A pattern worth noticing: the ordinal numbers 'third' and 'thirty' both use 'ir,' as does 'first.' Number words come up constantly, so anchoring the spelling to counting gives a child a reliable place to check their memory from.",
    ],
    commonErrors: [
      "Substituting 'er' or 'ur' when spelling 'ir' words",
      "Reading 'ir' with a short i sound",
      "Confusing 'girl' and 'grill' by transposing letters",
    ],
    relatedSlugs: ["er-r-controlled", "ur-r-controlled", "or-r-controlled"],
  },
  {
    slug: "ur-r-controlled",
    pattern: "ur",
    displayName: "UR (Bossy R)",
    category: "r-controlled",
    gradeLevel: "Grade 1–2",
    words: [
      "turn", "burn", "hurt", "curl", "curb", "surf", "fur",
      "burst", "church", "purple", "purse", "nurse", "turtle", "Thursday",
    ],
    sampleSentences: [
      "The turtle will turn and burn.",
      "My purple purse is hurt.",
      "The nurse can surf on Thursday.",
      "Curl the fur by the curb.",
    ],
    teachingNotes: [
      "'Ur' completes the triplet. All three spellings make one sound, and once a child accepts that, the reading side of this family is essentially solved - any of the three can be read the same way, so decoding never fails. The remaining difficulty is entirely in spelling.",
      "For spelling, the practical approach is word families rather than rules. Group 'turn, burn, churn' and 'hurt, burst, curb' and practice them as sets, because no reliable rule distinguishes 'ur' from 'er' and 'ir.' Telling a child that plainly is kinder than implying there is a rule they have failed to learn.",
    ],
    commonErrors: [
      "Substituting 'er' or 'ir' when spelling",
      "Reading 'ur' with a short u sound",
      "Missing that all three spellings sound identical",
    ],
    relatedSlugs: ["er-r-controlled", "ir-r-controlled", "ar-r-controlled"],
  },
  // ===END-BATCH-7===
];

export function getPatternBySlug(slug: string): PhonicsPattern | undefined {
  return phonicsPatterns.find((p) => p.slug === slug);
}

export function getPatternsByCategory(
  category: PatternCategory
): PhonicsPattern[] {
  return phonicsPatterns.filter((p) => p.category === category);
}

export const patternCategories: PatternCategory[] = [
  "word-family",
  "digraph",
  "blend",
  "vowel-team",
  "r-controlled",
];
