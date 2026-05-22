from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_finance_context_exists_and_not_empty():
    file_path = ROOT / "finance_context.md"
    assert file_path.exists()
    assert file_path.read_text(encoding="utf-8").strip()


def test_selected_measures_lookup_exists_and_not_empty():
    file_path = ROOT / "selected_measures_lookup.md"
    assert file_path.exists()
    assert file_path.read_text(encoding="utf-8").strip()