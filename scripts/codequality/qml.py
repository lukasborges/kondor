import re
from typing import List, NamedTuple

from .blocks import count_parameters, match_braces, matching_parenthesis
from .metrics import Body, Function, measure, unique_keys

HANDLER = re.compile(
    r"(?<![\w.])((?:[A-Za-z_]\w*\.)*on[A-Z]\w*)\s*:\s*(?:function\s*\([^)]*\)\s*)?\{"
)
FUNCTION = re.compile(r"\bfunction\s*([A-Za-z_]\w*)?\s*\(")
RETURN_TYPE = re.compile(r"\s*(?::\s*[\w.<>\[\]]+\s*)?\{")


class Candidate(NamedTuple):
    start: int
    name: str
    brace: int
    parameters: str
    is_handler: bool


def handler_candidates(text: str) -> List[Candidate]:
    candidates = []
    for match in HANDLER.finditer(text):
        name = match.group(1).split(".")[-1]
        parameters = parameters_of(text, match.start(), match.end())
        candidates.append(Candidate(match.start(), name, match.end() - 1, parameters, True))
    return candidates


def parameters_of(text: str, start: int, end: int) -> str:
    keyword = text.find("function", start, end)
    if keyword < 0:
        return ""
    open_index = text.index("(", keyword)
    return text[open_index + 1:matching_parenthesis(text, open_index)]


def function_candidate(text: str, match) -> List[Candidate]:
    open_index = match.end() - 1
    close_index = matching_parenthesis(text, open_index)
    after = RETURN_TYPE.match(text, close_index + 1)
    if not after:
        return []
    parameters = text[open_index + 1:close_index]
    return [Candidate(match.start(), match.group(1) or "anonymous", after.end() - 1, parameters, False)]


def function_candidates(text: str) -> List[Candidate]:
    candidates = []
    for match in FUNCTION.finditer(text):
        candidates += function_candidate(text, match)
    return candidates


def outermost(candidates: List[Candidate], pairs: dict) -> List[Candidate]:
    chosen: List[Candidate] = []
    limit = -1
    for candidate in sorted(candidates, key=lambda item: item.start):
        if candidate.start > limit:
            chosen.append(candidate)
            limit = pairs.get(candidate.brace, candidate.brace)
    return chosen


def handler_keys(functions: List[Function], candidates: List[Candidate], path: str) -> List[Function]:
    counts: dict = {}
    result = []
    for function, candidate in zip(functions, candidates):
        if candidate.is_handler:
            counts[candidate.name] = counts.get(candidate.name, 0) + 1
            function = function._replace(key="%s::%s#%d" % (path, candidate.name, counts[candidate.name]))
        result.append(function)
    return result


def find_qml_functions(path: str, text: str) -> List[Function]:
    pairs = match_braces(text)
    chosen = outermost(handler_candidates(text) + function_candidates(text), pairs)
    chosen = [item for item in chosen if item.brace in pairs]
    bodies = [Body(text, (item.brace, pairs[item.brace])) for item in chosen]
    functions = [qml_function(path, body, item) for body, item in zip(bodies, chosen)]
    return unique_keys(handler_keys(functions, chosen, path))


def qml_function(path: str, body: Body, candidate: Candidate) -> Function:
    return measure("%s::%s" % (path, candidate.name), body, count_parameters(candidate.parameters))
