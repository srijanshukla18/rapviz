"""
Test script for multilingual rhyme detection (Phase 2).
"""

import sys
from phoneme_rhyme import MultilingualPhonemeDetector


def test_script_detection():
    """Test script detection."""
    from multilingual_phoneme import ScriptDetector

    detector = ScriptDetector()

    test_cases = [
        ("hello", "ascii"),
        ("भाई", "devanagari"),
        ("bhai", "ascii"),
        ("tera", "ascii"),
        ("तेरा", "devanagari"),
    ]

    print("Testing script detection:")
    for word, expected_script in test_cases:
        detected = detector.detect_script(word)
        status = "✓" if detected == expected_script else "✗"
        print(f"  {status} '{word}': {detected} (expected: {expected_script})")


def test_hinglish_detection():
    """Test Hinglish word detection."""
    from multilingual_phoneme import HinglishTransliterator

    translit = HinglishTransliterator()

    test_words = ["bhai", "yaar", "tera", "hello", "cat", "kala", "flow"]

    print("\nTesting Hinglish detection:")
    for word in test_words:
        is_hinglish = translit.looks_like_hinglish(word)
        print(f"  '{word}': {'Hinglish' if is_hinglish else 'Not Hinglish'}")


def test_transliteration():
    """Test Hinglish → Devanagari transliteration."""
    from multilingual_phoneme import HinglishTransliterator

    translit = HinglishTransliterator()

    test_words = ["bhai", "yaar", "tera", "kala", "dil"]

    print("\nTesting transliteration:")
    for word in test_words:
        devanagari = translit.transliterate_to_devanagari(word)
        print(f"  '{word}' → '{devanagari}'")


def test_hindi_phonemization():
    """Test Devanagari → phoneme conversion."""
    from multilingual_phoneme import HindiPhonemeMapper

    mapper = HindiPhonemeMapper()

    test_words = [
        ("भाई", "bhai"),
        ("यार", "yaar"),
        ("काला", "kala"),
        ("दिल", "dil"),
    ]

    print("\nTesting Hindi phonemization:")
    for devanagari, romanized in test_words:
        phonemes = mapper.devanagari_to_phonemes(devanagari)
        print(f"  '{devanagari}' ({romanized}): {phonemes}")


def test_unified_phoneme_mapping():
    """Test ARPABET → IPA unified mapping."""
    from multilingual_phoneme import UnifiedPhonemeMapper

    mapper = UnifiedPhonemeMapper()

    # Test English word "cat" phonemes
    arpabet = ['K', 'AE1', 'T']
    unified = mapper.arpabet_to_unified(arpabet)

    print("\nTesting unified phoneme mapping:")
    print(f"  ARPABET: {arpabet}")
    print(f"  Unified: {unified}")

    # Test normalization
    normalized = mapper.normalize_for_comparison(unified)
    print(f"  Normalized: {normalized}")


def test_multilingual_rhyme_detection():
    """Test end-to-end multilingual rhyme detection."""
    detector = MultilingualPhonemeDetector()

    # Test with mixed English and Hinglish
    lyrics = "bhai yaar tera mera cat hat"
    words = lyrics.split()

    print("\nTesting multilingual rhyme detection:")
    print(f"Input words: {words}")

    # Show phonemes for each word
    print("\nPhonemes per word:")
    for word in words:
        phonemes = detector.get_phonemes(word)
        if phonemes:
            tail = detector.extract_rhyme_tail(phonemes)
            norm_tail = detector.normalize_phoneme_tail(tail) if tail else None
            print(f"  '{word}': {phonemes[:3]}... → tail: {tail}")
        else:
            print(f"  '{word}': No phonemes found")

    # Find rhyme clusters
    clusters = detector.find_rhyme_clusters(words)
    print(f"\nFound {len(clusters)} rhyme clusters:")
    for i, cluster in enumerate(clusters, 1):
        print(f"  Cluster {i}: {cluster}")


def test_devanagari_rhymes():
    """Test rhymes with actual Devanagari text."""
    detector = MultilingualPhonemeDetector()

    # Test with Devanagari words
    lyrics = "भाई यार काला गला"  # bhai yaar kala galla
    words = lyrics.split()

    print("\nTesting Devanagari rhyme detection:")
    print(f"Input words: {words}")

    clusters = detector.find_rhyme_clusters(words)
    print(f"\nFound {len(clusters)} rhyme clusters:")
    for i, cluster in enumerate(clusters, 1):
        print(f"  Cluster {i}: {cluster}")


def test_code_switched_lyrics():
    """Test with code-switched (English + Hinglish) lyrics."""
    detector = MultilingualPhonemeDetector()

    # Mix of English and Hinglish
    lyrics = "bhai flow show yaar car star"
    words = lyrics.split()

    print("\nTesting code-switched lyrics:")
    print(f"Input words: {words}")

    clusters = detector.find_rhyme_clusters(words)
    print(f"\nFound {len(clusters)} rhyme clusters:")
    for i, cluster in enumerate(clusters, 1):
        print(f"  Cluster {i}: {cluster}")


if __name__ == "__main__":
    print("=" * 60)
    print("MULTILINGUAL RHYME DETECTION TEST (PHASE 2)")
    print("=" * 60)

    try:
        test_script_detection()
        test_hinglish_detection()
        test_transliteration()
        test_hindi_phonemization()
        test_unified_phoneme_mapping()
        test_multilingual_rhyme_detection()
        test_devanagari_rhymes()
        test_code_switched_lyrics()

        print("\n" + "=" * 60)
        print("All Phase 2 tests completed!")
        print("=" * 60)

    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
