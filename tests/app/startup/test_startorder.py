import pytest

from kondor.app.startup import appstartup


class StubAdBlock:
    @staticmethod
    def instance() -> "StubAdBlock":
        return StubAdBlock()

    def start(self) -> None:
        pass


def test_translators_are_installed_before_singletons_are_registered(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    for name in (
        "discard_position_cache",
        "publish_startup_arguments",
        "register_profiles_with_extensions",
        "load_unpacked_extensions",
    ):
        monkeypatch.setattr(appstartup, name, lambda *_: None)
    monkeypatch.setattr(
        appstartup, "set_up_language_and_style", lambda *_: calls.append("language")
    )
    monkeypatch.setattr(appstartup, "register_all_types", lambda: calls.append("register"))
    monkeypatch.setattr(appstartup, "AdBlockManager", StubAdBlock)
    command_line = type("C", (), {"extension_directories": []})()
    appstartup.start_browser(None, command_line)  # type: ignore[arg-type]
    assert calls == ["language", "register"]
