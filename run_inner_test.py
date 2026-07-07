import pytest
from pathlib import Path
from agent import AgentConfig, AgentEngine, PlannerExecutorVerifier
import tempfile
import sys

def test():
    with tempfile.TemporaryDirectory() as d:
        tmp_path = Path(d)
        cfg = AgentConfig.default(root_dir=tmp_path)
        engine = AgentEngine(cfg, root_dir=tmp_path)
        loop = PlannerExecutorVerifier(engine)
        
        result = loop.run("Create hello.txt")
        print("RESULT:", result)
        if result["status"] != "done":
            print(result.get("report"))

if __name__ == "__main__":
    test()
