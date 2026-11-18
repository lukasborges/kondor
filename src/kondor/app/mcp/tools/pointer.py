from kondor.app.mcp.cdp.pagesession import PageSession
from kondor.app.mcp.protocol.toolresult import ToolFailureError
from kondor.app.mcp.tools.isolatedworld import run_in_world
from kondor.app.mcp.tools.snapshotscript import CENTER_SCRIPT, VIEWPORT_CENTER_SCRIPT

STALE_ELEMENT = "Unknown element uid. Take a new snapshot and use a uid from it."


def element_center(session: PageSession, uid: str) -> tuple[float, float]:
    if not uid.isdigit():
        raise ToolFailureError(STALE_ELEMENT)
    center = run_in_world(session, CENTER_SCRIPT % int(uid))
    if center is None:
        raise ToolFailureError(STALE_ELEMENT)
    return float(center["x"]), float(center["y"])


def viewport_center(session: PageSession) -> tuple[float, float]:
    center = run_in_world(session, VIEWPORT_CENTER_SCRIPT)
    return float(center["x"]), float(center["y"])


ANNOUNCED_KINDS = {"mouseMoved": "move", "mousePressed": "press"}


def mouse_event(session: PageSession, kind: str, position: tuple[float, float]) -> None:
    if kind in ANNOUNCED_KINDS:
        session.announce_pointer(ANNOUNCED_KINDS[kind], position)
    session.call("Input.dispatchMouseEvent", mouse_parameters(kind, position))


def mouse_parameters(kind: str, position: tuple[float, float]) -> dict[str, object]:
    is_moving = kind == "mouseMoved"
    return {
        "type": kind,
        "x": position[0],
        "y": position[1],
        "button": "none" if is_moving else "left",
        "buttons": 1 if kind == "mousePressed" else 0,
        "clickCount": 0 if is_moving else 1,
    }


def move_to(session: PageSession, position: tuple[float, float]) -> None:
    mouse_event(session, "mouseMoved", position)


def click_at(session: PageSession, position: tuple[float, float]) -> None:
    move_to(session, position)
    mouse_event(session, "mousePressed", position)
    mouse_event(session, "mouseReleased", position)


def wheel(session: PageSession, position: tuple[float, float], delta: tuple[float, float]) -> None:
    session.call(
        "Input.dispatchMouseEvent",
        {
            "type": "mouseWheel",
            "x": position[0],
            "y": position[1],
            "deltaX": delta[0],
            "deltaY": delta[1],
        },
    )
