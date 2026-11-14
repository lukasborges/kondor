import pytest

from kondor.history.historymanager import HistoryManager
from pytests.history.historyrows import reset_history


@pytest.fixture
def history(qapp: object) -> HistoryManager:
    reset_history()
    return HistoryManager.instance()
