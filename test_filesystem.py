"""Tests for filesystem utilities."""
import unittest
from pathlib import Path
import tempfile
import shutil
from tasklistprogram.core.filesystem import sanitize_folder_name, create_task_document_folder


class TestFilesystemUtilities(unittest.TestCase):
    """Test filesystem utility functions."""
    
    def setUp(self):
        """Create a temporary directory for testing."""
        self.test_dir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        """Clean up temporary directory."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_sanitize_folder_name_preserves_normal_characters(self):
        """Test that normal characters including 'n' and 't' are preserved."""
        test_cases = [
            ("Supplements", "Supplements"),
            ("Daily Maintenance", "Daily Maintenance"),
            ("Diet Food", "Diet Food"),
            ("Testing Nutrition", "Testing Nutrition"),
            ("Internet Connection", "Internet Connection"),
        ]
        
        for input_name, expected in test_cases:
            with self.subTest(input=input_name):
                result = sanitize_folder_name(input_name)
                self.assertEqual(result, expected, 
                    f"Normal characters should be preserved, got '{result}' for '{input_name}'")
    
    def test_sanitize_folder_name_removes_unsafe_characters(self):
        """Test that filesystem-unsafe characters are replaced."""
        test_cases = [
            ("Test<File>", "Test File"),
            ("Bad:Name", "Bad Name"),
            ("Slash/Name", "Slash Name"),
            ("Back\\Slash", "Back Slash"),
            ("Pipe|Name", "Pipe Name"),
            ("Question?", "Question"),
            ("Asterisk*", "Asterisk"),
            ("Quote\"Name", "Quote Name"),
        ]
        
        for input_name, expected in test_cases:
            with self.subTest(input=input_name):
                result = sanitize_folder_name(input_name)
                self.assertEqual(result, expected)
    
    def test_sanitize_folder_name_handles_empty_strings(self):
        """Test that empty strings are handled properly."""
        self.assertEqual(sanitize_folder_name(""), "Untitled")
        self.assertEqual(sanitize_folder_name("   "), "Untitled")
    
    def test_sanitize_folder_name_handles_dots_and_spaces(self):
        """Test that leading/trailing dots and spaces are removed."""
        test_cases = [
            ("  Spaced  ", "Spaced"),
            ("..Dotted..", "Dotted"),
            (" . Test . ", "Test"),
        ]
        
        for input_name, expected in test_cases:
            with self.subTest(input=input_name):
                result = sanitize_folder_name(input_name)
                self.assertEqual(result, expected)
    
    def test_sanitize_folder_name_collapses_multiple_spaces(self):
        """Test that multiple spaces are collapsed to single spaces."""
        result = sanitize_folder_name("Multiple     Spaces     Here")
        self.assertEqual(result, "Multiple Spaces Here")
    
    def test_sanitize_folder_name_limits_length(self):
        """Test that extremely long names are truncated."""
        long_name = "A" * 200
        result = sanitize_folder_name(long_name)
        self.assertLessEqual(len(result), 100)
    
    def test_create_task_document_folder(self):
        """Test that folders are created with sanitized names."""
        folder_name = "Test Task Folder"
        result_path = create_task_document_folder(self.test_dir, folder_name)
        
        self.assertTrue(result_path.exists())
        self.assertTrue(result_path.is_dir())
        self.assertEqual(result_path.name, "Test Task Folder")
    
    def test_create_task_document_folder_with_unsafe_name(self):
        """Test that folders are created even with unsafe characters in name."""
        folder_name = "Task<with>unsafe:chars"
        result_path = create_task_document_folder(self.test_dir, folder_name)
        
        self.assertTrue(result_path.exists())
        self.assertTrue(result_path.is_dir())
        # Should have removed the unsafe characters
        self.assertNotIn("<", result_path.name)
        self.assertNotIn(">", result_path.name)
        self.assertNotIn(":", result_path.name)
    
    def test_no_n_and_t_replacement_bug(self):
        """
        Critical test: Ensure that 'n' and 't' characters are NOT replaced.
        This was the reported bug that needs to be fixed.
        """
        bug_test_cases = [
            "Supplements",  # Should NOT become "Suppleme_s"
            "Daily Maintenance",  # Should NOT become "Daily Mai_e_a_ce"
            "Diet Food",  # Should NOT become "Die_ Food"
            "Internet",
            "Important Task",
            "Nutrition Plan",
        ]
        
        for name in bug_test_cases:
            with self.subTest(input=name):
                result = sanitize_folder_name(name)
                # Check that 'n' and 't' are preserved
                self.assertNotIn("_", result, 
                    f"Bug detected: underscores found in '{result}' for input '{name}'. "
                    f"The 'n' and 't' characters should be preserved, not replaced.")
                # Ensure the name is basically unchanged (except for trimming)
                self.assertEqual(result.strip(), name.strip(),
                    f"Name should be preserved: expected '{name}', got '{result}'")


if __name__ == '__main__':
    unittest.main()
