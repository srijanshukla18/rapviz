"""
Phoneme-based rhyme detection module.

This module provides sophisticated rhyme detection using phoneme analysis
rather than relying on external APIs. It supports:
- Phase 1: English phoneme extraction using CMUdict
- Phase 2: Multilingual support (Hindi/Hinglish) using phonemizer
- Phase 3: Multisyllable and internal rhyme detection
- Phase 4: LLM assist for edge cases
"""

import re
from typing import List, Dict, Tuple, Optional, Set
from collections import defaultdict
import hashlib

try:
    from nltk.corpus import cmudict
    import nltk
except ImportError:
    cmudict = None
    nltk = None


class PhonemeRhymeDetector:
    """
    Advanced rhyme detection using phoneme analysis.
    """

    def __init__(self):
        """Initialize the phoneme rhyme detector."""
        self.cmu_dict = None
        self._init_cmudict()

        # Cache for phoneme lookups
        self.phoneme_cache = {}

        # Blacklist for common words that shouldn't be highlighted
        self.blacklist = {"a", "the", "can", "an", "of", "to", "in", "is", "it"}

    def _init_cmudict(self):
        """Initialize CMUdict from NLTK."""
        if nltk is None:
            return

        try:
            # Try to load CMUdict
            self.cmu_dict = cmudict.dict()
        except LookupError:
            # Download CMUdict if not available
            try:
                nltk.download('cmudict', quiet=True)
                self.cmu_dict = cmudict.dict()
            except Exception as e:
                print(f"Warning: Could not load CMUdict: {e}")
                self.cmu_dict = None

    def get_phonemes(self, word: str) -> Optional[List[str]]:
        """
        Get phoneme sequence for a word.

        Phase 1: Uses CMUdict for English words
        Phase 1.5: Uses simple rule-based G2P for OOV words

        Args:
            word: The word to get phonemes for

        Returns:
            List of phonemes in ARPABET format, or None if not found
        """
        word_lower = word.lower()

        # Check cache first
        if word_lower in self.phoneme_cache:
            return self.phoneme_cache[word_lower]

        # Check CMUdict
        if self.cmu_dict and word_lower in self.cmu_dict:
            # CMUdict returns a list of possible pronunciations
            # We take the first one (most common)
            phonemes = self.cmu_dict[word_lower][0]
            self.phoneme_cache[word_lower] = phonemes
            return phonemes

        # Phase 1.5: Simple G2P fallback for OOV (out-of-vocabulary) words
        # This is a basic rule-based approach for common patterns
        phonemes = self._simple_g2p(word_lower)
        if phonemes:
            self.phoneme_cache[word_lower] = phonemes
            return phonemes

        return None

    def _simple_g2p(self, word: str) -> Optional[List[str]]:
        """
        Simple rule-based grapheme-to-phoneme converter for OOV words.

        This is a basic fallback for slang and informal spellings.
        Handles common patterns like:
        - Repeated letters (e.g., "shawtyyyy" → "shawty")
        - Common slang patterns

        Args:
            word: The word to convert

        Returns:
            List of phonemes or None
        """
        if not word:
            return None

        # Normalize repeated characters (e.g., "shawtyyyy" → "shawty")
        normalized = re.sub(r'(.)\1{2,}', r'\1', word)

        # Try CMUdict with normalized version
        if self.cmu_dict and normalized in self.cmu_dict:
            return self.cmu_dict[normalized][0]

        # For very short words, skip
        if len(word) < 2:
            return None

        # Basic pattern: try to find similar words in CMUdict
        # Look for words that start with the same 2-3 characters
        if self.cmu_dict:
            prefix = normalized[:3] if len(normalized) >= 3 else normalized
            for dict_word, phonemes_list in self.cmu_dict.items():
                if dict_word.startswith(prefix) and len(dict_word) >= len(normalized) - 2:
                    # Found a similar word, use its phonemes as approximation
                    return phonemes_list[0]

        return None

    def extract_rhyme_tail(self, phonemes: List[str]) -> Optional[Tuple[str, ...]]:
        """
        Extract the rhyme tail from a phoneme sequence.

        The rhyme tail is defined as the phoneme sequence from the last
        stressed vowel to the end of the word.

        For example:
        - "SCAR" → [S, K, AA1, R] → tail: (AA1, R)
        - "CAR" → [K, AA1, R] → tail: (AA1, R)

        Args:
            phonemes: List of phonemes in ARPABET format

        Returns:
            Tuple of phonemes representing the rhyme tail, or None
        """
        if not phonemes:
            return None

        # Find the last stressed vowel (phonemes ending in 0, 1, or 2)
        last_stressed_idx = None
        for i in range(len(phonemes) - 1, -1, -1):
            phoneme = phonemes[i]
            # Check if this is a stressed vowel (ends with 0, 1, or 2)
            if any(phoneme.endswith(stress) for stress in ['0', '1', '2']):
                last_stressed_idx = i
                break

        # If no stressed vowel found, use the last vowel-like phoneme
        if last_stressed_idx is None:
            # Look for any vowel (even unstressed)
            for i in range(len(phonemes) - 1, -1, -1):
                phoneme = phonemes[i]
                # Vowels in ARPABET contain letters like A, E, I, O, U
                if any(v in phoneme for v in ['A', 'E', 'I', 'O', 'U']):
                    last_stressed_idx = i
                    break

        # If still no vowel found, use the whole word
        if last_stressed_idx is None:
            return tuple(phonemes)

        # Return from last stressed vowel to end
        return tuple(phonemes[last_stressed_idx:])

    def normalize_phoneme_tail(self, tail: Tuple[str, ...]) -> Tuple[str, ...]:
        """
        Normalize a phoneme tail for comparison.

        This removes stress markers so that different stress patterns
        still rhyme (e.g., "present" as noun vs verb).

        Args:
            tail: Phoneme tail tuple

        Returns:
            Normalized tail tuple
        """
        if not tail:
            return tail

        # Remove stress markers (0, 1, 2) from vowels
        normalized = []
        for phoneme in tail:
            # Remove trailing digits
            clean_phoneme = re.sub(r'[012]$', '', phoneme)
            normalized.append(clean_phoneme)

        return tuple(normalized)

    def hash_tail(self, tail: Tuple[str, ...]) -> str:
        """
        Create a hash for a phoneme tail.

        This is used to group rhyming words into classes.

        Args:
            tail: Normalized phoneme tail

        Returns:
            Hash string representing the rhyme class
        """
        if not tail:
            return ""

        # Join phonemes and create a simple hash
        tail_str = "-".join(tail)
        # Use MD5 for a shorter hash
        return hashlib.md5(tail_str.encode()).hexdigest()[:8]

    def words_rhyme(self, word1: str, word2: str) -> bool:
        """
        Check if two words rhyme based on phoneme analysis.

        Args:
            word1: First word
            word2: Second word

        Returns:
            True if words rhyme, False otherwise
        """
        # Check blacklist
        if word1.lower() in self.blacklist or word2.lower() in self.blacklist:
            return False

        # Get phonemes for both words
        phonemes1 = self.get_phonemes(word1)
        phonemes2 = self.get_phonemes(word2)

        # If we can't get phonemes for either word, they don't rhyme
        if phonemes1 is None or phonemes2 is None:
            return False

        # Extract and normalize rhyme tails
        tail1 = self.extract_rhyme_tail(phonemes1)
        tail2 = self.extract_rhyme_tail(phonemes2)

        if tail1 is None or tail2 is None:
            return False

        norm_tail1 = self.normalize_phoneme_tail(tail1)
        norm_tail2 = self.normalize_phoneme_tail(tail2)

        # Check if normalized tails match
        return norm_tail1 == norm_tail2

    def find_rhyme_clusters(self, words: List[str]) -> List[List[str]]:
        """
        Group words into rhyme clusters based on phoneme analysis.

        This is the main method that replaces the Datamuse-based approach.
        Instead of greedy clustering, we use hash-based grouping for stability.

        Args:
            words: List of words to analyze

        Returns:
            List of rhyme clusters (each cluster is a list of rhyming words)
        """
        # Map from rhyme class hash to words in that class
        rhyme_classes: Dict[str, List[str]] = defaultdict(list)

        # Process each word
        for word in words:
            word_clean = word.lower().strip()

            # Skip empty words or blacklisted words
            if not word_clean or word_clean in self.blacklist:
                continue

            # Get phonemes
            phonemes = self.get_phonemes(word_clean)
            if phonemes is None:
                # TODO: Phase 1.5 - Add G2P fallback here
                continue

            # Extract and normalize rhyme tail
            tail = self.extract_rhyme_tail(phonemes)
            if tail is None:
                continue

            norm_tail = self.normalize_phoneme_tail(tail)

            # Hash the tail to get rhyme class ID
            rhyme_class_id = self.hash_tail(norm_tail)

            # Add word to its rhyme class
            rhyme_classes[rhyme_class_id].append(word)

        # Filter out single-word clusters (not rhymes)
        clusters = [cluster for cluster in rhyme_classes.values() if len(cluster) > 1]

        return clusters

    def get_rhyme_class_id(self, word: str) -> Optional[str]:
        """
        Get the rhyme class ID for a word.

        This is useful for assigning consistent colors to rhyme groups.

        Args:
            word: The word to get rhyme class for

        Returns:
            Rhyme class ID (hash) or None if word not recognized
        """
        phonemes = self.get_phonemes(word)
        if phonemes is None:
            return None

        tail = self.extract_rhyme_tail(phonemes)
        if tail is None:
            return None

        norm_tail = self.normalize_phoneme_tail(tail)
        return self.hash_tail(norm_tail)


