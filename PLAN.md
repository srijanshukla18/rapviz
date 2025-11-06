Good. You’re already ahead of 90% of “lyric visualizers” because you’re even asking this.

Right now you’re using Datamuse (rel_rhy) to decide if two words rhyme. That’s basically “does word A appear in a list of rhymes for word B from this external API?” It’s cheap and fast, but it’s surface-level and super Anglo. It will fall apart with slang, code-switching, Hindi/Punjabi/Urdu words, and multisyllable rapper schemes.

Let’s walk through stronger replacements, from practical → insane, and I’ll tell you exactly what to build.

–––

1. Why Datamuse is mid

Problems with the current approach:

* It’s word-level only. No awareness of multi-syllable internal rhyme like “Mary Mack / scary act”.
* It’s binary. Either “rhymes” or “doesn’t rhyme”. No score for “almost rhymes / slant rhymes”.
* It’s English-biased. Desi hip hop = half Hinglish, half Hindi words in Latin script, sometimes straight Devanagari. Datamuse doesn’t know what to do with “bakchod” or “dhadkan”.
* You’re trusting an external service you don’t control.

So you want to replace “API says yes/no” with “we compute pronunciation, compare endings, assign colors.” That’s the core upgrade.

Everything below is you owning rhyme detection locally instead of asking someone else.

–––
2. Option 1: Local phonetics with CMUdict (+ G2P for OOV)
This is the most realistic immediate upgrade for English bars.

What it is:

* The CMU Pronouncing Dictionary is an open-source lexicon of English words → phoneme sequences in ARPABET. Example: "LOVE" → "L AH1 V". It’s been used forever in speech and NLP. ([speech.cs.cmu.edu][1])
* The `pronouncing` Python lib wraps CMUdict and can already do “give me all pronunciations for word X”, “how many syllables”, “what rhymes with word Y.” ([pronouncing.readthedocs.io][2])
* For out-of-vocabulary (slang like “shyt”, “opp”, “shawtyyyy”), you fall back to a grapheme-to-phoneme (G2P) model. G2P = convert raw text → phonemes with ML instead of a fixed dictionary. These models exist in Python and are standard in TTS/ASR. ([NVIDIA Docs][3])

How rhyme scoring works with this setup:

1. For each word:

   * Get phoneme list (from CMUdict if available, else from G2P model).
   * Example: “SCAR” → [S, K, AA1, R], “CAR” → [K, AA1, R].
2. Extract the “rhyme tail.”

   * Heuristic: take from the last stressed vowel (the vowel with a stress digit like AH1) to the end.
   * “SCAR” tail: [AA1, R]
   * “CAR” tail: [AA1, R]
   * If tails match or are very close (Levenshtein distance small), they rhyme.
3. Build rhyme classes:

   * First time you see a new tail, assign a new color ID.
   * Every later word whose tail matches that tail joins that color.

This is already miles better than Datamuse:

* You’re comparing pronunciation, not spelling.
* You can catch multisyllable rhymes by using last 2–3 syllables instead of only final syllable.
* You can support internal rhyme inside the bar, not just end rhyme.

How you’d plug this into your Flask service:

* Pre-step: load CMUdict into memory (via `pronouncing`).
* Also load a fallback G2P model so we can generate phonemes for slang.
* For each `/song` request, instead of `api.words(rel_rhy=word)` you:

  * Generate word → phoneme tail.
  * Cluster words by matching tails.

This would immediately give you correct highlighting for “Mary Mack / scary act / scary black”, etc. which is what your screenshot is doing.

Weakness:

* Purely English. CMUdict is English-only. ([speech.cs.cmu.edu][1])
* Still doesn’t know “bakchodi,” “tera flow chhaku jaisa,” etc.

So: Option 1 fixes American/UK rap quality and makes you independent of Datamuse. But it won’t solve Desi rap yet.

–––
3. Option 2: Multilingual phoneme pipeline (English + Hindi + Hinglish)
This is where you become unique. You basically do Option 1, but multilingual.

Goal:
Turn every word, regardless of script, into a pronunciation sequence (IPA or similar), then compare the tail sounds to decide rhyme groups.

Pieces you’d use:

A. Phonemizer / eSpeak-ng stack

* `phonemizer` is a Python lib that converts text to phonemes (IPA-ish symbols) for many languages by calling backends like eSpeak-ng. ([GitHub][4])
* eSpeak-ng is a lightweight TTS core that can output phonemes, not just audio, and it supports a bunch of languages including Hindi. ([espeak.sourceforge.net][5])
* This means for a Hindi word in Devanagari, like "तूफ़ान", you ask phonemizer(eSpeak-ng backend) and you get an approximate phoneme string. (There are known issues / gaps for some Hindi tokens, but the stack is intended to do Hindi phonemization, not just English.) ([GitHub][6])

B. G2P models / transformer G2P

