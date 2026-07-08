import pytest
from pathlib import Path
import shutil

# Tell pytest to ignore the out/ directory during test discovery
collect_ignore = ["out"]

@pytest.fixture(autouse=True)
def tmp_path(request):
    # Create a path under tests/out based on the test name
    test_name = request.node.name
    # Clean special characters to make a safe directory name
    safe_name = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in test_name)
    out_dir = Path(__file__).parent / "out" / safe_name
    
    # Clean up prior test runs if exists
    if out_dir.exists():
        try:
            shutil.rmtree(out_dir)
        except Exception:
            pass
    out_dir.mkdir(parents=True, exist_ok=True)
    
    return out_dir
