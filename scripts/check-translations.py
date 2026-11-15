#!/usr/bin/env python3
import glob
import re
import sys
import xml.etree.ElementTree as ET

PLACEHOLDER = re.compile(r"%\d+|%n")


def translation_texts(message: ET.Element, translation: ET.Element) -> list[str]:
    numerus = message.get("numerus") == "yes"
    forms = translation.findall("numerusform") if numerus else [translation]
    return [(form.text or "").strip() for form in forms]


def message_problem(message: ET.Element) -> str | None:
    source = message.findtext("source") or ""
    translation = message.find("translation")
    if translation is None:
        return f"missing translation for {source!r}"
    texts = translation_texts(message, translation)
    if translation.get("type") == "unfinished" or not texts or not all(texts):
        return f"unfinished or empty translation for {source!r}"
    expected = sorted(set(PLACEHOLDER.findall(source)))
    actual = sorted(set(PLACEHOLDER.findall(" ".join(texts))))
    if expected != actual:
        return f"placeholders differ for {source!r}: expected {expected}, got {actual}"
    return None


def file_problems(path: str) -> list[str]:
    problems = []
    for context in ET.parse(path).getroot():
        for message in context.findall("message"):
            problem = message_problem(message)
            if problem:
                problems.append(f"::error file={path}::{context.findtext('name')}: {problem}")
    return problems


def main() -> int:
    problems = [line for path in sorted(glob.glob("i18n/*.ts")) for line in file_problems(path)]
    print("\n".join(problems))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
