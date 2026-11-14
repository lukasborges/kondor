from .model import ClassApi, normalize_type

ANY_TYPE = "QVariant"


def missing_names(kind: str, cpp: dict, python: dict) -> list[str]:
    return [f"missing {kind} {name}" for name in sorted(cpp) if name not in python]


def missing_counts(kind: str, cpp: dict[str, set[int]], python: dict[str, set[int]]) -> list[str]:
    problems = []
    for name in sorted(cpp.keys() & python.keys()):
        for count in sorted(cpp[name] - python[name]):
            problems.append(f"{kind} {name} does not accept {count} arguments")
    return problems


def types_match(cpp_type: str, python_type: str) -> bool:
    cpp_name, python_name = normalize_type(cpp_type), normalize_type(python_type)
    return ANY_TYPE in (cpp_name, python_name) or cpp_name == python_name


def property_differences(name: str, cpp: ClassApi, python: ClassApi) -> list[str]:
    cpp_property, python_property = cpp.properties[name], python.properties[name]
    problems = []
    if cpp_property.is_writable != python_property.is_writable:
        problems.append(f"property {name} writability differs")
    if not types_match(cpp_property.type_name, python_property.type_name):
        problems.append(
            f"property {name} type differs: "
            f"{cpp_property.type_name} != {python_property.type_name}"
        )
    return problems


def shared_property_problems(cpp: ClassApi, python: ClassApi) -> list[str]:
    shared = sorted(cpp.properties.keys() & python.properties.keys())
    return [problem for name in shared for problem in property_differences(name, cpp, python)]


def compare_class(cpp: ClassApi, python: ClassApi) -> list[str]:
    problems = missing_names("property", cpp.properties, python.properties)
    problems += missing_names("signal", cpp.signals, python.signals)
    problems += missing_names("callable", cpp.callables, python.callables)
    problems += missing_counts("signal", cpp.signals, python.signals)
    problems += missing_counts("callable", cpp.callables, python.callables)
    return problems + shared_property_problems(cpp, python)


def compare_all(cpp: dict[str, ClassApi], python: dict[str, ClassApi]) -> list[str]:
    problems = []
    for name, python_class in sorted(python.items()):
        if name not in cpp:
            problems.append(f"{name}: no C++ class with this name")
            continue
        problems += [f"{name}: {problem}" for problem in compare_class(cpp[name], python_class)]
    return problems
