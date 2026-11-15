import pytest

from kondor.passwords.passwordstore import PasswordStore
from tests.passwords.fakewallet import FakeWallet

DISABLE_VARIABLE = "KONDOR_NO_KWALLET"


@pytest.fixture(autouse=True)
def no_real_wallet(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(DISABLE_VARIABLE, "1")


@pytest.fixture
def wallet(qapp: object) -> FakeWallet:
    return FakeWallet()


@pytest.fixture
def store(wallet: FakeWallet, monkeypatch: pytest.MonkeyPatch) -> PasswordStore:
    monkeypatch.delenv(DISABLE_VARIABLE)
    return PasswordStore(wallet)
