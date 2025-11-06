"""
Multilingual phoneme detection for Hindi/Hinglish rap lyrics.

Phase 2: This module provides multilingual rhyme detection for:
- Devanagari script (Hindi/Marathi/Nepali)
- Romanized Hinglish (Latin script with Hindi words)
- Code-switched lyrics (English + Hindi mixed)
"""

import re
from typing import List, Optional, Dict, Tuple
from collections import defaultdict

try:
    from indic_transliteration import sanscript
    from indic_transliteration.sanscript import transliterate
    TRANSLITERATION_AVAILABLE = True
except ImportError:
    TRANSLITERATION_AVAILABLE = False
    print("Warning: indic-transliteration not available")


class ScriptDetector:
    """
    Detect the script of a word (Devanagari vs Latin/ASCII).
    """

    @staticmethod
    def is_devanagari(text: str) -> bool:
        """
        Check if text contains Devanagari characters.

        Args:
            text: Text to check

        Returns:
            True if text contains Devanagari characters
        """
        # Devanagari Unicode range: U+0900 to U+097F
        devanagari_pattern = re.compile(r'[\u0900-\u097F]')
        return bool(devanagari_pattern.search(text))

    @staticmethod
    def is_ascii(text: str) -> bool:
        """
        Check if text is pure ASCII.

        Args:
            text: Text to check

        Returns:
            True if text is ASCII only
        """
        try:
            text.encode('ascii')
            return True
        except UnicodeEncodeError:
            return False

    @staticmethod
    def detect_script(word: str) -> str:
        """
        Detect the script type of a word.

        Args:
            word: Word to analyze

        Returns:
            One of: 'devanagari', 'ascii', 'mixed', 'other'
        """
        if not word:
            return 'other'

        has_devanagari = ScriptDetector.is_devanagari(word)
        has_ascii = ScriptDetector.is_ascii(word)

        if has_devanagari and not has_ascii:
            return 'devanagari'
        elif has_ascii and not has_devanagari:
            return 'ascii'
        elif has_devanagari and has_ascii:
            return 'mixed'
        else:
            return 'other'


class HinglishTransliterator:
    """
    Transliterate romanized Hinglish to Devanagari.

    This handles common patterns in Desi hip-hop:
    - "tera" → तेरा
    - "bhai" → भाई
    - "kala" → काला
    """

    # Common Hinglish words → Devanagari mapping
    COMMON_WORDS = {
        'bhai': 'भाई',
        'yaar': 'यार',
        'tera': 'तेरा',
        'mera': 'मेरा',
        'kya': 'क्या',
        'hai': 'है',
        'hoon': 'हूं',
        'nahi': 'नहीं',
        'koi': 'कोई',
        'dil': 'दिल',
        'pyar': 'प्यार',
        'jaan': 'जान',
        'aaj': 'आज',
        'kal': 'कल',
        'raat': 'रात',
        'din': 'दिन',
        'kala': 'काला',
        'galla': 'गल्ला',
        'bakchod': 'बकचोद',
        'dhadkan': 'धड़कन',
        'gaadi': 'गाड़ी',
        'paisa': 'पैसा',
        'chora': 'छोरा',
        'kaam': 'काम',
        'naam': 'नाम',
        'shaam': 'शाम',
        'jaga': 'जगह',
        'sach': 'सच',
        'jhoot': 'झूठ',
        'dost': 'दोस्त',
        'flow': 'फ्लो',  # English loanword
        'game': 'गेम',
        'boss': 'बॉस',
    }

    # Hinglish heuristic patterns
    HINGLISH_PATTERNS = [
        'aa', 'ii', 'uu', 'ee', 'oo',  # Long vowels
        'kh', 'gh', 'ch', 'chh', 'jh', 'th', 'dh', 'ph', 'bh',  # Aspirated consonants
        'sh', 'zh',  # Sibilants
        'ng', 'ny',  # Nasals
        'ri', 'ru',  # र combinations
    ]

    @staticmethod
    def looks_like_hinglish(word: str) -> bool:
        """
        Heuristically determine if a word looks like romanized Hindi.

        Args:
            word: Word to check

        Returns:
            True if word looks like Hinglish
        """
        word_lower = word.lower()

        # Check common word list
        if word_lower in HinglishTransliterator.COMMON_WORDS:
            return True

        # Check for Hinglish patterns
        for pattern in HinglishTransliterator.HINGLISH_PATTERNS:
            if pattern in word_lower:
                return True

        # Check for doubled consonants (common in Hinglish)
        if re.search(r'([bcdfghjklmnpqrstvwxyz])\1', word_lower):
            return True

        return False

    @staticmethod
    def transliterate_to_devanagari(word: str) -> Optional[str]:
        """
        Transliterate romanized Hinglish word to Devanagari.

        Args:
            word: Romanized Hindi word

        Returns:
            Devanagari string or None if transliteration fails
        """
        word_lower = word.lower()

        # Check common words first
        if word_lower in HinglishTransliterator.COMMON_WORDS:
            return HinglishTransliterator.COMMON_WORDS[word_lower]

        # Use indic-transliteration if available
        if TRANSLITERATION_AVAILABLE:
            try:
                # Try ITRANS scheme (common for romanization)
                devanagari = transliterate(word, sanscript.ITRANS, sanscript.DEVANAGARI)
                return devanagari
            except Exception:
                pass

        # Fallback: basic rule-based transliteration
        return HinglishTransliterator._basic_transliterate(word)

    @staticmethod
    def _basic_transliterate(word: str) -> str:
        """
        Basic rule-based transliteration as fallback.

        Args:
            word: Romanized word

        Returns:
            Best-effort Devanagari representation
        """
        # This is a simplified mapping - not perfect but better than nothing
        vowel_map = {
            'a': 'अ', 'aa': 'आ', 'i': 'इ', 'ii': 'ई',
            'u': 'उ', 'uu': 'ऊ', 'e': 'ए', 'ai': 'ऐ',
            'o': 'ओ', 'au': 'औ'
        }

        consonant_map = {
            'k': 'क', 'kh': 'ख', 'g': 'ग', 'gh': 'घ',
            'ch': 'च', 'chh': 'छ', 'j': 'ज', 'jh': 'झ',
            't': 'त', 'th': 'थ', 'd': 'द', 'dh': 'ध',
            'n': 'न', 'p': 'प', 'ph': 'फ', 'b': 'ब',
            'bh': 'भ', 'm': 'म', 'y': 'य', 'r': 'र',
            'l': 'ल', 'v': 'व', 'w': 'व', 'sh': 'श',
            's': 'स', 'h': 'ह'
        }

        # Very basic conversion (this is approximate)
        result = word
        for rom, dev in sorted(consonant_map.items(), key=lambda x: -len(x[0])):
            result = result.replace(rom, dev)

        return result


