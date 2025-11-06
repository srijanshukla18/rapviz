"""
Song class that consumes lyrics and determines the rhyme scheme.
"""

import re
from typing import Dict, List, Optional

from phoneme_rhyme import PhonemeRhymeDetector, MultisyllableRhymeDetector
from rhyme_cache import RhymeCache


class Song:
    """
    Song class with advanced phoneme-based rhyme detection.

    Supports:
    - Phase 1: English phoneme-based rhyme detection (CMUdict + G2P fallback)
    - Phase 3: Multisyllable and internal rhyme patterns
    - Phase 4: Caching for performance and consistency
    """

    # Class-level cache shared across all instances
    _cache = RhymeCache()

    def __init__(self, lyrics: str, use_advanced: bool = False, use_cache: bool = True):
        """initialize song object

        Arguments:
            lyrics {str} -- string to analyze
            use_advanced {bool} -- use advanced multisyllable detector (default: False)
            use_cache {bool} -- use caching for results (default: True)
        """
        # Use appropriate rhyme detector
        if use_advanced:
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
        self.use_cache = use_cache
        # print(self.lyrics_array)

    def find_all_rhyme_clusters(self):
        """
        Find all rhyme clusters using phoneme-based analysis.

        This replaces the old Datamuse + greedy clustering approach with
        a stable, hash-based phoneme analysis method.

        Phase 4: Includes caching for improved performance and consistency.

        Returns:
            List of rhyme clusters (each cluster is a list of rhyming words)
        """
        # Check cache first if enabled
        if self.use_cache:
            cached_result = self._cache.get(self.lyrics, self.detector_type)
            if cached_result is not None:
                return cached_result

        # Compute rhyme clusters using phoneme-based detection
        rhyme_clusters = self.rhyme_detector.find_rhyme_clusters(self.lyrics_array)

        # Cache the result if caching is enabled
        if self.use_cache:
            self._cache.set(self.lyrics, rhyme_clusters, self.detector_type)

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
