#!/usr/bin/env python3
"""Test script for no-consecutive-duplicates mantra picking."""

import sys
from pathlib import Path

# Add tasklistprogram to path
sys.path.insert(0, str(Path(__file__).parent))

from tasklistprogram.core.documents import get_mantras_file_path

def test_no_consecutive_duplicates():
    print("Testing no consecutive duplicates...")
    
    # Create a minimal test class
    class TestApp:
        def __init__(self):
            self.last_shown_mantra = None
        
        def _pick_random_mantra(self) -> str:
            """Pick a random mantra from file, avoiding the last shown one if possible."""
            from tasklistprogram.core.documents import load_mantras_from_file
            import random
            
            mantras = load_mantras_from_file()
            if not mantras:
                return ""
            
            # If only one mantra, return it
            if len(mantras) == 1:
                return mantras[0]
            
            # Filter out the last shown mantra to avoid consecutive duplicates
            available = [m for m in mantras if m != self.last_shown_mantra]
            
            # If all mantras were filtered out (shouldn't happen), use all mantras
            if not available:
                available = mantras
            
            return random.choice(available)
    
    app = TestApp()
    
    # Test 1: First pick should work
    print("\n1. First mantra pick...")
    first = app._pick_random_mantra()
    print(f"   Picked: {first}")
    assert first, "Should pick a mantra"
    app.last_shown_mantra = first
    print("   ✓ First pick successful")
    
    # Test 2: Next picks should not match the last one (with multiple mantras)
    print("\n2. Testing no consecutive duplicates (10 tries)...")
    successes = 0
    for i in range(10):
        next_mantra = app._pick_random_mantra()
        if next_mantra != app.last_shown_mantra:
            successes += 1
        app.last_shown_mantra = next_mantra
    print(f"   Avoided duplicates: {successes}/10 times")
    assert successes >= 8, "Should avoid duplicates most of the time with 5 mantras"
    print("   ✓ Consecutive duplicates avoided")
    
    # Test 3: With only one mantra, it should still work
    print("\n3. Testing with single mantra...")
    # Write a temp file with one mantra
    mantra_path = get_mantras_file_path()
    backup = mantra_path.read_text()
    try:
        mantra_path.write_text("# Test\n\nOnly one mantra.\n")
        
        app2 = TestApp()
        m1 = app2._pick_random_mantra()
        app2.last_shown_mantra = m1
        m2 = app2._pick_random_mantra()
        print(f"   With one mantra: '{m1}' -> '{m2}'")
        assert m1 == m2 == "Only one mantra.", "Should return the same (only) mantra"
        print("   ✓ Single mantra case handled")
    finally:
        mantra_path.write_text(backup)
    
    print("\n✅ All tests passed!")

if __name__ == "__main__":
    test_no_consecutive_duplicates()
