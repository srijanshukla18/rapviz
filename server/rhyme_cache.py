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


# Phase 4 - LLM Integration (COMPLETED)
class LLMEnhancedRhymeCache(RhymeCache):
    """
    Extended cache with LLM integration for handling edge cases.

    This uses Claude (Anthropic) to:
    - Classify OOV (out-of-vocabulary) words
    - Merge slang/ad-libs into existing rhyme classes
    - Improve detection for code-switched lyrics (Hinglish, etc.)
    - Guess pronunciations for unknown words
    """

    def __init__(self, cache_dir: str = ".rhyme_cache", llm_api_key: Optional[str] = None):
        super().__init__(cache_dir)
        self.llm_api_key = llm_api_key or os.getenv("ANTHROPIC_API_KEY")
        self.client = None

        # Initialize Anthropic client if API key is available
        if self.llm_api_key:
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=self.llm_api_key)
                self.llm_enabled = True
            except ImportError:
                print("Warning: anthropic package not installed")
                self.llm_enabled = False
        else:
            self.llm_enabled = False

    def classify_oov_words(self, words: List[str], existing_classes: Dict[str, List[str]]) -> Dict[str, str]:
        """
        Use LLM to classify out-of-vocabulary words into existing rhyme classes.

        Args:
            words: List of OOV words to classify
            existing_classes: Existing rhyme classes (class_id -> list of words)

        Returns:
            Dict mapping OOV word to best matching class_id
        """
        if not self.llm_enabled or not words or not existing_classes:
            return {}

        # Prepare the prompt
        classes_str = "\n".join([
            f"Class {class_id}: {', '.join(class_words[:5])}"
            for class_id, class_words in existing_classes.items()
        ])

        prompt = f"""You are a pronunciation and rhyme expert analyzing rap lyrics.

I have these existing rhyme classes:
{classes_str}

I need you to classify these out-of-vocabulary words into the most appropriate rhyme class based on how they sound:
Words: {', '.join(words)}

For each word, determine which class it rhymes with (or "NONE" if it doesn't rhyme with any).

Respond in JSON format:
{{
  "word1": "class_id or NONE",
  "word2": "class_id or NONE",
  ...
}}

Focus on pronunciation and sound, not spelling."""

        try:
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Parse response
            response_text = message.content[0].text

            # Extract JSON from response
            import json
            import re

            # Try to find JSON in the response
            json_match = re.search(r'\{[^}]+\}', response_text, re.DOTALL)
            if json_match:
                classifications = json.loads(json_match.group())
                # Filter out NONE values
                return {k: v for k, v in classifications.items() if v != "NONE"}

        except Exception as e:
            print(f"LLM classification failed: {e}")

        return {}

    def get_phoneme_guess(self, word: str) -> Optional[str]:
        """
        Use LLM to guess phonetic pronunciation for slang/unknown words.

        Args:
            word: The word to get pronunciation for

        Returns:
            Phonetic spelling in IPA-ish format or None
        """
        if not self.llm_enabled or not word:
            return None

        prompt = f"""You are a pronunciation expert. Convert this word to IPA phonetic symbols.

Word: "{word}"

This might be:
- English slang (e.g., "shawtyyyy", "opp", "skrrt")
- Hinglish/Desi slang (e.g., "bakchod", "gaadi")
- Stretched/repeated letters (e.g., "yooooo")

Provide a simple IPA representation focusing on the core sounds.
Respond with ONLY the IPA string, nothing else.

Examples:
- "cat" → "kæt"
- "shawty" → "ʃɔːti"
- "bhai" → "bʰaːi"

Now convert: {word}"""

        try:
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=256,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Parse response - should be simple IPA string
            response_text = message.content[0].text.strip()

            # Basic validation - should look like IPA
            if len(response_text) > 0 and len(response_text) < 50:
                return response_text

        except Exception as e:
            print(f"LLM phoneme guess failed: {e}")

        return None

    def enhance_rhyme_detection(
        self,
        words: List[str],
        phoneme_detector,
        existing_clusters: List[List[str]]
    ) -> List[List[str]]:
        """
        Use LLM to enhance rhyme detection by handling edge cases.

        This is the main integration point that combines phoneme detection
        with LLM assistance for difficult cases.

        Args:
            words: All words in the lyrics
            phoneme_detector: The phoneme detector instance
            existing_clusters: Clusters found by phoneme detection

        Returns:
            Enhanced cluster list with LLM-classified OOV words
        """
        if not self.llm_enabled:
            return existing_clusters

        # Find words that didn't get clustered (OOV words)
        clustered_words = set()
        for cluster in existing_clusters:
            clustered_words.update(cluster)

        oov_words = [w for w in words if w.lower() not in clustered_words]

        if not oov_words:
            return existing_clusters

        # Build existing classes dict
        existing_classes = {
            f"class_{i}": cluster
            for i, cluster in enumerate(existing_clusters)
        }

        # Classify OOV words
        classifications = self.classify_oov_words(oov_words, existing_classes)

        # Merge classifications into clusters
        enhanced_clusters = [list(cluster) for cluster in existing_clusters]

        for word, class_id in classifications.items():
            # Find the cluster index
            class_idx = int(class_id.replace("class_", ""))
            if 0 <= class_idx < len(enhanced_clusters):
                enhanced_clusters[class_idx].append(word)

        return enhanced_clusters

    def analyze_verse_with_llm(self, verse: str) -> Dict:
        """
        Use LLM to perform comprehensive rhyme analysis on a verse.

        This can identify:
        - End rhymes
        - Internal rhymes
        - Assonance and consonance
        - Flow patterns

        Args:
            verse: The verse text to analyze

        Returns:
            Dict with analysis results
        """
        if not self.llm_enabled:
            return {}

        prompt = f"""You are a hip-hop lyrics analyst. Analyze this verse for rhyme patterns.

Verse:
{verse}

Identify:
1. End rhymes (words at end of lines that rhyme)
2. Internal rhymes (rhymes within lines)
3. Multisyllable rhymes (2+ syllable patterns that repeat)
4. Assonance (similar vowel sounds)

Respond in JSON format:
{{
  "end_rhymes": [["word1", "word2"], ...],
  "internal_rhymes": [["word1", "word2"], ...],
  "multisyllable": [["phrase1", "phrase2"], ...],
  "notes": "any observations about flow, scheme, etc."
}}"""

        try:
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2048,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            response_text = message.content[0].text

            # Extract JSON
            import json
            import re

            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
                return analysis

        except Exception as e:
            print(f"LLM verse analysis failed: {e}")

        return {}
