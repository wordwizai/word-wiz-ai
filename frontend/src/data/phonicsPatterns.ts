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
      "mast", "contrast",
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

  // ===END-BATCH-2===
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