# Phase 2 - Multilingual support (Hindi/Hinglish)
class MultilingualPhonemeDetector(PhonemeRhymeDetector):
    """
    Extended detector with multilingual support (Hindi/Hinglish).

    This detector handles:
    - Devanagari script (Hindi/Marathi/Nepali)
    - Romanized Hinglish
    - Code-switched lyrics (English + Hindi mixed)
    - Unified phoneme comparison across languages
    """

    def __init__(self):
        super().__init__()

        # Import multilingual modules
        try:
            from multilingual_phoneme import (
                ScriptDetector,
                HinglishTransliterator,
                HindiPhonemeMapper,
                UnifiedPhonemeMapper
            )
            self.script_detector = ScriptDetector()
            self.hinglish_translit = HinglishTransliterator()
            self.hindi_mapper = HindiPhonemeMapper()
            self.unified_mapper = UnifiedPhonemeMapper()
            self.multilingual_enabled = True
        except ImportError as e:
            print(f"Warning: Multilingual support not available: {e}")
            self.multilingual_enabled = False

    def get_phonemes(self, word: str) -> Optional[List[str]]:
        """
        Get phoneme sequence for a word (multilingual version).

        This overrides the parent method to support Hindi/Hinglish.

        Process:
        1. Detect script (Devanagari / ASCII / mixed)
        2. For Devanagari: directly phonemize to IPA
        3. For ASCII: check if Hinglish, transliterate if needed
        4. For English: use parent CMUdict method
        5. Convert all to unified IPA-ish space

        Args:
            word: The word to get phonemes for

        Returns:
            List of phonemes in unified IPA-ish format
        """
        if not self.multilingual_enabled:
            # Fallback to English-only
            return super().get_phonemes(word)

        # Detect script
        script_type = self.script_detector.detect_script(word)

        # Handle Devanagari script
        if script_type == 'devanagari':
            hindi_phonemes = self.hindi_mapper.devanagari_to_phonemes(word)
            # Already in IPA-ish format, just return
            return hindi_phonemes if hindi_phonemes else None

        # Handle ASCII (could be English or Hinglish)
        if script_type == 'ascii':
            # Check if it looks like Hinglish
            if self.hinglish_translit.looks_like_hinglish(word):
                # Try to transliterate to Devanagari
                devanagari = self.hinglish_translit.transliterate_to_devanagari(word)
                if devanagari:
                    hindi_phonemes = self.hindi_mapper.devanagari_to_phonemes(devanagari)
                    if hindi_phonemes:
                        return hindi_phonemes

            # Not Hinglish or transliteration failed - try English
            english_phonemes = super().get_phonemes(word)
            if english_phonemes:
                # Convert ARPABET to unified IPA-ish
                unified_phonemes = self.unified_mapper.arpabet_to_unified(english_phonemes)
                return unified_phonemes

        # Fallback to English
        english_phonemes = super().get_phonemes(word)
        if english_phonemes:
            unified_phonemes = self.unified_mapper.arpabet_to_unified(english_phonemes)
            return unified_phonemes

        return None

    def extract_rhyme_tail(self, phonemes: List[str]) -> Optional[Tuple[str, ...]]:
        """
        Extract rhyme tail for multilingual phonemes.

        For IPA phonemes, we find the last vowel and take from there to end.

        Args:
            phonemes: List of IPA-ish phonemes

        Returns:
            Tuple of phonemes representing the rhyme tail
        """
        if not phonemes:
            return None

        # Define vowel characters (IPA vowels)
        vowels = {'a', 'e', 'i', 'o', 'u', 'æ', 'ɑ', 'ɔ', 'ɛ', 'ɪ', 'ʊ', 'ʌ', 'ə', 'ɜ'}

        # Find last vowel
        last_vowel_idx = None
        for i in range(len(phonemes) - 1, -1, -1):
            phoneme = phonemes[i]
            # Check if phoneme contains a vowel
            if any(v in phoneme for v in vowels):
                last_vowel_idx = i
                break

        # If no vowel found, use whole word
        if last_vowel_idx is None:
            return tuple(phonemes)

        # Return from last vowel to end
        return tuple(phonemes[last_vowel_idx:])

    def normalize_phoneme_tail(self, tail: Tuple[str, ...]) -> Tuple[str, ...]:
        """
        Normalize a phoneme tail for comparison (multilingual version).

        Uses unified mapper to ensure consistency across languages.

        Args:
            tail: Phoneme tail tuple

        Returns:
            Normalized tail tuple
        """
        if not tail:
            return tail

        if self.multilingual_enabled:
            # Use unified normalization
            normalized = self.unified_mapper.normalize_for_comparison(list(tail))
            return normalized
        else:
            # Fallback to parent method
            return super().normalize_phoneme_tail(tail)


