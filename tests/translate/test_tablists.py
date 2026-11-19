from kondor.translate import languagelists
from kondor.translate.tablists import TabTranslationLists


def lists_for(language: str, is_private: bool) -> TabTranslationLists:
    lists = TabTranslationLists(is_private)
    lists.set_language(language)
    lists.set_host("kde.org")
    return lists


def test_a_normal_tab_writes_the_lists(qapp: object) -> None:
    lists = lists_for("xx", False)
    lists.setNever(True)
    assert lists.is_blocked()
    lists.setNever(False)
    assert not lists.is_blocked()


def test_a_private_tab_never_writes_the_lists(qapp: object) -> None:
    lists = lists_for("xx", True)
    lists.setAlways(True)
    lists.setNever(True)
    lists.setNeverHost(True)
    assert languagelists.stored(languagelists.ALWAYS) == []
    assert languagelists.stored(languagelists.NEVER) == []
    assert languagelists.stored(languagelists.NEVER_HOSTS) == []
    assert not lists.canChange


def test_a_blocked_host_blocks_the_page(qapp: object) -> None:
    lists = lists_for("xx", False)
    lists.setNeverHost(True)
    assert lists.is_blocked()
    lists.setNeverHost(False)
