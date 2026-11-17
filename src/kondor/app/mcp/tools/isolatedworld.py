from typing import Any

from kondor.app.mcp.cdp.pagesession import PageSession
from kondor.app.mcp.protocol.toolresult import ToolFailureError

WORLD_NAME = "kondor-agent"
WORLD_KEY = "world"


def frame_id(session: PageSession) -> str:
    return str(session.call("Page.getFrameTree")["frameTree"]["frame"]["id"])


def create_world(session: PageSession) -> int:
    reply = session.call(
        "Page.createIsolatedWorld", {"frameId": frame_id(session), "worldName": WORLD_NAME}
    )
    return int(reply["executionContextId"])


def run_in_world(session: PageSession, expression: str) -> Any:
    cache = session.isolated_worlds
    if WORLD_KEY not in cache:
        cache[WORLD_KEY] = create_world(session)
    reply = evaluate(session, expression, cache[WORLD_KEY])
    if "exceptionDetails" in reply and is_lost_context(reply):
        cache[WORLD_KEY] = create_world(session)
        reply = evaluate(session, expression, cache[WORLD_KEY])
    return value_of(reply)


def evaluate(session: PageSession, expression: str, context_id: int) -> dict[str, Any]:
    try:
        return session.call(
            "Runtime.evaluate",
            {"expression": expression, "contextId": context_id, "returnByValue": True},
        )
    except ToolFailureError as failure:
        return {"exceptionDetails": {"lostContext": "context" in str(failure).lower()}}


def is_lost_context(reply: dict[str, Any]) -> bool:
    return bool(reply["exceptionDetails"].get("lostContext"))


def value_of(reply: dict[str, Any]) -> Any:
    if "exceptionDetails" in reply:
        raise ToolFailureError("The page script failed. Take a new snapshot and try again.")
    return reply.get("result", {}).get("value")
