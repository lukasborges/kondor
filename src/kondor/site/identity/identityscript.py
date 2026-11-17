import json

from PySide6.QtCore import Q_ARG, QMetaObject, QObject
from PySide6.QtWebEngineCore import QWebEngineScript

from kondor.browser.profile import pagescripts
from kondor.site.identity.useragents import keeps_client_hints

IDENTITY_RESOURCE = ":/scripts/identity.js"
IDENTITY_SCRIPT = "kondor-identity"
InjectionPoint = QWebEngineScript.InjectionPoint
ScriptWorldId = QWebEngineScript.ScriptWorldId


def script_source(agents: dict[str, str], body: str) -> str:
    entries = {
        host: {"agent": agent, "keepsHints": keeps_client_hints(agent)}
        for host, agent in agents.items()
    }
    return f"{{\nconst agents = {json.dumps(entries)};\n{body}\n}}"


def build_script(agents: dict[str, str]) -> QWebEngineScript | None:
    body = pagescripts.read_resource(IDENTITY_RESOURCE)
    if body is None:
        return None
    source = script_source(agents, body)
    spec = pagescripts.ScriptSpec(
        IDENTITY_SCRIPT, source, InjectionPoint.DocumentCreation, ScriptWorldId.MainWorld
    )
    return pagescripts.make_script(spec)


def remove_script(collection: QObject | None, script: QWebEngineScript) -> None:
    if collection is not None:
        QMetaObject.invokeMethod(collection, "remove", Q_ARG(QWebEngineScript, script))
