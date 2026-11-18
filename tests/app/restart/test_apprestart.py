from kondor.app.restart import apprestart
from kondor.app.restart.apprestart import AppRestart


class FakeSessions:
    def save_now(self):
        pass


class FakeSingleInstance:
    def __init__(self):
        self.is_closed = False

    def close(self):
        self.is_closed = True


def test_does_nothing_when_no_restart_requested():
    single_instance = FakeSingleInstance()
    AppRestart().start_again_when_pending(single_instance)
    assert not single_instance.is_closed


def test_closes_server_before_starting_again(monkeypatch):
    calls = []
    single_instance = FakeSingleInstance()
    monkeypatch.setattr(apprestart, "start_again", lambda: calls.append(single_instance.is_closed))
    monkeypatch.setattr(apprestart.QCoreApplication, "quit", lambda: None)
    monkeypatch.setattr(apprestart.SessionManager, "instance", FakeSessions)
    restart = AppRestart()
    restart.restart()
    restart.start_again_when_pending(single_instance)
    assert calls == [True]
