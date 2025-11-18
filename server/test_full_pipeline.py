"""
Test script for full pipeline integration (All Phases).

Tests the complete rhyme detection system with:
- Phase 1: English phoneme detection
- Phase 2: Multilingual (Hindi/Hinglish)
- Phase 3: Multisyllable patterns
- Phase 4: Caching + LLM enhancement
"""

import sys
from song import Song


def test_phase1_english():
    """Test Phase 1: Basic English rhyme detection."""
    print("\n" + "=" * 60)
    print("TEST 1: Phase 1 - English Rhyme Detection")
    print("=" * 60)

    lyrics = "cat hat bat dog log fog car star bar"
    song = Song(lyrics, use_cache=False)
    clusters = song.find_all_rhyme_clusters()

    print(f"Lyrics: {lyrics}")
    print(f"\nFound {len(clusters)} clusters:")
    for i, cluster in enumerate(clusters, 1):
        print(f"  Cluster {i}: {cluster}")

    assert len(clusters) >= 2, "Should find at least 2 clusters"
    print("✓ Phase 1 test passed!")


def test_phase2_multilingual():
    """Test Phase 2: Multilingual (Hinglish) rhyme detection."""
    print("\n" + "=" * 60)
    print("TEST 2: Phase 2 - Multilingual Rhyme Detection")
    print("=" * 60)

    # Mixed English and Hinglish
    lyrics = "bhai yaar tera mera cat hat flow show"
    song = Song(lyrics, use_multilingual=True, use_cache=False)
    clusters = song.find_all_rhyme_clusters()

    print(f"Lyrics: {lyrics}")
    print(f"\nFound {len(clusters)} clusters:")
    for i, cluster in enumerate(clusters, 1):
        print(f"  Cluster {i}: {cluster}")

    assert len(clusters) >= 2, "Should find at least 2 clusters"
    print("✓ Phase 2 test passed!")


def test_phase3_multisyllable():
    """Test Phase 3: Multisyllable pattern detection."""
    print("\n" + "=" * 60)
    print("TEST 3: Phase 3 - Multisyllable Pattern Detection")
    print("=" * 60)

    lyrics = "Mary Mack scary black attack track back pack"
    song = Song(lyrics, use_advanced=True, use_cache=False)
    clusters = song.find_all_rhyme_clusters()

    print(f"Lyrics: {lyrics}")
    print(f"\nFound {len(clusters)} clusters:")
    for i, cluster in enumerate(clusters, 1):
        print(f"  Cluster {i}: {cluster}")

    assert len(clusters) >= 1, "Should find at least 1 cluster"
    print("✓ Phase 3 test passed!")


def test_phase4_caching():
    """Test Phase 4: Caching functionality."""
    print("\n" + "=" * 60)
    print("TEST 4: Phase 4 - Caching")
    print("=" * 60)

    lyrics = "cat hat bat dog log"

    # First call - should compute
    print("First call (computing)...")
    song1 = Song(lyrics, use_cache=True)
    clusters1 = song1.find_all_rhyme_clusters()

    # Second call - should retrieve from cache
    print("Second call (from cache)...")
    song2 = Song(lyrics, use_cache=True)
    clusters2 = song2.find_all_rhyme_clusters()

    # Results should be identical
    assert clusters1 == clusters2, "Cached results should match"
    print(f"Clusters: {clusters1}")
    print("✓ Phase 4 caching test passed!")


def test_full_pipeline_without_llm():
    """Test the full pipeline without LLM (all other phases)."""
    print("\n" + "=" * 60)
    print("TEST 5: Full Pipeline (Phases 1-3 + Caching)")
    print("=" * 60)

    # Complex lyrics with mixed features
    lyrics = """
    bhai yaar tera flow show
    Mary Mack scary black attack track
    cat hat bat dog log fog
    """

    song = Song(
        lyrics,
        use_advanced=True,
        use_multilingual=True,
        use_cache=True,
        use_llm=False
    )

    clusters = song.find_all_rhyme_clusters()

    print(f"Input lyrics (trimmed):")
    print(lyrics.strip())
    print(f"\nFound {len(clusters)} clusters:")
    for i, cluster in enumerate(clusters, 1):
        if len(cluster) > 1:  # Only show clusters with 2+ words
            print(f"  Cluster {i}: {cluster}")

    assert len(clusters) >= 3, "Should find multiple clusters"
    print("✓ Full pipeline test passed!")


