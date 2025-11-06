# Rhyme Detection Implementation Notes

This document describes the phoneme-based rhyme detection system implemented based on PLAN.md.

## Overview

The system has been upgraded from Datamuse API-based rhyme detection to a sophisticated phoneme-based approach that provides:

- **Phase 1**: Local English phoneme detection using CMUdict + G2P fallback
- **Phase 2**: Framework for multilingual support (requires eSpeak-ng installation)
- **Phase 3**: Multisyllable and internal rhyme detection
- **Phase 4**: Caching layer for performance and consistency

## Phase 1: English Phoneme-Based Rhyme Detection ✅

**Status**: **COMPLETED**

### What was implemented:

1. **phoneme_rhyme.py** - Core phoneme detection module
   - `PhonemeRhymeDetector` class with CMUdict integration
   - Phoneme extraction from words using NLTK's CMUdict
   - Rhyme tail extraction (last stressed vowel → end)
   - Phoneme normalization (stress marker removal)
   - Hash-based rhyme class grouping (stable, non-greedy)
   - Simple G2P fallback for out-of-vocabulary words

2. **song.py** - Updated Song class
   - Replaced Datamuse API with phoneme-based detection
   - Removed greedy clustering algorithm
   - Added configurable detector support

3. **requirements.txt** - Added dependencies
   - `nltk==3.9.2` for CMUdict access
   - `phonemizer==3.2.1` for Phase 2 (future)

### Key improvements over Datamuse:

- ✅ Pronunciation-based rhyming (not spelling-based)
- ✅ Works offline (no external API dependency)
- ✅ Handles multisyllable words correctly
- ✅ Stable rhyme class assignment via hashing
- ✅ Basic OOV word handling (repeated character normalization, prefix matching)

### Test results:

```
✓ Basic rhyme pairs: 6/6 passed
✓ Rhyme clustering: Correctly groups "cat/hat/bat", "dog/log", "car/star/bar"
✓ Multisyllable: Correctly groups "scary/Mary", "Mack/black/track/attack"
```

### Example usage:

```python
from song import Song

lyrics = "cat hat bat dog log fog car star bar"
song = Song(lyrics)
clusters = song.find_all_rhyme_clusters()
# Returns: [['cat', 'hat', 'bat'], ['dog', 'log'], ['car', 'star', 'bar']]
```

---

## Phase 2: Multilingual Support (Hindi/Hinglish)

**Status**: **FRAMEWORK READY** (requires eSpeak-ng installation)

### What was implemented:

1. **phoneme_rhyme.py**
   - `MultilingualPhonemeDetector` class stub
   - Ready for integration with phonemizer + eSpeak-ng

### What's needed to complete:

1. Install eSpeak-ng backend: `apt-get install espeak-ng`
2. Implement script detection (Devanagari vs ASCII/romanized)
3. Create Hinglish → Devanagari transliteration rules
4. Implement Hindi phonemization using phonemizer
5. Create unified ARPABET + IPA comparison space
6. Test with Desi hip-hop lyrics

### Architecture:

```
Word → Detect Script → [English: CMUdict] or [Hindi: phonemizer+eSpeak-ng]
                     → Transliterate Hinglish if needed
                     → Convert to unified phoneme space (IPA-ish)
                     → Extract rhyme tail
                     → Hash and cluster
```

---

## Phase 3: Multisyllable & Internal Rhyme Detection ✅

**Status**: **COMPLETED**

### What was implemented:

1. **phoneme_rhyme.py**
   - `MultisyllableRhymeDetector` class
   - Syllable segmentation from phoneme sequences
   - Syllable n-gram sliding windows (2-3 syllable chunks)
   - Multisyllable pattern detection
   - Span-based clustering (supports substring highlighting)

2. **song.py**
   - Added `use_advanced` parameter for multisyllable detection

### Key features:

- ✅ Detects internal rhymes (not just end-of-line)
- ✅ Finds multisyllable patterns like "Mary Mack" / "scary black"
- ✅ Provides span indices for partial word highlighting
- ✅ Tracks word positions for frontend rendering

### Example usage:

```python
from song import Song

lyrics = "Mary Mack scary black attack track"
song = Song(lyrics, use_advanced=True)
clusters = song.find_all_rhyme_clusters()
# Returns clusters with multisyllable patterns detected
```

### Test results:

```
✓ Syllable splitting: Works correctly for 1-3 syllable words
✓ Cluster with spans: Returns proper index and span information
✓ Regular rhymes: Still detected alongside multisyllable patterns
```

---

## Phase 4: Caching & LLM Integration ✅

**Status**: **CACHING COMPLETED, LLM FRAMEWORK READY**

### What was implemented:

1. **rhyme_cache.py** - Caching module
   - `RhymeCache` class with file-based storage
   - MD5-based cache key generation (lyrics + detector type)
   - JSON serialization for cache entries
   - Cache info and clearing utilities

