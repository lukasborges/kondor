def model_record(pair: tuple[str, str], kind: str, version: str) -> dict[str, object]:
    source, target = pair
    name = f"{kind}.{source}{target}"
    return {
        "name": name,
        "fromLang": source,
        "toLang": target,
        "fileType": kind,
        "version": version,
        "filter_expression": "",
        "attachment": {
            "hash": "a" * 64,
            "size": 10,
            "filename": name,
            "location": f"main-workspace/{name}-{version}",
        },
    }


def pair_records(source: str, target: str, version: str = "2.0") -> list[dict[str, object]]:
    return [model_record((source, target), kind, version) for kind in ("model", "lex", "vocab")]


def engine_record(version: str, filter_expression: str = "") -> dict[str, object]:
    return {
        "name": "bergamot-translator",
        "version": version,
        "filter_expression": filter_expression,
        "attachment": {
            "hash": "b" * 64,
            "size": 5,
            "filename": "bergamot-translator.wasm",
            "location": f"engine-{version}",
        },
    }
