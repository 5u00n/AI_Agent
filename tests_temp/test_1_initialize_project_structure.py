import os
import pytest

def test_project_structure_created():
    """Test that the project structure is properly initialized"""
    # Check if the main.py file exists
    assert os.path.exists('src/main.py'), "src/main.py file should exist"
    
    # Check if src directory exists
    assert os.path.exists('src'), "src directory should exist"
    
    # Verify it's actually a file, not a directory
    assert os.path.isfile('src/main.py'), "src/main.py should be a file, not a directory"
    
    # Check that the file is not empty
    with open('src/main.py', 'r') as f:
        content = f.read()
        assert len(content.strip()) > 0, "src/main.py should contain code"

def test_main_file_content():
    """Test that main.py contains expected content"""
    with open('src/main.py', 'r') as f:
        content = f.read()
        # Basic check for Python file structure
        assert 'def main()' in content or 'if __name__' in content, "main.py should contain main function or if __name__ block"