class HindiPhonemeMapper:
    """
    Map Devanagari characters to IPA-like phoneme representations.

    This creates a unified phoneme space that can be compared with
    ARPABET phonemes from English CMUdict.
    """

    # Mapping Devanagari vowels to IPA-ish representations
    VOWEL_MAP = {
        'अ': 'ə', 'आ': 'aː', 'इ': 'i', 'ई': 'iː',
        'उ': 'u', 'ऊ': 'uː', 'ऋ': 'ri', 'ए': 'eː',
        'ऐ': 'ɛː', 'ओ': 'oː', 'औ': 'ɔː',
        'ा': 'aː', 'ि': 'i', 'ी': 'iː', 'ु': 'u',
        'ू': 'uː', 'े': 'eː', 'ै': 'ɛː', 'ो': 'oː',
        'ौ': 'ɔː', '्': '',  # Halant (virama) - removes inherent vowel
    }

    # Mapping Devanagari consonants to IPA-ish
    CONSONANT_MAP = {
        'क': 'k', 'ख': 'kʰ', 'ग': 'g', 'घ': 'gʰ', 'ङ': 'ŋ',
        'च': 'tʃ', 'छ': 'tʃʰ', 'ज': 'dʒ', 'झ': 'dʒʰ', 'ञ': 'ɲ',
        'ट': 'ʈ', 'ठ': 'ʈʰ', 'ड': 'ɖ', 'ढ': 'ɖʰ', 'ण': 'ɳ',
        'त': 't', 'थ': 'tʰ', 'द': 'd', 'ध': 'dʰ', 'न': 'n',
        'प': 'p', 'फ': 'pʰ', 'ब': 'b', 'भ': 'bʰ', 'म': 'm',
        'य': 'j', 'र': 'r', 'ल': 'l', 'व': 'ʋ', 'श': 'ʃ',
        'ष': 'ʂ', 'स': 's', 'ह': 'ɦ', 'ळ': 'ɭ', 'क्ष': 'kʂ',
        'ज्ञ': 'ɡj', 'ड़': 'ɽ', 'ढ़': 'ɽʰ',
    }

    @staticmethod
    def devanagari_to_phonemes(text: str) -> List[str]:
        """
        Convert Devanagari text to phoneme list.

        Args:
            text: Devanagari text

        Returns:
            List of IPA-ish phoneme strings
        """
        phonemes = []

        i = 0
        while i < len(text):
            char = text[i]

            # Check for two-character consonant clusters
            if i + 1 < len(text):
                two_char = text[i:i+2]
                if two_char in HindiPhonemeMapper.CONSONANT_MAP:
                    phonemes.append(HindiPhonemeMapper.CONSONANT_MAP[two_char])
                    i += 2
                    continue

            # Check vowels
            if char in HindiPhonemeMapper.VOWEL_MAP:
                vowel = HindiPhonemeMapper.VOWEL_MAP[char]
                if vowel:  # Skip empty (halant)
                    phonemes.append(vowel)
                i += 1
                continue

            # Check consonants
            if char in HindiPhonemeMapper.CONSONANT_MAP:
                phonemes.append(HindiPhonemeMapper.CONSONANT_MAP[char])
                # Add inherent 'ə' vowel unless followed by virama or vowel sign
                if i + 1 < len(text):
                    next_char = text[i + 1]
                    if next_char not in HindiPhonemeMapper.VOWEL_MAP:
                        phonemes.append('ə')
                else:
                    phonemes.append('ə')
                i += 1
                continue

            # Skip unknown characters
            i += 1

        return phonemes


