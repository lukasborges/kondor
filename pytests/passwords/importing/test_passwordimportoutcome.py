from kondor.passwords.importing.importoutcome import ImportOutcome

WRITTEN = 5
FAILED = -1


def test_is_notified_once_when_the_page_is_closed() -> None:
    outcome = ImportOutcome()
    outcome.record(WRITTEN, "logins.csv")
    assert outcome.claim_notification()["count"] == WRITTEN
    assert outcome.claim_notification() == {}
    assert outcome.take()["fileName"] == "logins.csv"


def test_is_not_notified_when_the_page_is_open() -> None:
    outcome = ImportOutcome()
    outcome.set_page_open(True)
    outcome.record(WRITTEN, "logins.csv")
    assert outcome.claim_notification() == {}


def test_is_taken_once() -> None:
    outcome = ImportOutcome()
    outcome.record(FAILED, "logins.csv")
    assert outcome.claim_notification() == {}
    assert outcome.take()["count"] == FAILED
    assert outcome.take() == {}