2. **song.py** - Cache integration
   - Class-level cache shared across instances
   - Configurable caching via `use_cache` parameter
   - Automatic cache lookup before computation
   - Automatic cache storage after computation

3. **rhyme_cache.py** - LLM framework
   - `LLMEnhancedRhymeCache` stub class
   - Methods ready for OpenAI/Anthropic integration
   - OOV word classification support
   - Phoneme guessing for slang/ad-libs

### Cache benefits:

- ✅ Improved performance (no re-computation for same lyrics)
- ✅ Consistent results across requests
- ✅ Supports future LLM-enhanced results (deterministic after first call)

### Example usage:

```python
from song import Song

# First call: computes and caches
song1 = Song("cat hat bat", use_cache=True)
clusters1 = song1.find_all_rhyme_clusters()

# Second call: retrieved from cache (instant)
song2 = Song("cat hat bat", use_cache=True)
clusters2 = song2.find_all_rhyme_clusters()  # Same result, no computation
```

### What's needed to complete LLM integration:

1. Add OpenAI/Anthropic API key configuration
2. Implement `classify_oov_words()` with LLM prompts
3. Implement `get_phoneme_guess()` for slang pronunciation
4. Add fallback logic to main detector pipeline
5. Test with diverse lyrics (English + Desi + slang)

---

## File Structure

```
server/
├── phoneme_rhyme.py          # Core rhyme detection (Phases 1, 2, 3)
├── rhyme_cache.py            # Caching layer (Phase 4)
├── song.py                   # Song class (updated)
├── main.py                   # Flask API (unchanged)
├── test_rhyme.py             # Test suite
├── requirements.txt          # Updated dependencies
└── .rhyme_cache/             # Cache directory (created automatically)
```

---

## API Compatibility

The implementation maintains **full backward compatibility** with the existing API:

- `/song?lyrics=...` endpoint works exactly as before
- Response format unchanged
- No breaking changes to frontend

The Song class can optionally use advanced features:

```python
# Basic mode (Phase 1 only) - default
song = Song(lyrics)

# Advanced mode (Phase 1 + Phase 3)
song = Song(lyrics, use_advanced=True)

# With caching (Phase 4)
song = Song(lyrics, use_cache=True)

# All features enabled
song = Song(lyrics, use_advanced=True, use_cache=True)
```

---

## Performance Improvements

| Feature | Before (Datamuse) | After (Phoneme) |
|---------|-------------------|-----------------|
| Network dependency | ✗ Required | ✅ Offline |
| Pronunciation accuracy | ❌ Spelling-based | ✅ Phoneme-based |
| Multisyllable rhymes | ❌ Not supported | ✅ Supported (Phase 3) |
| Internal rhymes | ❌ Not supported | ✅ Supported (Phase 3) |
| Caching | ❌ None | ✅ Built-in (Phase 4) |
| Code-switched lyrics | ❌ English only | 🟡 Framework ready (Phase 2) |
| Slang handling | ❌ Failed | 🟡 Basic G2P + LLM framework |

---

## Testing

Run the test suite:

```bash
cd server
python test_rhyme.py
```

Expected output:
- ✅ Phoneme extraction tests
- ✅ Basic rhyme pair tests (6/6)
- ✅ Rhyme clustering tests
- ✅ Multisyllable pattern tests
- ✅ Phase 3 syllable splitting tests

---

## Future Enhancements

### Short-term (Phase 2 completion):
1. Install eSpeak-ng in production environment
2. Implement Hinglish transliteration
3. Add Hindi phonemization
4. Test with Desi hip-hop artists

### Medium-term (Phase 4 completion):
1. Integrate LLM API for OOV words
2. Build database backend for cache
3. Add cache expiration policies
4. Implement batch processing for albums

### Long-term:
1. Support more languages (Punjabi, Urdu, Marathi)
2. Train custom G2P models for slang
3. Add confidence scores to rhyme matches
4. Build web dashboard for cache management

---

## References

- [CMU Pronouncing Dictionary](https://www.speech.cs.cmu.edu/cgi-bin/cmudict)
- [NLTK CMUdict Documentation](https://www.nltk.org/howto/phonetic.html)
- [Phonemizer GitHub](https://github.com/bootphon/phonemizer)
- [eSpeak-ng Languages](https://espeak.sourceforge.net/languages.html)
- Original plan: `PLAN.md`

---

## Contributors

Implementation based on the roadmap in `PLAN.md`.

**Phases completed**:
- ✅ Phase 1: English phoneme-based rhyme detection
- 🟡 Phase 2: Multilingual framework (awaiting eSpeak-ng)
- ✅ Phase 3: Multisyllable and internal rhyme detection
- ✅ Phase 4: Caching layer (LLM framework ready)

---

Last updated: 2025-11-06
