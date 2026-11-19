from pathlib import Path

from kondor.translate.catalog.selection import select_engine, select_models
from kondor.translate.download.bundles import missing_bundles, total_bytes
from kondor.translate.download.catalogloader import Catalog
from kondor.translate.storage.translationstore import TranslationStore
from tests.translate.recordfactory import engine_record, pair_records


def catalog() -> Catalog:
    records = pair_records("de", "en") + pair_records("en", "pt")
    return Catalog(select_engine([engine_record("3.0")]), select_models(records), "https://cdn/")


def install(store: TranslationStore, pair: tuple[str, str]) -> None:
    directory = store.pair_directory(pair)
    store.partial_directory(directory).mkdir(parents=True)
    store.publish(directory, {})


def test_a_new_pair_needs_the_engine_and_its_files(tmp_path: Path) -> None:
    bundles = missing_bundles(TranslationStore(tmp_path), catalog(), [("en", "pt")])
    assert [bundle.directory.name for bundle in bundles] == ["engine", "en-pt"]
    assert total_bytes(bundles) == 5 + 3 * 10


def test_a_pivot_route_downloads_both_pairs(tmp_path: Path) -> None:
    route = [("de", "en"), ("en", "pt")]
    bundles = missing_bundles(TranslationStore(tmp_path), catalog(), route)
    assert [bundle.directory.name for bundle in bundles][1:] == ["de-en", "en-pt"]


def test_installed_pairs_are_not_downloaded_again(tmp_path: Path) -> None:
    store = TranslationStore(tmp_path)
    install(store, ("en", "pt"))
    names = [bundle.directory.name for bundle in missing_bundles(store, catalog(), [("en", "pt")])]
    assert names == ["engine"]
