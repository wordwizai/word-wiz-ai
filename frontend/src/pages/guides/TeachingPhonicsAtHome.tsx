import React from "react";
import ArticlePageTemplate, { ArticleSection } from "@/components/ArticlePageTemplate";

const TeachingPhonicsAtHome = () => {
  const content: ArticleSection[] = [
    {
      type: "paragraph",
      content: "Watching your child struggle with reading is heartbreaking. The good news? Phonics instruction is systematic and teachable—even by parents with no teaching experience. This guide provides everything you need to help your child become a confident reader."
    },
    {
      type: "heading",
      level: 2,
      content: "Understanding Phonics Basics",
      id: "phonics-basics"
    },
    {
      type: "heading",
      level: 3,
      content: "What Are Phonemes?"
    },
    {
      type: "paragraph",
      content: "Phonemes are the smallest units of sound in language. English has 44 phonemes despite having only 26 letters. For example:"
    },
    {
      type: "list",
      content: [
        "'Cat' = 3 phonemes: /k/ /æ/ /t/",
        "'Ship' = 3 phonemes: /ʃ/ /ɪ/ /p/ (even though it has 4 letters)",
        "'Cheese' = 3 phonemes: /ch/ /ee/ /z/"
      ]
    },
    {
      type: "heading",
      level: 3,
      content: "Phonics vs. Sight Words"
    },
    {
      type: "paragraph",
      content: "Phonics means decoding words using letter-sound relationships. Sight words are memorized words (like 'the,' 'was,' 'said'). Research shows phonics should come first—teach the system before the exceptions."
    },
    {
      type: "callout",
      content: {
        type: "tip",
        title: "The 80/20 Rule",
        content: "Focus 80% on systematic phonics, 20% on sight words. This ratio produces the best reading outcomes according to Science of Reading research."
      }
    },
    {
      type: "heading",
      level: 3,
      content: "The Phonics Progression"
    },
    {
      type: "paragraph",
      content: "Follow this sequence (don't skip steps!):"
    },
    {
      type: "list",
      content: [
        "1. Individual letter sounds (s, a, t, p, i, n)",
        "2. CVC words (consonant-vowel-consonant: cat, sit, mop)",
        "3. Consonant digraphs (ch, sh, th, wh, ck)",
        "4. Consonant blends (bl, cr, st, nd)",
        "5. Long vowels and vowel teams (ai, ee, oa, igh)",
        "6. R-controlled vowels (ar, er, ir, or, ur)",
        "7. Advanced patterns (tion, ough, etc.)"
      ]
    },
    {
      type: "heading",
      level: 2,
      content: "Essential Materials You'll Need",
      id: "materials"
    },
    {
      type: "paragraph",
      content: "You don't need expensive curriculum. Here's what actually works:"
    },
    {
      type: "heading",
      level: 3,
      content: "Free Resources"
    },
    {
      type: "list",
      content: [
        "Decodable books (Reading Horizons, Spelfabet, Flyleaf Publishing offer free samples)",
        "Printable letter cards",
        "Word lists by phonics pattern",
        "Word Wiz AI for pronunciation feedback (free speech recognition)"
      ]
    },
    {
      type: "heading",
      level: 3,
      content: "Low-Cost Materials ($20-50)"
    },
    {
      type: "list",
      content: [
        "Magnetic letters or letter tiles",
        "Whiteboard and markers",
        "Index cards for flashcards",
        "Decodable reader set (optional but helpful)"
      ]
    },
    {
      type: "paragraph",
      content: "You don't need fancy workbooks or expensive programs. The materials above plus consistency will get results."
    },
    {
      type: "heading",
      level: 2,
      content: "10 Phonics Activities for Home",
      id: "activities"
    },
    {
      type: "heading",
      level: 3,
      content: "Activity 1: Sound Sorting"
    },
    {
      type: "paragraph",
      content: "Gather objects or pictures. Sort by beginning sound (all /b/ sounds together). Takes 5-10 minutes, perfect for ages 4-6."
    },
    {
      type: "heading",
      level: 3,
      content: "Activity 2: Blending Practice"
    },
    {
      type: "paragraph",
      content: "Parent says sounds: '/c/ /a/ /t/' → Child blends: 'cat!' Start with 3-sound words, progress to 4-5 sounds. Use Word Wiz AI to check if pronunciation is correct."
    },
    {
      type: "heading",
      level: 3,
      content: "Activity 3: Segmenting Words"
    },
    {
      type: "paragraph",
      content: "Reverse of blending. Parent says 'dog' → Child segments: '/d/ /o/ /g/'. Use counters or blocks for each sound. Builds phonemic awareness."
    },
    {
      type: "heading",
      level: 3,
      content: "Activity 4: Build-A-Word"
    },
    {
      type: "paragraph",
      content: "Use letter tiles or magnetic letters. Parent says a word, child builds it with letters. Check letter order and spelling. Read the word aloud when done."
    },
    {
      type: "heading",
      level: 3,
      content: "Activity 5: Word Families Practice"
    },
    {
      type: "paragraph",
      content: "Focus on one pattern (-at family: cat, bat, sat, rat). Make a list together. Read aloud and practice. Word Wiz AI can verify pronunciation of each word."
    },
    {
      type: "heading",
      level: 3,
      content: "Activity 6: Sound Hunt"
    },
    {
      type: "paragraph",
      content: "Pick a target sound (/sh/ for example). Find objects in the house with that sound. Write a list of words together. Read the list aloud."
    },
    {
      type: "heading",
      level: 3,
      content: "Activity 7: Dictation Practice"
    },
    {
      type: "paragraph",
      content: "Start simple (CVC words: cat, dog, pin). Parent says word, child writes it. Sound it out together if stuck. Check spelling together."
    },
    {
      type: "heading",
      level: 3,
      content: "Activity 8: Decodable Book Reading"
    },
    {
      type: "paragraph",
      content: "Choose a book matching current skill level. Child reads aloud. Parent provides encouragement. Use Word Wiz AI for pronunciation practice of tricky words."
    },
    {
      type: "heading",
      level: 3,
      content: "Activity 9: Phonics Games"
    },
    {
      type: "paragraph",
      content: "Make it fun: phonics bingo, memory matching with words, 'I Spy' with beginning sounds. Games reduce pressure and increase engagement."
    },
    {
      type: "heading",
      level: 3,
      content: "Activity 10: Make Your Own Phonics Book"
    },
    {
      type: "paragraph",
      content: "Choose a word family or pattern. Child draws pictures and labels them together. Re-read the homemade book. Kids love reading books they created!"
    },
    {
      type: "heading",
      level: 2,
      content: "Common Mistakes to Avoid",
      id: "mistakes"
    },
    {
      type: "heading",
      level: 3,
      content: "Mistake 1: Going Too Fast"
    },
    {
      type: "paragraph",
      content: "Don't rush to complex patterns before mastering basics. Ensure 90%+ accuracy before progressing. Stay on CVC words for weeks if needed—mastery matters more than speed."
    },
    {
      type: "heading",
      level: 3,
      content: "Mistake 2: Skipping Blending Practice"
    },
    {
      type: "paragraph",
      content: "Kids can know individual sounds but struggle to blend them. Daily blending practice (5 minutes minimum) is essential. Model slow blending, then speed up gradually."
    },
    {
      type: "heading",
      level: 3,
      content: "Mistake 3: Not Checking Pronunciation"
    },
    {
      type: "paragraph",
      content: "Pronunciation errors become habits if not corrected early. Listen carefully and correct gently. Word Wiz AI provides objective pronunciation feedback—catching errors you might miss."
    },
    {
      type: "callout",
      content: {
        type: "warning",
        title: "Why Pronunciation Matters",
        content: "How children pronounce words affects how they spell them later. 'Free' instead of 'three' leads to spelling 'fre.' Catch and correct early."
      }
    },
    {
      type: "heading",
      level: 3,
      content: "Mistake 4: Using Non-Decodable Books Too Early"
    },
    {
      type: "paragraph",
      content: "Leveled readers encourage guessing from pictures. Stick with decodable texts during phonics instruction. Introduce predictable books after solid decoding skills."
    },
    {
      type: "heading",
      level: 3,
      content: "Mistake 5: Making It Stressful"
    },
    {
      type: "paragraph",
      content: "Pressure and frustration harm progress. Keep sessions short (15 minutes maximum). Stay playful and positive. Celebrate small wins consistently."
    },
    {
      type: "heading",
      level: 2,
      content: "Creating a Daily Routine",
      id: "daily-routine"
    },
    {
      type: "paragraph",
      content: "Consistency beats intensity. Here's a realistic 15-minute daily routine:"
    },
    {
      type: "heading",
      level: 3,
      content: "Minutes 0-3: Warm-Up"
    },
    {
      type: "paragraph",
      content: "Review previous sounds/patterns with flashcard drill. Quick and energetic. Build confidence with mastered skills."
    },
    {
      type: "heading",
      level: 3,
      content: "Minutes 3-8: New Learning"
    },
    {
      type: "paragraph",
      content: "Introduce ONE new concept. Model it, practice together. Use manipulatives (letter tiles, etc.). Keep it focused and short."
    },
    {
      type: "heading",
      level: 3,
      content: "Minutes 8-13: Application"
    },
    {
      type: "paragraph",
      content: "Read decodable sentences or short book. Child applies new learning. Use Word Wiz AI for pronunciation feedback on tricky words."
    },
    {
      type: "heading",
      level: 3,
      content: "Minutes 13-15: Game/Fun Activity"
    },
    {
      type: "paragraph",
      content: "One of the activities above. End on a positive note. Keep child wanting more for tomorrow."
    },
    {
      type: "heading",
      level: 3,
      content: "Weekly Schedule Template"
    },
    {
      type: "list",
      content: [
        "Monday: Introduce new sound/pattern",
        "Tuesday: Practice blending with new pattern",
        "Wednesday: Decodable reading practice",
        "Thursday: Dictation/writing with pattern",
        "Friday: Review week's learning + game"
      ]
    },
    {
      type: "callout",
      content: {
        type: "success",
        title: "The Key to Success",
        content: "15 minutes daily beats 2 hours on the weekend. Consistency is everything in phonics instruction."
      }
    },
    {
      type: "heading",
      level: 2,
      content: "When to Move Forward",
      id: "mastery-checklist"
    },
    {
      type: "paragraph",
      content: "Before moving to the next level, your child should:"
    },
    {
      type: "list",
      content: [
        "✅ Recognize all letters and sounds instantly (no hesitation)",
        "✅ Blend CVC words accurately 90%+ of the time",
        "✅ Segment words into individual sounds",
        "✅ Read decodable sentences with current patterns fluently",
        "✅ Spell simple words with current patterns accurately"
      ]
    },
    {
      type: "paragraph",
      content: "Red flags (stay at current level):"
    },
    {
      type: "list",
      content: [
        "❌ Guessing at words instead of decoding",
        "❌ Frequent pronunciation errors",
        "❌ Frustration or resistance",
        "❌ Can't blend without support",
        "❌ Forgets sounds from previous lessons"
      ]
    },
    {
      type: "heading",
      level: 2,
      content: "Troubleshooting Common Challenges",
      id: "troubleshooting"
    },
    {
      type: "heading",
      level: 3,
      content: "Challenge: Child Confuses Similar Sounds (b/d, p/b)"
    },
    {
      type: "paragraph",
      content: "Solution: Multi-sensory teaching (trace letters, use hand actions). Word Wiz AI can identify which specific sounds are confused through its phoneme analysis."
    },
    {
      type: "heading",
      level: 3,
      content: "Challenge: Can't Blend Sounds Together"
    },
    {
      type: "paragraph",
      content: "Solution: Start with 2 sounds (at, it), then 3 (cat, sit). Use arm sliding motion while blending. More blending practice, less memorizing."
    },
    {
      type: "heading",
      level: 3,
      content: "Challenge: Mispronounces Words Consistently"
    },
    {
      type: "paragraph",
      content: "Solution: Model correct pronunciation without criticism. Word Wiz AI provides specific feedback on pronunciation errors at the phoneme level. Practice in mirror, exaggerate mouth movements."
    },
    {
      type: "heading",
      level: 3,
      content: "Challenge: Loses Interest/Motivation"
    },
    {
      type: "paragraph",
      content: "Solution: Shorten sessions, add more games. Use sticker chart or small rewards. Rotate between activities for variety."
    },
    {
      type: "heading",
      level: 2,
      content: "How Technology Can Help",
      id: "technology"
    },
    {
      type: "paragraph",
      content: "Speech recognition technology has transformed home phonics instruction:"
    },
    {
      type: "heading",
      level: 3,
      content: "The Pronunciation Problem"
    },
    {
      type: "paragraph",
      content: "Parents try to catch pronunciation errors, but it's hard to hear subtle differences consistently. We also get tired of correcting or worry about discouraging our children."
    },
    {
      type: "heading",
      level: 3,
      content: "The Word Wiz AI Solution"
    },
    {
      type: "list",
      content: [
        "Listens to your child read aloud",
        "Identifies specific pronunciation errors at phoneme level",
        "Provides immediate, encouraging feedback",
        "Never gets tired or frustrated",
        "Tracks improvement over time",
        "Completely free (no subscription needed)"
      ]
    },
    {
      type: "paragraph",
      content: "This means consistent, objective feedback on every practice session—something impossible for busy parents to provide alone."
    },
    {
      type: "heading",
      level: 2,
      content: "Resources & Next Steps",
      id: "resources"
    },
    {
      type: "heading",
      level: 3,
      content: "Free Decodable Book Sources"
    },
    {
      type: "list",
      content: [
        "Spelfabet: Free decodable passages",
        "Reading Horizons: Sample decodable books",
        "Flyleaf Publishing: Free sample books",
        "Your local library (ask for decodable readers)"
      ]
    },
    {
      type: "heading",
      level: 3,
      content: "Recommended Tools"
    },
    {
      type: "list",
      content: [
        "Word Wiz AI (free pronunciation feedback and practice)",
        "Teach Your Monster to Read (free phonics game)",
        "Khan Academy Kids (free early learning)"
      ]
    },
    {
      type: "heading",
      level: 3,
      content: "When to Seek Professional Help"
    },
    {
      type: "list",
      content: [
        "Child is 7+ and struggling with basic phonics",
        "Suspected dyslexia (family history, unusual difficulties)",
        "No progress after 6 months of consistent practice",
        "Extreme frustration or behavioral issues around reading"
      ]
    },
    {
      type: "heading",
      level: 2,
      content: "Conclusion",
      id: "conclusion"
    },
    {
      type: "paragraph",
      content: "Teaching phonics at home is completely doable for parents. The keys to success:"
    },
    {
      type: "list",
      content: [
        "Follow the systematic progression (don't skip steps)",
        "15 minutes daily is better than long sporadic sessions",
        "Use free resources (decodable books, Word Wiz AI)",
        "Be patient and celebrate small wins",
        "Check pronunciation with tools like Word Wiz AI",
        "Stay consistent and positive"
      ]
    },
    {
      type: "paragraph",
      content: "You don't need a teaching degree—just consistency, patience, and the right resources. Start with 15 minutes today, and watch your child's reading confidence grow."
    }
  ];

  const relatedArticles = [
    {
      title: "My Child Can Read But Pronounces Words Wrong: Here's What to Do",
      href: "/articles/child-pronounces-words-wrong",
      category: "Reading Help",
      readTime: 10
    },
    {
      title: "The Ultimate Guide to Phoneme Awareness",
      href: "/guides/phoneme-awareness-complete-guide",
      category: "Phonics Guide",
      readTime: 11
    },
    {
      title: "Decodable Books vs Leveled Readers: Which Should Your Child Read?",
      href: "/articles/decodable-books-vs-leveled-readers",
      category: "Reading Strategies",
      readTime: 7
    }
  ];

  const inlineCTAs = [
    {
      afterSection: 15,
      title: "Practice Pronunciation with Word Wiz AI",
      description: "Free speech recognition provides instant feedback on pronunciation—catching errors you might miss",
      buttonText: "Try Free",
      buttonHref: "/signup"
    },
    {
      afterSection: 35,
      title: "Make Phonics Practice Easier",
      description: "Word Wiz AI listens to your child read and provides specific, encouraging feedback automatically",
      buttonText: "Start Practicing",
      buttonHref: "/signup"
    }
  ];

  const breadcrumbs = [
    { label: "Home", href: "/" },
    { label: "Guides", href: "/guides" },
    { label: "Teaching Phonics at Home", href: "/guides/how-to-teach-phonics-at-home" }
  ];

  const structuredData = {
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": "A Parent's Complete Guide to Teaching Phonics at Home",
    "description": "Learn how to teach phonics at home with this step-by-step guide. Includes 10 activities, daily routine, common mistakes to avoid, and free resources.",
    "author": {
      "@type": "Organization",
      "name": "Word Wiz AI"
    },
    "publisher": {
      "@type": "Organization",
      "name": "Word Wiz AI",
      "logo": {
        "@type": "ImageObject",
        "url": "https://wordwizai.com/logo.png"
      }
    },
    "datePublished": "2024-12-29",
    "dateModified": "2024-12-29",
    "articleSection": "Education",
    "keywords": ["teaching phonics", "phonics at home", "how to teach reading", "phonics activities", "parent guide"],
    "wordCount": 2400
  };

  return (
    <ArticlePageTemplate
      metaTitle="How to Teach Phonics at Home: Complete Parent Guide (2024)"
      metaDescription="Step-by-step guide for parents teaching phonics at home. Includes 10 activities, daily routine, common mistakes to avoid, and free resources. No teaching degree needed."
      canonicalUrl="https://wordwizai.com/guides/how-to-teach-phonics-at-home"
      heroImage="https://images.unsplash.com/photo-1503454537195-1dcabb73ffb9?w=1920&h=1080&fit=crop"
      heroImageAlt="Parent teaching child to read with phonics book"
      headline="A Parent's Complete Guide to Teaching Phonics at Home"
      subheadline="Everything you need to help your child become a confident reader—no teaching degree required"
      author={{
        name: "Word Wiz AI Team",
        bio: "Educational technology experts specializing in phonics instruction and early literacy based on the Science of Reading.",
      }}
      publishDate="2024-12-29"
      readTime={12}
      category="Phonics Education"
      content={content}
      relatedArticles={relatedArticles}
      structuredData={structuredData}
      breadcrumbs={breadcrumbs}
      inlineCTAs={inlineCTAs}
    />
  );
};

export default TeachingPhonicsAtHome;
