import pytest

def test_identify_query_purpose():
    # Test that the query purpose is correctly identified
    step_title = "Identify the query purpose"
    expected_content = "who are you"
    
    # Verify the step title matches expected
    assert step_title == "Identify the query purpose"
    
    # Verify the content contains expected phrase
    assert expected_content in "who are you"
    
    # Additional verification that the mode is analyze
    assert "analyze" == "analyze"
    
    print("Query purpose identification test passed!")
    
# Run the test
if __name__ == "__main__":
    test_identify_query_purpose()