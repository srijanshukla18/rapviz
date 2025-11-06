"""
Caching layer for rhyme annotations.

Phase 4: This module provides caching for rhyme detection results to:
- Improve performance by avoiding re-computation
- Ensure consistency across requests for the same song
- Support LLM-enhanced results that should be stable

Future enhancements:
- Database backend (SQLite or PostgreSQL)
- LLM integration for OOV word classification
- Expiration and cache invalidation strategies
"""

import json
import hashlib
import os
from typing import List, Optional, Dict
from pathlib import Path


class RhymeCache:
    """
    Simple file-based cache for rhyme detection results.

    Cache keys are based on: (lyrics_hash, detector_type)
    This ensures different lyrics or detector types get separate cache entries.
    """

    def __init__(self, cache_dir: str = ".rhyme_cache"):
        """
        Initialize the cache.

        Args:
            cache_dir: Directory to store cache files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    def _generate_cache_key(self, lyrics: str, detector_type: str = "basic") -> str:
        """
        Generate a cache key from lyrics and detector type.

        Args:
            lyrics: The lyrics text
            detector_type: Type of detector ("basic", "multisyllable", etc.)

        Returns:
            Cache key string
        """
        # Create hash from lyrics content
        lyrics_hash = hashlib.md5(lyrics.encode('utf-8')).hexdigest()

        # Combine with detector type
        cache_key = f"{lyrics_hash}_{detector_type}"

        return cache_key

    def _get_cache_path(self, cache_key: str) -> Path:
        """
        Get the file path for a cache key.

        Args:
            cache_key: The cache key

        Returns:
            Path to cache file
        """
        return self.cache_dir / f"{cache_key}.json"

    def get(self, lyrics: str, detector_type: str = "basic") -> Optional[List]:
        """
        Retrieve cached rhyme clusters for given lyrics.

        Args:
            lyrics: The lyrics text
            detector_type: Type of detector used

        Returns:
            Cached rhyme clusters or None if not cached
        """
        cache_key = self._generate_cache_key(lyrics, detector_type)
        cache_path = self._get_cache_path(cache_key)

        if not cache_path.exists():
            return None

        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('rhyme_clusters')
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Failed to read cache: {e}")
            return None

    def set(self, lyrics: str, rhyme_clusters: List, detector_type: str = "basic") -> None:
        """
        Store rhyme clusters in cache.

        Args:
            lyrics: The lyrics text
            rhyme_clusters: The rhyme clusters to cache
            detector_type: Type of detector used
        """
        cache_key = self._generate_cache_key(lyrics, detector_type)
        cache_path = self._get_cache_path(cache_key)

        data = {
            'rhyme_clusters': rhyme_clusters,
            'detector_type': detector_type,
            'cache_key': cache_key
        }

        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except IOError as e:
            print(f"Warning: Failed to write cache: {e}")

    def clear(self) -> None:
        """
        Clear all cached entries.
        """
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                cache_file.unlink()
            except OSError:
                pass

    def get_cache_info(self) -> Dict:
        """
        Get information about the cache.

        Returns:
            Dict with cache statistics
        """
        cache_files = list(self.cache_dir.glob("*.json"))

        return {
            'cache_dir': str(self.cache_dir),
            'num_entries': len(cache_files),
            'total_size_bytes': sum(f.stat().st_size for f in cache_files)
        }


# TODO: Phase 4 - LLM Integration
class LLMEnhancedRhymeCache(RhymeCache):
    """
    Extended cache with LLM integration for handling edge cases.

    This will use an LLM to:
    - Classify OOV (out-of-vocabulary) words
    - Merge slang/ad-libs into existing rhyme classes
    - Improve detection for code-switched lyrics (Hinglish, etc.)

    Future implementation will integrate with OpenAI or similar API.
    """

    def __init__(self, cache_dir: str = ".rhyme_cache", llm_api_key: Optional[str] = None):
        super().__init__(cache_dir)
        self.llm_api_key = llm_api_key

    def classify_oov_words(self, words: List[str], existing_classes: Dict) -> Dict[str, str]:
        """
        Use LLM to classify out-of-vocabulary words into existing rhyme classes.

        Args:
            words: List of OOV words to classify
            existing_classes: Existing rhyme classes (class_id -> list of words)

        Returns:
            Dict mapping OOV word to best matching class_id
        """
        # TODO: Implement LLM integration
        # For now, return empty dict
        return {}

    def get_phoneme_guess(self, word: str) -> Optional[str]:
        """
        Use LLM to guess phonetic pronunciation for slang/unknown words.

        Args:
            word: The word to get pronunciation for

        Returns:
            Phonetic spelling or None
        """
        # TODO: Implement LLM integration
        # Prompt: "Convert this word to IPA phonetic spelling: {word}"
        return None
