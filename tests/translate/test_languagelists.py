from kondor.core.settings.settings import Settings
from kondor.translate import languagelists


def test_always_removes_the_language_from_never(qapp: object) -> None:
    languagelists.set_never("xx", True)
    languagelists.set_always("xx", True)
    assert languagelists.is_listed(languagelists.ALWAYS, "xx")
    assert not languagelists.is_listed(languagelists.NEVER, "xx")
    languagelists.set_always("xx", False)


def test_never_removes_the_language_from_always(qapp: object) -> None:
    languagelists.set_always("xx", True)
    languagelists.set_never("xx", True)
    assert languagelists.is_listed(languagelists.NEVER, "xx")
    assert not languagelists.is_listed(languagelists.ALWAYS, "xx")
    languagelists.set_never("xx", False)


def test_a_host_is_listed_once(qapp: object) -> None:
    languagelists.set_listed(languagelists.NEVER_HOSTS, "kde.org", True)
    languagelists.set_listed(languagelists.NEVER_HOSTS, "kde.org", True)
    assert languagelists.stored(languagelists.NEVER_HOSTS).count("kde.org") == 1
    languagelists.set_listed(languagelists.NEVER_HOSTS, "kde.org", False)


def test_the_default_target_is_the_ui_language(qapp: object) -> None:
    assert str(Settings.instance().property("translateTo")).isalpha()