* There are multilingual transformer-based G2P models that map spelling → phoneme sequences across many languages, not just English. These things were benchmarked on ~15 languages and got strong accuracy. ([ACL Anthology][7])
* G2P in general is a solved subproblem in TTS pipelines. You can run it locally (PyTorch). ([NVIDIA Docs][3])

C. Romanized Hindi / Hinglish

* Desi hip hop is mostly romanized Hindi + English mashed together. Example: “tera flow jyada heavy hai bhai”.
* eSpeak-ng will choke on “tera” if it assumes English rules. You fix this by:

  1. Detecting language/script heuristically per word.

     * If the token is pure ASCII but “looks Hindi” (heuristic: lots of ‘aa’, ‘yaar’, ‘bhai’, ‘kh’, ‘chh’, ‘gaadi’, etc.), you pass it through a Hinglish→Devanagari transliterator (there are tons of Hinglish transliteration datasets; worst case you hack a ruleset).
  2. Once you have Devanagari, run phonemizer in Hindi mode to get IPA/phonemes. ([GitHub][4])
  3. Now English words and Hindi words both live in a single phoneme space (IPA-ish). Now you can compare rhyme tails across languages.

How rhyme scoring works in this multilingual setup:

1. Normalize every token to a phoneme sequence in a shared alphabet (IPA or pseudo-IPA).
2. Chop off from the last stressed vowel or last vowel cluster to the end. (Hindi doesn’t mark stress the same way English does, so fallback rule is “last vowel sound + following consonants”.)
3. Compute distance between tails. If similar enough, they’re in the same rhyme class.

Why this is powerful:

* “flow” / “dhokha” probably won’t rhyme, but “kala” / “galla” type endings might light up in the same color even if one is Hindi and one is gutter Hinglish spelling.
* You become the first visualizer I’ve seen that can color rhyme groups across mixed-language bars, which is exactly how Indian and Pakistani rappers write.

Caveats:

* Hindi support in eSpeak-ng is decent-but-not-perfect. People report gaps for some Hindi tokens, especially with nukta/aspirated consonants. ([GitHub][6])
* Hinglish transliteration is non-trivial and you’ll have to hack rules (“kh” → ख / ख़, “aa” → आ, etc.). This is work, but it’s deterministic work.
* You’ll still miss Marathi/Punjabi/Urdu slang unless you build more translit rules.

But this gives you a scalable path: word in → phone sequence out → rhyme class.

This is the first “serious” answer if you truly care about Desi hip hop.

–––
4. Option 3: True rapper-grade rhyme detection (multisyllable chains, internals)
Now we’re past just “end-of-word rhymes.”

Rappers don’t just rhyme last syllables. They rhyme 2–4 syllable chunks in the middle of the line:
“My momma told me / pass her her glass of Ol’ E / not to be troublesome”
That’s not just the last word. It’s repeating vowel-consonant shapes across spans.

How to do this algorithmically:

1. After you phonemize each word, also split the phoneme sequence into syllables (you can infer syllable boundaries from vowel/consonant structure; most phonemizers or TTS G2P models can give you this or you can heuristically chunk between vowels). ([bootphon.github.io][8])
2. Slide a 2–3 syllable window across the line, like n-grams but on phonemes, not letters.

   * Example: “my MOM-ma TOLD me” → take “OM-ma-TOLD” as a sound chunk.
3. Hash those chunks (normalize stress marks, collapse length markers so “AA1” and “AA0” are both just “AA”).
4. If the same or near-same chunk appears again later in the bar or next bar, flag it as an internal rhyme group and give it a color.

Now you’re doing what battle rap breakdown channels do: you’re showing multisyllabic schemes, not just “cat / hat”.

UI change:

* Instead of coloring whole words only, you color substrings within words (like your screenshot: sometimes only part of a word is highlighted because only that phonetic tail corresponds to the rhyme scheme).
* You’ll need to surface span indices: “word #12, phoneme positions [2:4] map to color X”.
* Frontend then splits tokens into spans for highlighting.

This is the “holy shit” mode. This is how you impress rap nerds.

–––
5. Option 4: LLM assist (safety net for slang, nicknames, stretched vowels)
Now let’s talk LLMs.

LLMs can help in two places:

A. Normalizing slang → pronunciation guess
Prompt the LLM with:
“You are a pronunciation generator. Convert each token to an approximate phonetic spelling in IPA-ish or ARPABET. Keep it short, 1 per word.”
Feed it all OOV words from a verse at once so it can use context (“shawtyyyy” vs “shaawdi” vs “shawdi”).
Then you merge that guess into the same pipeline as above.
Benefit: handles “ghanta”, “bakchodi”, “opp”, “skrrt”, “rrrrrah” better than rule-based translit alone.

B. Direct rhyme class labeling
You can literally ask an LLM:
“Here’s a verse split into words in order. Assign a label (A, B, C, …) to each word such that words with the same ending sound share the same label. Treat near rhymes / slant rhymes as same label. Return JSON: [{word:'rest', label:'A'}, ...]. Ignore stopwords like 'the', 'a', 'and'.”
It will group rhyme classes for you.