# Phase 3 - Multisyllable and internal rhyme detection
class MultisyllableRhymeDetector(PhonemeRhymeDetector):
    """
    Extended detector with multisyllable and internal rhyme detection.

    This detector can find:
    - Internal rhymes (rhymes within a line, not just at the end)
    - Multisyllable rhyme patterns (2-3 syllable chunks that repeat)
    - Partial word rhymes (substring highlighting)
    """

    def __init__(self):
        super().__init__()
        self.syllable_chunk_size = 2  # Look for 2-3 syllable patterns

    def split_into_syllables(self, phonemes: List[str]) -> List[List[str]]:
        """
        Split a phoneme sequence into syllables.

        A syllable typically has one vowel sound plus surrounding consonants.

        Args:
            phonemes: List of phonemes

        Returns:
            List of syllables (each syllable is a list of phonemes)
        """
        if not phonemes:
            return []

        syllables = []
        current_syllable = []

        for i, phoneme in enumerate(phonemes):
            # Check if this is a vowel (contains A, E, I, O, U)
            is_vowel = any(v in phoneme for v in ['A', 'E', 'I', 'O', 'U'])

            current_syllable.append(phoneme)

            # If this is a vowel and not the last phoneme
            if is_vowel:
                # Look ahead - if next phoneme is also a vowel, end syllable here
                if i + 1 < len(phonemes):
                    next_phoneme = phonemes[i + 1]
                    next_is_vowel = any(v in next_phoneme for v in ['A', 'E', 'I', 'O', 'U'])

                    if next_is_vowel:
                        syllables.append(current_syllable)
                        current_syllable = []
                    # If next is consonant and there are more phonemes after, might split
                    elif i + 2 < len(phonemes):
                        # Keep the consonant with this syllable
                        pass
                else:
                    # Last phoneme and it's a vowel - end syllable
                    syllables.append(current_syllable)
                    current_syllable = []

        # Add any remaining phonemes as the last syllable
        if current_syllable:
            syllables.append(current_syllable)

        return syllables

    def get_syllable_chunks(self, words: List[str], chunk_size: int = 2) -> List[Tuple[Tuple[str, ...], List[Tuple[int, int]]]]:
        """
        Create sliding windows of N-syllable chunks across words.

        This enables detection of multisyllable rhyme patterns like
        "Mary Mack" / "scary act".

        Args:
            words: List of words
            chunk_size: Number of syllables per chunk (default 2)

        Returns:
            List of (phoneme_chunk, word_positions) tuples
            where word_positions is list of (word_idx, syllable_idx_within_word)
        """
        # First, get all syllables with their word positions
        all_syllables = []  # List of (syllables, word_idx)

        for word_idx, word in enumerate(words):
            phonemes = self.get_phonemes(word)
            if phonemes:
                syllables = self.split_into_syllables(phonemes)
                for syl_idx, syllable in enumerate(syllables):
                    all_syllables.append((syllable, word_idx, syl_idx))

        # Now create sliding windows
        chunks = []
        for i in range(len(all_syllables) - chunk_size + 1):
            # Get chunk_size syllables
            window = all_syllables[i:i + chunk_size]

            # Combine phonemes from all syllables in window
            chunk_phonemes = []
            positions = []
            for syllable, word_idx, syl_idx in window:
                chunk_phonemes.extend(syllable)
                positions.append((word_idx, syl_idx))

            # Normalize the chunk (remove stress markers)
            normalized_chunk = tuple(re.sub(r'[012]$', '', p) for p in chunk_phonemes)

            chunks.append((normalized_chunk, positions))

        return chunks

    def find_multisyllable_patterns(self, words: List[str]) -> Dict[str, List[Dict]]:
        """
        Find repeated multisyllable patterns in the lyrics.

        This detects patterns like:
        - "Mary Mack" / "scary black"
        - Internal rhymes within lines

        Args:
            words: List of words

        Returns:
            Dict mapping pattern_id to list of occurrences
            Each occurrence has: {
                'words': [word_indices],
                'pattern': normalized phoneme pattern
            }
        """
        # Get syllable chunks
        chunks = self.get_syllable_chunks(words, chunk_size=2)

        # Group by pattern
        pattern_groups: Dict[str, List[Dict]] = defaultdict(list)

        for chunk_phonemes, positions in chunks:
            if not chunk_phonemes:
                continue

            # Hash the pattern
            pattern_id = hashlib.md5("-".join(chunk_phonemes).encode()).hexdigest()[:8]

            # Get the word indices involved
            word_indices = [pos[0] for pos in positions]

            pattern_groups[pattern_id].append({
                'words': word_indices,
                'pattern': chunk_phonemes,
                'positions': positions
            })

        # Filter out patterns that only appear once
        repeated_patterns = {
            pattern_id: occurrences
            for pattern_id, occurrences in pattern_groups.items()
            if len(occurrences) > 1
        }

        return repeated_patterns

    def find_rhyme_clusters_with_spans(self, words: List[str]) -> List[Dict]:
        """
        Find rhyme clusters with span information for substring highlighting.

        This is the Phase 3 version that supports partial word highlighting.

        Args:
            words: List of words

        Returns:
            List of rhyme cluster objects with span information:
            [{
                'cluster_id': str,
                'words': [{'word': str, 'index': int, 'span': (start, end)}]
            }]
        """
        # Start with basic word-level clusters
        basic_clusters = self.find_rhyme_clusters(words)

        # Convert to span format
        result = []
        cluster_counter = 0

        for cluster in basic_clusters:
            cluster_obj = {
                'cluster_id': f'cluster_{cluster_counter}',
                'words': []
            }

            for word in cluster:
                # Find all indices where this word appears
                for idx, w in enumerate(words):
                    if w.lower() == word.lower():
                        cluster_obj['words'].append({
                            'word': word,
                            'index': idx,
                            'span': (0, len(word))  # Full word for now
                        })

            result.append(cluster_obj)
            cluster_counter += 1

        # Add multisyllable patterns
        multi_patterns = self.find_multisyllable_patterns(words)

        for pattern_id, occurrences in multi_patterns.items():
            cluster_obj = {
                'cluster_id': f'multi_{pattern_id}',
                'words': [],
                'is_multisyllable': True
            }

            for occurrence in occurrences:
                for word_idx in occurrence['words']:
                    cluster_obj['words'].append({
                        'word': words[word_idx],
                        'index': word_idx,
                        'span': (0, len(words[word_idx]))  # Could be refined to partial spans
                    })

            if len(cluster_obj['words']) > 1:
                result.append(cluster_obj)

        return result
