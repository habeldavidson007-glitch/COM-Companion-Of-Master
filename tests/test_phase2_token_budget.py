import importlib.util
import sys
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "core" / "context_compressor.py"
spec = importlib.util.spec_from_file_location("context_compressor", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
assert spec.loader is not None
spec.loader.exec_module(mod)
ContextCompressor = mod.ContextCompressor


def test_compress_many_with_budget_enforces_total_limit():
    c = ContextCompressor(max_tokens=256)
    texts = ["alpha " * 800, "beta " * 700, "gamma " * 600]
    out = c.compress_many_with_budget(texts, max_total_tokens=300, per_item_floor=48)
    total = sum(c.count_tokens(x) for x in out)
    assert total <= 300


def test_compress_many_with_budget_is_deterministic():
    c = ContextCompressor(max_tokens=256)
    texts = ["player physics collision " * 300, "config gravity floor " * 200]
    out1 = c.compress_many_with_budget(texts, max_total_tokens=220, per_item_floor=40)
    out2 = c.compress_many_with_budget(texts, max_total_tokens=220, per_item_floor=40)
    assert out1 == out2


def test_compress_many_with_budget_stats_fields():
    c = ContextCompressor(max_tokens=256)
    texts = ["alpha " * 300, "beta " * 250]
    out, stats = c.compress_many_with_budget_stats(texts, max_total_tokens=180, per_item_floor=32)
    assert isinstance(out, list)
    assert set(stats.keys()) == {
        "input_tokens_total",
        "output_tokens_total",
        "compression_ratio",
        "budget_enforced",
    }
    assert stats["output_tokens_total"] <= 180
    assert stats["budget_enforced"] is True
