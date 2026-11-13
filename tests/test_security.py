from contextlib import contextmanager
from pathlib import Path

import pytest

from php_legacy_auditor.security import validate_safe_path


def test_validate_safe_path_ok():
    root = Path("/tmp/php_legacy_auditor_allowed_tests")
    root.mkdir(parents=True, exist_ok=True)
    try:
        with _temp_env(root):
            validated = validate_safe_path(str(root / "sub" / "file.txt"))
        assert validated.parent == root / "sub"
    finally:
        import shutil

        shutil.rmtree(root, ignore_errors=True)


def test_validate_safe_path_blocks_traversal():
    with pytest.raises(ValueError):
        validate_safe_path("../../etc/passwd")


def test_validate_safe_path_blocks_escape_from_root():
    root = Path("/tmp/php_legacy_auditor_escape_tests")
    root.mkdir(parents=True, exist_ok=True)
    try:
        with _temp_env(root):
            try:
                validate_safe_path("../outside.txt")
                assert False, "expected ValueError for traversal"
            except ValueError:
                pass
    finally:
        import shutil

        shutil.rmtree(root, ignore_errors=True)


def test_validate_safe_path_requires_extension_for_existing_file():
    root = Path("/tmp/php_legacy_auditor_ext_tests")
    root.mkdir(parents=True, exist_ok=True)
    try:
        with _temp_env(root):
            file_path = root / "app.txt"
            file_path.write_text("hello", encoding="utf-8")
            with pytest.raises(ValueError):
                validate_safe_path(str(file_path), required_extension=".php")
    finally:
        import shutil

        shutil.rmtree(root, ignore_errors=True)


@contextmanager
def _temp_env(root: Path):
    import os

    old = os.environ.get("ALLOWED_AUDIT_ROOT")
    os.environ["ALLOWED_AUDIT_ROOT"] = str(root)
    try:
        yield
    finally:
        if old is None:
            os.environ.pop("ALLOWED_AUDIT_ROOT", None)
        else:
            os.environ["ALLOWED_AUDIT_ROOT"] = old
