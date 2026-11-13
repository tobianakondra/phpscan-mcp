import pytest

from php_legacy_auditor.mappers import map_project_structure, read_code_context


def test_read_code_context_returns_numbers_and_truncation(tmp_path):
    (tmp_path / "app.php").write_text(
        "<?php\n" + "\n".join(f"line {i};" for i in range(1, 30)) + "\n", encoding="utf-8"
    )
    result = read_code_context(str(tmp_path / "app.php"), 5, 25)
    assert result["visible_start"] == 5
    assert result["visible_end"] == 25
    assert result["truncated"] is False
    assert result["lines"][0]["line"] == 5
    assert result["lines"][-1]["line"] == 25


def test_read_code_context_truncates_when_too_big(tmp_path):
    (tmp_path / "big.php").write_text(
        "<?php\n" + "\n".join(f"line {i};" for i in range(1, 300)) + "\n", encoding="utf-8"
    )
    result = read_code_context(str(tmp_path / "big.php"), 250, 400)
    assert len(result["lines"]) <= 200
    assert result["truncated"] is True


def test_map_project_structure_returns_summary(tmp_path):
    (tmp_path / "index.php").write_text("<?php echo \"hi\";\n", encoding="utf-8")
    lib_dir = tmp_path / "lib"
    lib_dir.mkdir()
    (lib_dir / "util.inc").write_text("<?php\n", encoding="utf-8")
    db_dir = tmp_path / "db"
    db_dir.mkdir()
    (db_dir / "schema.sql").write_text("CREATE TABLE t (id INT);\n", encoding="utf-8")
    result = map_project_structure(str(tmp_path))
    assert result["root"] == str(tmp_path)
    assert result["file_count"] == 3
    assert result["probable_entry_points"]
