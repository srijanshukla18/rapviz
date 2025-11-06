"""
Test script for phoneme-based rhyme detection.
"""

import sys
from phoneme_rhyme import PhonemeRhymeDetector, MultisyllableRhymeDetector

def test_basic_rhymes():
    """Test basic rhyme detection."""
    detector = PhonemeRhymeDetector()

    # Test some simple rhymes
    test_pairs = [
        ("cat", "hat", True),
        ("dog", "log", True),
        ("car", "star", True),
        ("love", "dove", True),
        ("cat", "dog", False),
        ("tree", "car", False),
    ]

    print("Testing basic rhyme pairs:")
    for word1, word2, expected in test_pairs:
        result = detector.words_rhyme(word1, word2)
        status = "✓" if result == expected else "✗"
        print(f"  {status} '{word1}' vs '{word2}': {result} (expected: {expected})")

def test_rhyme_clusters():
    """Test rhyme clustering."""
    detector = PhonemeRhymeDetector()

    # Test with some rap lyrics
    lyrics = "cat hat bat dog log fog car star bar"
    words = lyrics.split()

    print("\nTesting rhyme clusters:")
    print(f"Input words: {words}")

    clusters = detector.find_rhyme_clusters(words)
    print(f"\nFound {len(clusters)} rhyme clusters:")
    for i, cluster in enumerate(clusters, 1):
        print(f"  Cluster {i}: {cluster}")

def test_multisyllable():
    """Test multisyllable rhymes."""
    detector = PhonemeRhymeDetector()

    # Test words that rhyme on multiple syllables
    lyrics = "scar car scary Mary Mack black track attack"
    words = lyrics.split()

    print("\nTesting multisyllable rhyme detection:")
    print(f"Input words: {words}")

    clusters = detector.find_rhyme_clusters(words)
    print(f"\nFound {len(clusters)} rhyme clusters:")
    for i, cluster in enumerate(clusters, 1):
        print(f"  Cluster {i}: {cluster}")

def test_phoneme_extraction():
    """Test phoneme extraction."""
    detector = PhonemeRhymeDetector()

    test_words = ["cat", "hat", "scar", "car", "love", "dove"]

    print("\nTesting phoneme extraction:")
    for word in test_words:
        phonemes = detector.get_phonemes(word)
        if phonemes:
            tail = detector.extract_rhyme_tail(phonemes)
            norm_tail = detector.normalize_phoneme_tail(tail) if tail else None
            rhyme_id = detector.hash_tail(norm_tail) if norm_tail else None
            print(f"  '{word}': {phonemes} → tail: {tail} → normalized: {norm_tail} → ID: {rhyme_id}")
        else:
            print(f"  '{word}': No phonemes found")

def test_phase3_multisyllable():
    """Test Phase 3 multisyllable pattern detection."""
    detector = MultisyllableRhymeDetector()

    # Test with rap lyrics that have multisyllable patterns
    lyrics = "Mary Mack scary black attack track back pack"
    words = lyrics.split()

    print("\nTesting Phase 3 multisyllable pattern detection:")
    print(f"Input words: {words}")

    # Test syllable splitting
    print("\nSyllable splitting:")
    for word in words[:3]:  # Just show first 3
        phonemes = detector.get_phonemes(word)
        if phonemes:
            syllables = detector.split_into_syllables(phonemes)
            print(f"  '{word}': {phonemes} → syllables: {syllables}")

    # Test multisyllable pattern finding
    patterns = detector.find_multisyllable_patterns(words)
    print(f"\nFound {len(patterns)} repeated multisyllable patterns:")
    for pattern_id, occurrences in patterns.items():
        print(f"  Pattern {pattern_id}:")
        for occ in occurrences:
            involved_words = [words[i] for i in occ['words']]
            print(f"    - {involved_words} (pattern: {occ['pattern'][:5]}...)")

    # Test cluster with spans
    clusters_with_spans = detector.find_rhyme_clusters_with_spans(words)
    print(f"\nClusters with span information: {len(clusters_with_spans)} total")
    for cluster in clusters_with_spans[:3]:  # Show first 3
        is_multi = cluster.get('is_multisyllable', False)
        cluster_type = "multisyllable" if is_multi else "regular"
        print(f"  {cluster['cluster_id']} ({cluster_type}):")
        for word_info in cluster['words'][:3]:  # Show first 3 words
            print(f"    - '{word_info['word']}' at index {word_info['index']}")

if __name__ == "__main__":
    print("=" * 60)
    print("PHONEME-BASED RHYME DETECTION TEST")
    print("=" * 60)

    try:
        test_phoneme_extraction()
        test_basic_rhymes()
        test_rhyme_clusters()
        test_multisyllable()
        test_phase3_multisyllable()

        print("\n" + "=" * 60)
        print("All tests completed!")
        print("=" * 60)

    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
