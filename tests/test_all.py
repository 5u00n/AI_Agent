# tests/test_all.py
# Acts as a master test runner to execute the entire suite programmatically.

import pytest
import sys

def test_suite_discovery_gate():
    # Simple check to confirm suite is discoverable
    assert True

if __name__ == "__main__":
    sys.exit(pytest.main())
