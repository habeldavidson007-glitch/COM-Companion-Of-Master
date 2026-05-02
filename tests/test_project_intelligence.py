import importlib.util
import sys
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "core" / "project_intelligence.py"
spec = importlib.util.spec_from_file_location("project_intelligence", MODULE_PATH)
project_intelligence = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = project_intelligence
assert spec.loader is not None
spec.loader.exec_module(project_intelligence)
ProjectIntelligence = project_intelligence.ProjectIntelligence


def test_index_and_relevance_prioritization(tmp_path: Path):
    (tmp_path / "main.tscn").write_text("[node name=\"Player\"]\n", encoding="utf-8")
    (tmp_path / "player.gd").write_text(
        "class_name Player\nfunc move_and_slide():\n    pass\n", encoding="utf-8"
    )
    (tmp_path / "config.toml").write_text("[physics]\ngrav=9.8\n", encoding="utf-8")
    (tmp_path / "big_module.py").write_text("\n".join(["x = 1"] * 2000), encoding="utf-8")

    pil = ProjectIntelligence(str(tmp_path))
    count = pil.index_project()

    assert count == 4

    results = pil.query_relevant_files("why player falls through floor physics", limit=3)
    assert len(results) > 0
    paths = [r.path for r in results]
    assert "player.gd" in paths
    assert "main.tscn" in paths
    assert paths[0] != "big_module.py"


def test_index_is_rebuilt_not_reparsed_on_query(tmp_path: Path):
    (tmp_path / "a.py").write_text("def alpha():\n    return 1\n", encoding="utf-8")

    pil = ProjectIntelligence(str(tmp_path))
    pil.index_project()
    first = dict(pil.file_index)

    pil.query_relevant_files("alpha function")
    second = dict(pil.file_index)

    assert first.keys() == second.keys()
    assert first["a.py"].lines == second["a.py"].lines