class UnifiedPhonemeMapper:
    """
    Create a unified phoneme comparison space for English (ARPABET) and Hindi (IPA).

    This allows us to compare rhyme tails across languages by normalizing
    both to a common representation.
    """

    # Map ARPABET vowels to IPA-ish for comparison
    ARPABET_TO_IPA = {
        # Vowels
        'AA': 'ɑ', 'AE': 'æ', 'AH': 'ʌ', 'AO': 'ɔ', 'AW': 'aʊ',
        'AY': 'aɪ', 'EH': 'ɛ', 'ER': 'ɜr', 'EY': 'eɪ', 'IH': 'ɪ',
        'IY': 'i', 'OW': 'oʊ', 'OY': 'ɔɪ', 'UH': 'ʊ', 'UW': 'u',
        # Consonants
        'B': 'b', 'CH': 'tʃ', 'D': 'd', 'DH': 'ð', 'F': 'f',
        'G': 'g', 'HH': 'h', 'JH': 'dʒ', 'K': 'k', 'L': 'l',
        'M': 'm', 'N': 'n', 'NG': 'ŋ', 'P': 'p', 'R': 'r',
        'S': 's', 'SH': 'ʃ', 'T': 't', 'TH': 'θ', 'V': 'v',
        'W': 'w', 'Y': 'j', 'Z': 'z', 'ZH': 'ʒ',
    }

    @staticmethod
    def arpabet_to_unified(arpabet_phonemes: List[str]) -> List[str]:
        """
        Convert ARPABET phonemes to unified IPA-ish representation.

        Args:
            arpabet_phonemes: List of ARPABET phonemes (e.g., ['K', 'AE1', 'T'])

        Returns:
            List of unified phonemes
        """
        unified = []
        for phoneme in arpabet_phonemes:
            # Remove stress markers (0, 1, 2)
            clean_phoneme = re.sub(r'[012]$', '', phoneme)

            # Map to IPA
            if clean_phoneme in UnifiedPhonemeMapper.ARPABET_TO_IPA:
                unified.append(UnifiedPhonemeMapper.ARPABET_TO_IPA[clean_phoneme])
            else:
                # Keep unknown phonemes as-is
                unified.append(clean_phoneme.lower())

        return unified

    @staticmethod
    def normalize_for_comparison(phonemes: List[str]) -> Tuple[str, ...]:
        """
        Normalize phoneme list for rhyme comparison.

        This creates a coarse representation that works across languages.

        Args:
            phonemes: List of phonemes (IPA-ish)

        Returns:
            Tuple of normalized phonemes
        """
        # Simplify similar sounds
        normalized = []
        for p in phonemes:
            # Collapse long/short vowel distinctions
            p = p.replace('ː', '')
            # Collapse aspiration
            p = p.replace('ʰ', '')
            # Simplify affricates
            p = p.replace('tʃ', 'ch')
            p = p.replace('dʒ', 'j')
            normalized.append(p)

        return tuple(normalized)


# Export all classes
__all__ = [
    'ScriptDetector',
    'HinglishTransliterator',
    'HindiPhonemeMapper',
    'UnifiedPhonemeMapper',
]
