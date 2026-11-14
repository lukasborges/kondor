from kondor.passwords.csvimport.importtypes import Login
from kondor.passwords.csvimport.passwordimportplan import merge_logins, summarize_import

SITE = "https://example.com"
TWO_CONFLICTS = 2


def test_counts_new_identical_and_conflicting_logins() -> None:
    saved = {SITE: {"same": "pw", "other": "old"}}
    logins = [Login(SITE, "fresh", "pw"), Login(SITE, "same", "pw"), Login(SITE, "other", "new")]
    summary = summarize_import(logins, saved)
    assert summary.new_count == 1
    assert summary.identical_count == 1
    assert summary.conflict_count == 1


def test_counts_each_conflicting_site_once() -> None:
    saved = {SITE: {"a": "old", "b": "old"}}
    summary = summarize_import([Login(SITE, "a", "new"), Login(SITE, "b", "new")], saved)
    assert summary.conflict_count == TWO_CONFLICTS
    assert summary.conflict_sites == 1


def test_merge_keeps_conflicts_unless_replacing() -> None:
    saved = {"a": "old"}
    logins = [Login(SITE, "a", "new"), Login(SITE, "b", "pw")]
    assert merge_logins(saved, logins, False) == 1
    assert saved["a"] == "old"
    assert merge_logins(saved, logins, True) == 1
    assert saved["a"] == "new"


def test_merge_leaves_identical_logins_unchanged() -> None:
    saved = {"a": "pw"}
    assert merge_logins(saved, [Login(SITE, "a", "pw")], True) == 0
    assert len(saved) == 1