def test_real_world_lyrics():
    """Test with realistic rap lyrics."""
    print("\n" + "=" * 60)
    print("TEST 6: Real-World Rap Lyrics")
    print("=" * 60)

    # Simulated rap verse
    lyrics = """
    I got the flow so sick everybody knows
    When I hit the stage they go crazy in the rows
    From the bottom to the top never gonna stop
    Making hits that pop like a soda that dropped
    """

    song = Song(
        lyrics,
        use_advanced=True,
        use_multilingual=False,
        use_cache=True,
        use_llm=False
    )

    clusters = song.find_all_rhyme_clusters()

    print("Rap verse:")
    print(lyrics.strip())
    print(f"\nFound {len(clusters)} rhyme clusters:")
    for i, cluster in enumerate(clusters, 1):
        if len(cluster) >= 2:  # Only show actual rhyme groups
            print(f"  Cluster {i}: {cluster}")

    print("✓ Real-world lyrics test passed!")


def test_devanagari_lyrics():
    """Test with actual Devanagari (Hindi) lyrics."""
    print("\n" + "=" * 60)
    print("TEST 7: Devanagari (Hindi) Lyrics")
    print("=" * 60)

    # Hindi words
    lyrics = "भाई यार काला गला दिल मिल"
    song = Song(lyrics, use_multilingual=True, use_cache=False)
    clusters = song.find_all_rhyme_clusters()

    print(f"Hindi lyrics: {lyrics}")
    print(f"\nFound {len(clusters)} clusters:")
    for i, cluster in enumerate(clusters, 1):
        print(f"  Cluster {i}: {cluster}")

    print("✓ Devanagari test passed!")


def test_llm_stub():
    """Test LLM integration (without actual API call)."""
    print("\n" + "=" * 60)
    print("TEST 8: LLM Integration (Stub Test)")
    print("=" * 60)

    lyrics = "cat hat xyzabc"  # xyzabc is OOV word

    # LLM won't actually be called without API key
    song = Song(
        lyrics,
        use_llm=True,
        use_cache=False,
        llm_api_key=None  # No key = LLM disabled
    )

    clusters = song.find_all_rhyme_clusters()

    print(f"Lyrics (with OOV word): {lyrics}")
    print(f"Found {len(clusters)} clusters: {clusters}")
    print("Note: LLM not enabled (no API key), using phoneme detection only")
    print("✓ LLM stub test passed!")


def test_performance():
    """Test performance with larger lyrics."""
    print("\n" + "=" * 60)
    print("TEST 9: Performance Test")
    print("=" * 60)

    import time

    # Generate longer lyrics
    lyrics = " ".join(["cat hat bat dog log fog car star bar"] * 10)

    start = time.time()
    song = Song(lyrics, use_cache=False)
    clusters = song.find_all_rhyme_clusters()
    duration = time.time() - start

    print(f"Processed {len(lyrics.split())} words in {duration:.3f} seconds")
    print(f"Found {len(clusters)} clusters")
    print(f"Average: {duration / len(lyrics.split()) * 1000:.2f} ms per word")

    assert duration < 5.0, "Should process within reasonable time"
    print("✓ Performance test passed!")


def run_all_tests():
    """Run all integration tests."""
    print("=" * 60)
    print("FULL PIPELINE INTEGRATION TESTS")
    print("All Phases: 1 (English) + 2 (Multilingual) + 3 (Multisyllable) + 4 (Cache/LLM)")
    print("=" * 60)

    tests = [
        ("Phase 1 - English", test_phase1_english),
        ("Phase 2 - Multilingual", test_phase2_multilingual),
        ("Phase 3 - Multisyllable", test_phase3_multisyllable),
        ("Phase 4 - Caching", test_phase4_caching),
        ("Full Pipeline", test_full_pipeline_without_llm),
        ("Real-World Lyrics", test_real_world_lyrics),
        ("Devanagari", test_devanagari_lyrics),
        ("LLM Stub", test_llm_stub),
        ("Performance", test_performance),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"\n✗ Test '{test_name}' FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Total tests: {len(tests)}")
    print(f"✓ Passed: {passed}")
    if failed > 0:
        print(f"✗ Failed: {failed}")
    else:
        print("ALL TESTS PASSED! 🎉")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
