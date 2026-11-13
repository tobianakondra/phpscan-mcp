from php_legacy_auditor.utils import installed


def test_installed_checks_basic_structure():
    details = installed(("php", "phpcs"))
    assert isinstance(details, dict)
    for name in ("php", "phpcs"):
        assert name in details
        assert "installed" in details[name]
        assert "version" in details[name]
