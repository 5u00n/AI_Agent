import pytest

class TestDetermineResponseType:
    def test_response_type_contains_assistant(self, step_result):
        assert 'assistant' in step_result.lower()
    
    def test_response_type_contains_ai(self, step_result):
        assert 'ai' in step_result.lower() or 'artificial intelligence' in step_result.lower()
    
    def test_response_type_contains_language_model(self, step_result):
        assert 'language model' in step_result.lower()
    
    def test_response_type_classification(self, step_result):
        # Check that the response is classified as an AI assistant response
        assert any(keyword in step_result.lower() for keyword in ['assistant', 'ai', 'language model'])
        
    def test_complete_content_expectations(self, step_result):
        # Verify all expected content is present
        expectations = ['assistant', 'ai', 'language model']
        for expectation in expectations:
            assert expectation in step_result.lower(), f"Missing '{expectation}' in response"
