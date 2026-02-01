#!/usr/bin/env python3
"""Test script for mantras functionality."""

import sys
from pathlib import Path

# Add tasklistprogram to path
sys.path.insert(0, str(Path(__file__).parent))

from tasklistprogram.core.documents import get_mantras_file_path, load_mantras_from_file

def test_mantras():
    print("Testing mantras functionality...")
    
    # Test 1: Get mantra file path (should create file if not exists)
    print("\n1. Getting mantra file path...")
    mantra_path = get_mantras_file_path()
    print(f"   Mantra file path: {mantra_path}")
    print(f"   File exists: {mantra_path.exists()}")
    assert mantra_path.suffix == ".md", "Mantra file should be .md"
    print("   ✓ Mantra file is .md")
    
    # Test 2: Load mantras from file
    print("\n2. Loading mantras from file...")
    mantras = load_mantras_from_file()
    print(f"   Loaded {len(mantras)} mantras:")
    for i, mantra in enumerate(mantras, 1):
        print(f"   {i}. {mantra}")
    assert len(mantras) > 0, "Should have at least one mantra"
    print("   ✓ Mantras loaded successfully")
    
    # Test 3: Verify default mantras are present
    print("\n3. Verifying default mantras...")
    expected = [
        "Protect your sleep.",
        "Keep it simple and start small.",
        "Breathe, then act.",
        "Progress over perfection."
    ]
    for expected_mantra in expected:
        assert expected_mantra in mantras, f"Missing expected mantra: {expected_mantra}"
    print("   ✓ All default mantras found")
    
    # Test 4: Verify comments are ignored
    print("\n4. Verifying comments are ignored...")
    content = mantra_path.read_text(encoding="utf-8")
    assert "# Mantras" in content, "Header should be in file"
    for mantra in mantras:
        assert not mantra.startswith("#"), f"Mantra should not be a comment: {mantra}"
    print("   ✓ Comments properly filtered")
    
    print("\n✅ All tests passed!")

if __name__ == "__main__":
    test_mantras()
