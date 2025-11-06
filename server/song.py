"""
Song class that consumes lyrics and determines the rhyme scheme.
"""

import re
from typing import Dict, List, Optional

from phoneme_rhyme import PhonemeRhymeDetector, MultisyllableRhymeDetector, MultilingualPhonemeDetector
from rhyme_cache import RhymeCache, LLMEnhancedRhymeCache


class Song:
    """
    Song class with advanced phoneme-based rhyme detection.

    Supports:
    - Phase 1: English phoneme-based rhyme detection (CMUdict + G2P fallback)
    - Phase 2: Multilingual support (Hindi/Hinglish)
    - Phase 3: Multisyllable and internal rhyme patterns
    - Phase 4: Caching and LLM enhancement for edge cases
    """

    # Class-level caches shared across all instances
    _cache = RhymeCache()
    _llm_cache = None  # Lazy initialization with API key

    def __init__(
        self,
        lyrics: str,
        use_advanced: bool = False,
        use_multilingual: bool = False,
        use_cache: bool = True,
        use_llm: bool = False,
        llm_api_key: Optional[str] = None
    ):
        """initialize song object

        Arguments:
            lyrics {str} -- string to analyze
            use_advanced {bool} -- use advanced multisyllable detector (default: False)
            use_multilingual {bool} -- use multilingual detector for Hindi/Hinglish (default: False)
            use_cache {bool} -- use caching for results (default: True)
            use_llm {bool} -- use LLM for OOV word classification (default: False)
            llm_api_key {str} -- Anthropic API key for LLM features (optional)
        """
        # Use appropriate rhyme detector
        if use_multilingual:
            self.rhyme_detector = MultilingualPhonemeDetector()
            self.detector_type = "multilingual"
        elif use_advanced:
            self.rhyme_detector = MultisyllableRhymeDetector()
            self.detector_type = "multisyllable"
        else:
            self.rhyme_detector = PhonemeRhymeDetector()
            self.detector_type = "basic"

        self.lyrics = lyrics
        replace_all_punc = re.sub("[.,:?!;\-()']", "", self.lyrics)
        self.lyrics_array = re.split("[ |\n]", replace_all_punc)

        # Filter out empty strings
        self.lyrics_array = [word for word in self.lyrics_array if word.strip()]

        self.blacklist = ["a", "the", "can", "an"]
        self.use_advanced = use_advanced
        self.use_multilingual = use_multilingual
        self.use_cache = use_cache
        self.use_llm = use_llm

        # Initialize LLM cache if needed
        if use_llm and Song._llm_cache is None:
            Song._llm_cache = LLMEnhancedRhymeCache(llm_api_key=llm_api_key)
        # print(self.lyrics_array)

    def find_all_rhyme_clusters(self):
        """
        Find all rhyme clusters using phoneme-based analysis.

        This replaces the old Datamuse + greedy clustering approach with
        a stable, hash-based phoneme analysis method.

        Phase 4: Includes caching and optional LLM enhancement for edge cases.

        Returns:
            List of rhyme clusters (each cluster is a list of rhyming words)
        """
        # Check cache first if enabled
        cache_key_suffix = f"{self.detector_type}_llm" if self.use_llm else self.detector_type
        if self.use_cache:
            cached_result = self._cache.get(self.lyrics, cache_key_suffix)
            if cached_result is not None:
                return cached_result

        # Compute rhyme clusters using phoneme-based detection
        rhyme_clusters = self.rhyme_detector.find_rhyme_clusters(self.lyrics_array)

        # Phase 4: Optionally enhance with LLM for OOV words
        if self.use_llm and Song._llm_cache and Song._llm_cache.llm_enabled:
            rhyme_clusters = Song._llm_cache.enhance_rhyme_detection(
                self.lyrics_array,
                self.rhyme_detector,
                rhyme_clusters
            )

        # Cache the result if caching is enabled
        if self.use_cache:
            self._cache.set(self.lyrics, rhyme_clusters, cache_key_suffix)

        return rhyme_clusters

    # Keep these methods for backwards compatibility if needed
    def rhyme(self, word1: str, word2: str) -> bool:
        """
        Check if two words rhyme using phoneme analysis.

        Arguments:
            word1 {str} -- first word
            word2 {str} -- second word

        Returns:
            bool -- does the two words rhyme
        """
        return self.rhyme_detector.words_rhyme(word1, word2)
