from kondor.app.startup.qmlregistry import FEATURE_TYPES
from pytests.kondortypes import qmltypes_modules


def test_feature_types_list_every_qmltypes_module() -> None:
    assert sorted(module.__name__ for module in FEATURE_TYPES) == sorted(
        module.__name__ for module in qmltypes_modules()
    )


def test_feature_types_list_each_module_once() -> None:
    assert len(set(FEATURE_TYPES)) == len(FEATURE_TYPES)
