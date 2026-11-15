import pytest

from kondor.passwords.wallet import kwalletservice
from kondor.passwords.wallet.kwalletservice import KWalletService


class FakeInterface:
    created: list["FakeInterface"] = []
    service_available = False

    def __init__(self, *_arguments: object) -> None:
        self._valid = FakeInterface.service_available
        FakeInterface.created.append(self)

    def isValid(self) -> bool:
        return self._valid


@pytest.fixture
def service(monkeypatch: pytest.MonkeyPatch) -> KWalletService:
    FakeInterface.created = []
    FakeInterface.service_available = False
    monkeypatch.setattr(kwalletservice, "QDBusInterface", FakeInterface)
    return KWalletService()


def test_keeps_a_valid_interface(service: KWalletService) -> None:
    FakeInterface.service_available = True
    first = service._kwallet()
    assert service._kwallet() is first


def test_builds_a_new_interface_when_the_cached_one_is_invalid(service: KWalletService) -> None:
    missing = service._kwallet()
    FakeInterface.service_available = True
    available = service._kwallet()
    assert available is not missing
    assert available.isValid()