Pros:

* Handles multilingual, slang, repeated hooks, inside-bar schemes.
* Zero setup. You don’t build phoneme logic at all.

Cons:

* It’s probabilistic. Two passes may not 100% agree unless you force deterministic decoding.
* Latency and cost scale with verse length.
* You’ll still want stable color assignment between calls (label “A” today should still be cyan tomorrow). You’ll need a caching layer keyed by (artist, song, line_index).

Where LLMs actually shine:
Use them as a fallback, not as the main pipeline.

* Do deterministic phoneme-based clustering first (Option 2/3).
* For any leftover token that didn’t land in a rhyme class but looks like it should (visually obvious to humans), ask LLM to merge it.
* This gives you the look of human annotation with machine repeatability.

–––
6. What I’d build (roadmap, no fluff)

Phase 1 (replace Datamuse, ship fast):

1. Add `pronouncing` + CMUdict in your Flask server. ([pronouncing.readthedocs.io][2])
2. Add an English G2P fallback model for OOV words. ([NVIDIA Docs][3])
3. For each word:

   * Get phonemes.
   * Extract rhyme tail (last stressed vowel → end).
   * Hash that tail to a class ID.
4. Color by class ID.
5. Drop the greedy “cluster.append(word)” logic. Instead, rhyme class is literally “same tail hash.” Way more stable.

This alone makes you look way smarter than Datamuse.

Phase 2 (Desi mode, your differentiator):

1. Add phonemizer with eSpeak-ng backend.

   * For any token that isn’t clean English:

     * Detect script.
     * If Devanagari → phonemize directly as Hindi → IPA. ([GitHub][4])
     * If Hinglish romanization → transliterate heuristically → then phonemize.
2. Convert both English ARPABET (from Phase 1) and Hindi IPA (from phonemizer) into one shared comparison space. Easiest hack: map both down to a coarse vowel+consonant skeleton like “AA R” / “AA R” so you can compare tails even if alphabet differs.
3. Do the same rhyme-tail hashing.
4. Now you get rhyme colors across bilingual bars.

This is your “headline feature.” No one else has this.

Phase 3 (real rap nerd mode):

1. Implement syllable n-gram sliding windows over phoneme sequences.
2. Highlight repeated multisyllable chunks inside the bar, not just end words.
3. Keep colors consistent across lines and verses.

Phase 4 (LLM assist):

1. Cache every line’s final annotation (word → color ID).
2. When you hit garbage (slang scream, ad-lib, weird stretch vowels), ask the LLM to classify only those leftovers into an existing color class rather than inventing new ones.
3. Store that in DB so the same song is deterministic next time.

–––
Bottom line

Datamuse is fine for a toy, but it’s blind to pronunciation reality, code-switch, and internal multisyllable schemes.

The serious path is:

* Local phoneme generation (CMUdict + G2P) for English. ([speech.cs.cmu.edu][1])
* Multilingual phonemizer / eSpeak-ng / transformer G2P to turn Hindi / Hinglish / Urdu-ish tokens into IPA-like phones so you can rhyme across desi bars. ([GitHub][4])
* Syllable-chunk n-gram matching for internal/multisyllable rhyme highlighting, which is how rap nerds actually analyze flow. ([bootphon.github.io][8])
* LLM as a cleanup layer for slang and noisy romanized tokens, not the main engine.

Do this and your highlight output can actually look like the screenshot: consistent color bands across whole phrases, not just guessing word pairs. You’ll be in a different league.

[1]: https://www.speech.cs.cmu.edu/cgi-bin/cmudict?utm_source=chatgpt.com "The CMU Pronouncing Dictionary"
[2]: https://pronouncing.readthedocs.io/en/latest/?utm_source=chatgpt.com "Documentation for pronouncing — pronouncing 0.2.0 ..."
[3]: https://docs.nvidia.com/nemo-framework/user-guide/latest/nemotoolkit/tts/g2p.html?utm_source=chatgpt.com "Grapheme-to-Phoneme Models"
[4]: https://github.com/bootphon/phonemizer?utm_source=chatgpt.com "bootphon/phonemizer: Simple text to phones converter for ..."
[5]: https://espeak.sourceforge.net/languages.html?utm_source=chatgpt.com "3. languages - eSpeak"
[6]: https://github.com/bootphon/phonemizer/issues/63?utm_source=chatgpt.com "Does not produce phonemes for few hindi words · Issue #63"
[7]: https://aclanthology.org/2020.sigmorphon-1.16.pdf?utm_source=chatgpt.com "Multilingual Grapheme-to-Phoneme Conversion With a ..."
[8]: https://bootphon.github.io/phonemizer/?utm_source=chatgpt.com "Welcome to Phonemizer's documentation! - GitHub Pages"

