import hashlib
from pathlib import Path

from kondor.translate.storage.filehash import matches_hash
from kondor.translate.storage.translationstore import TranslationStore

PAYLOAD_BYTES = 100


def publish_pair(store: TranslationStore, pair: tuple[str, str]) -> None:
    directory = store.pair_directory(pair)
    partial = store.partial_directory(directory)
    partial.mkdir(parents=True)
    (partial / "model.bin").write_bytes(b"x" * PAYLOAD_BYTES)
    store.publish(directory, {"model": "model.bin"})


def test_publishes_a_pair_and_lists_it_with_its_size(tmp_path: Path) -> None:
    store = TranslationStore(tmp_path)
    publish_pair(store, ("en", "pt"))
    assert store.is_pair_installed(("en", "pt"))
    [installed] = store.installed_pairs()
    assert (installed.source, installed.target) == ("en", "pt")
    assert installed.size_bytes >= PAYLOAD_BYTES


def test_returns_the_files_of_an_installed_pair(tmp_path: Path) -> None:
    store = TranslationStore(tmp_path)
    publish_pair(store, ("en", "pt"))
    assert store.pair_files(("en", "pt")) == {
        "model": store.pair_directory(("en", "pt")) / "model.bin"
    }


def test_removing_a_pair_deletes_its_files(tmp_path: Path) -> None:
    store = TranslationStore(tmp_path)
    publish_pair(store, ("en", "pt"))
    store.remove_pair(("en", "pt"))
    assert not store.pair_directory(("en", "pt")).exists()
    assert store.installed_pairs() == []


def test_ignores_partial_downloads(tmp_path: Path) -> None:
    store = TranslationStore(tmp_path)
    partial = store.partial_directory(store.pair_directory(("en", "pt")))
    partial.mkdir(parents=True)
    assert store.installed_pairs() == []


def test_discarding_a_partial_download_deletes_its_files(tmp_path: Path) -> None:
    store = TranslationStore(tmp_path)
    directory = store.pair_directory(("en", "pt"))
    store.partial_directory(directory).mkdir(parents=True)
    store.discard_partial(directory)
    assert not store.partial_directory(directory).exists()


def test_checks_a_file_against_its_sha256(tmp_path: Path) -> None:
    path = tmp_path / "file.bin"
    path.write_bytes(b"content")
    assert matches_hash(path, hashlib.sha256(b"content").hexdigest())
    assert not matches_hash(path, "0" * 64)
    assert not matches_hash(tmp_path / "missing", "0" * 64)
