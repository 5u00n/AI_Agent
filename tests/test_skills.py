from pathlib import Path

def test_skills_listing(tmp_path: Path) -> None:
    skills_dir = tmp_path / ".agents" / "skills" / "translator"
    skills_dir.mkdir(parents=True, exist_ok=True)
    skill_md = """---
name: Spanish Translator
description: Expert Spanish translator
---
# Instructions
Always translate inputs to Spanish.
"""
    (skills_dir / "SKILL.md").write_text(skill_md, encoding="utf-8")

    skills = []
    skills_root = tmp_path / ".agents" / "skills"
    if skills_root.exists():
        for p in skills_root.iterdir():
            if p.is_dir() and (p / "SKILL.md").exists():
                content = (p / "SKILL.md").read_text(encoding="utf-8")
                name = p.name
                desc = ""
                for line in content.splitlines():
                    if line.strip().startswith("name:"):
                        name = line.split(":", 1)[1].strip().strip('"').strip("'")
                    elif line.strip().startswith("description:"):
                        desc = line.split(":", 1)[1].strip().strip('"').strip("'")
                skills.append({"name": name, "description": desc, "folder": p.name})

    assert len(skills) == 1
    assert skills[0]["name"] == "Spanish Translator"
    assert skills[0]["description"] == "Expert Spanish translator"
    assert skills[0]["folder"] == "translator"
