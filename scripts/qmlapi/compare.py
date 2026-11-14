from dataclasses import dataclass

from .model import ClassApi, normalize_type

ANY_TYPE = "QVariant"
OBJECT_TYPES = {"QAbstractItemModel", "QObject"}
QT_OBJECT_TYPES = {"QQuickWebEngineProfile"}
LIST_TYPE = "QVariantList"


@dataclass(frozen=True)
class ClassPair:
    cpp: ClassApi
    python: ClassApi
    registered_names: frozenset[str]


def missing_names(kind: str, cpp: dict, python: dict) -> list[str]:
    return [f"missing {kind} {name}" for name in sorted(cpp) if name not in python]


def missing_counts(kind: str, cpp: dict[str, set[int]], python: dict[str, set[int]]) -> list[str]:
    problems = []
    for name in sorted(cpp.keys() & python.keys()):
        for count in sorted(cpp[name] - python[name]):
            problems.append(f"{kind} {name} does not accept {count} arguments")
    return problems


def is_registered_object(cpp_name: str, python_name: str, registered_names: frozenset[str]) -> bool:
    is_known_object = cpp_name in registered_names or cpp_name in QT_OBJECT_TYPES
    return python_name in OBJECT_TYPES and is_known_object


def is_list_of_values(cpp_name: str, python_name: str) -> bool:
    return python_name == LIST_TYPE and cpp_name.startswith("QList<")


def types_match(cpp_type: str, python_type: str, registered_names: frozenset[str]) -> bool:
    cpp_name, python_name = normalize_type(cpp_type), normalize_type(python_type)
    if ANY_TYPE in (cpp_name, python_name) or cpp_name == python_name:
        return True
    if is_list_of_values(cpp_name, python_name):
        return True
    return is_registered_object(cpp_name, python_name, registered_names)


def property_differences(name: str, classes: ClassPair) -> list[str]:
    cpp_property, python_property = classes.cpp.properties[name], classes.python.properties[name]
    problems = []
    if cpp_property.is_writable != python_property.is_writable:
        problems.append(f"property {name} writability differs")
    if not types_match(cpp_property.type_name, python_property.type_name, classes.registered_names):
        problems.append(
            f"property {name} type differs: "
            f"{cpp_property.type_name} != {python_property.type_name}"
        )
    return problems


def shared_property_problems(classes: ClassPair) -> list[str]:
    shared = sorted(classes.cpp.properties.keys() & classes.python.properties.keys())
    return [problem for name in shared for problem in property_differences(name, classes)]


def compare_class(classes: ClassPair) -> list[str]:
    cpp, python = classes.cpp, classes.python
    problems = missing_names("property", cpp.properties, python.properties)
    problems += missing_names("signal", cpp.signals, python.signals)
    problems += missing_names("callable", cpp.callables, python.callables)
    problems += missing_counts("signal", cpp.signals, python.signals)
    problems += missing_counts("callable", cpp.callables, python.callables)
    return problems + shared_property_problems(classes)


def compare_all(cpp: dict[str, ClassApi], python: dict[str, ClassApi]) -> list[str]:
    registered_names = frozenset(python)
    problems = []
    for name, python_class in sorted(python.items()):
        if name not in cpp:
            problems.append(f"{name}: no C++ class with this name")
            continue
        classes = ClassPair(cpp[name], python_class, registered_names)
        problems += [f"{name}: {problem}" for problem in compare_class(classes)]
    return problems
