import re

NAMED_ENTITIES = (
    ("&amp;", "&"),
    ("&lt;", "<"),
    ("&gt;", ">"),
    ("&quot;", '"'),
    ("&#39;", "'"),
    ("&apos;", "'"),
    ("&nbsp;", " "),
)
NUMERIC_ENTITY = re.compile(r"&#(x?)([0-9a-fA-F]+);")
MARKUP_TAG = re.compile(r"<[^>]*>")
HEXADECIMAL = 16
DECIMAL = 10
LAST_CODE_POINT = 0x10FFFF
SURROGATES = range(0xD800, 0xE000)


def is_valid_code_point(code_point: int) -> bool:
    return code_point != 0 and code_point <= LAST_CODE_POINT and code_point not in SURROGATES


def parsed_code_point(match: re.Match[str]) -> int | None:
    base = HEXADECIMAL if match.group(1) else DECIMAL
    try:
        return int(match.group(2), base)
    except ValueError:
        return None


def decoded_entity(match: re.Match[str]) -> str:
    code_point = parsed_code_point(match)
    if code_point is None or not is_valid_code_point(code_point):
        return match.group(0)
    return chr(code_point)


def decode_entities(text: str) -> str:
    for name, replacement in NAMED_ENTITIES:
        text = text.replace(name, replacement)
    return NUMERIC_ENTITY.sub(decoded_entity, text)


def clean_title(text: str) -> str:
    return " ".join(decode_entities(MARKUP_TAG.sub("", text)).split())


def attribute_value(tag: str, name: str) -> str:
    pattern = re.compile(rf"\b{name}\s*=\s*(?:\"([^\"]*)\"|'([^']*)')", re.IGNORECASE)
    match = pattern.search(tag)
    if match is None:
        return ""
    return match.group(1) or match.group(2) or ""
