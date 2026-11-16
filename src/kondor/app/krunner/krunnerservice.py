from collections.abc import Callable
from typing import Any, ClassVar

import shiboken6
from PySide6.QtCore import QObject

from kondor.app.instance.singleinstancemessage import SingleInstanceMessage
from kondor.app.instance.windowactivation import raise_window
from kondor.app.krunner.opentabs import open_tabs
from kondor.app.krunner.runnerbus import Reply, RunnerBus
from kondor.app.krunner.runnermatches import RunnerMatch, find_matches
from kondor.app.krunner.runnerreply import match_reply
from kondor.app.windows.windowmanager import WindowManager

NO_REPLY: Reply = ("", ())


def is_open_tab_alive(match: RunnerMatch) -> bool:
    tab = match.tab
    if tab is None or not shiboken6.isValid(tab.window) or not shiboken6.isValid(tab.tab):
        return False
    return int(tab.tab_model.indexOfTab(tab.tab)) >= 0


class KRunnerService(QObject):
    _instance: ClassVar["KRunnerService | None"] = None

    def __init__(self) -> None:
        super().__init__()
        self._bus = RunnerBus(self.handle_call, self)
        self.last_matches: dict[str, RunnerMatch] = {}
        self._token = b""

    @classmethod
    def instance(cls) -> "KRunnerService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def start(self) -> bool:
        return self._bus.start()

    def stop(self) -> None:
        self._bus.stop()

    def handle_call(self, member: str, body: tuple[Any, ...]) -> Reply | None:
        handlers: dict[str, Callable[..., Reply]] = {
            "Match": self.match,
            "Run": self.run,
            "Actions": lambda *_: ("a(sss)", ([],)),
            "SetActivationToken": self.remember_token,
            "Teardown": self.teardown,
        }
        handler = handlers.get(member)
        return handler(*body) if handler is not None else None

    def match(self, query: str) -> Reply:
        windows = WindowManager.instance().windows()
        matches = find_matches(query, open_tabs(windows))
        self.last_matches = {match.match_id: match for match in matches}
        return match_reply(matches)

    def remember_token(self, token: str) -> Reply:
        self._token = token.encode("utf-8")
        return NO_REPLY

    def teardown(self) -> Reply:
        self.last_matches = {}
        self._token = b""
        return NO_REPLY

    def run(self, match_id: str, _action_id: str = "") -> Reply:
        match = self.last_matches.get(match_id)
        if match is not None:
            self.open(match)
        self._token = b""
        return NO_REPLY

    def open(self, match: RunnerMatch) -> None:
        if match.tab is not None and is_open_tab_alive(match):
            self.switch_to(match)
            return
        message = SingleInstanceMessage(urls=[match.url], activation_token=self._token)
        WindowManager.instance().handle_single_instance_message(message)

    def switch_to(self, match: RunnerMatch) -> None:
        tab = match.tab
        if tab is None:
            return
        tab.tab_model.setCurrentIndex(tab.tab_model.indexOfTab(tab.tab))
        raise_window(tab.window, self._token)
