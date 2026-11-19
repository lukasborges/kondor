from collections.abc import Sequence
from typing import NamedTuple

from PySide6.QtCore import Q_ARG, QFile, QIODevice, QMetaObject, QObject, qWarning
from PySide6.QtQml import QJSEngine
from PySide6.QtWebEngineCore import QWebEngineScript
from PySide6.QtWebEngineQuick import QQuickWebEngineProfile

WEB_CHANNEL_RESOURCE = ":/qtwebchannel/qwebchannel.js"
CHANNEL_RESOURCE = ":/scripts/channel.js"
PASSWORDS_RESOURCES = tuple(
    f":/scripts/{name}.js"
    for name in ("usernamefield", "fieldvalue", "newpasswordfield", "passwords", "newpassword")
)
CHANNEL_SCRIPT = "kondor-channel"
PASSWORDS_SCRIPT = "kondor-passwords"
MEDIA_SESSION_RESOURCE = ":/scripts/mediasession.js"
MEDIA_WATCH_RESOURCE = ":/scripts/mediawatch.js"
MEDIA_SESSION_SCRIPT = "kondor-media-session"
MEDIA_WATCH_SCRIPT = "kondor-media-watch"
POPUP_GUARD_RESOURCE = ":/scripts/popupguard.js"
POPUP_WATCH_RESOURCE = ":/scripts/popupwatch.js"
DEVTOOLS_ROUTING_RESOURCE = ":/scripts/devtoolsrouting.js"
DEVTOOLS_ROUTING_SCRIPT = "kondor-devtools-routing"
POPUP_GUARD_SCRIPT = "kondor-popup-guard"
POPUP_WATCH_SCRIPT = "kondor-popup-watch"
USER_SCRIPTS_PROPERTY = "userScripts"
InjectionPoint = QWebEngineScript.InjectionPoint
ScriptWorldId = QWebEngineScript.ScriptWorldId


class ScriptSpec(NamedTuple):
    name: str
    source: str
    injection_point: QWebEngineScript.InjectionPoint
    world: QWebEngineScript.ScriptWorldId = QWebEngineScript.ScriptWorldId.ApplicationWorld
    runs_on_sub_frames: bool = True


def read_resource(path: str) -> str | None:
    file = QFile(path)
    if not file.open(QIODevice.OpenModeFlag.ReadOnly):
        return None
    return bytes(file.readAll().data()).decode()


def joined_resources(paths: Sequence[str]) -> str | None:
    sources = [read_resource(path) for path in paths]
    if any(source is None for source in sources):
        return None
    return "\n".join(source for source in sources if source is not None)


def make_script(spec: ScriptSpec) -> QWebEngineScript:
    script = QWebEngineScript()
    script.setName(spec.name)
    script.setSourceCode(spec.source)
    script.setInjectionPoint(spec.injection_point)
    script.setWorldId(spec.world.value)
    script.setRunsOnSubFrames(spec.runs_on_sub_frames)
    return script


def insert_script(collection: QObject | None, script: QWebEngineScript) -> bool:
    if collection is not None and QMetaObject.invokeMethod(
        collection, "insert", Q_ARG(QWebEngineScript, script)
    ):
        return True
    qWarning(f"Cannot install the page script {script.name()}")
    return False


def install_channel_script(collection: QObject | None) -> bool:
    source = joined_resources((WEB_CHANNEL_RESOURCE, CHANNEL_RESOURCE))
    if source is None:
        qWarning("Web channel script resources not found: autofill and extensions are off")
        return False
    spec = ScriptSpec(CHANNEL_SCRIPT, source, InjectionPoint.DocumentCreation)
    return insert_script(collection, make_script(spec))


def install_passwords_script(collection: QObject | None) -> None:
    source = joined_resources(PASSWORDS_RESOURCES)
    if source is None:
        qWarning("Password script resource not found: autofill is off")
        return
    spec = ScriptSpec(PASSWORDS_SCRIPT, source, InjectionPoint.DocumentReady)
    insert_script(collection, make_script(spec))


class PageScript(NamedTuple):
    name: str
    resource: str
    world: QWebEngineScript.ScriptWorldId


MEDIA_SESSION = PageScript(MEDIA_SESSION_SCRIPT, MEDIA_SESSION_RESOURCE, ScriptWorldId.MainWorld)
MEDIA_WATCH = PageScript(MEDIA_WATCH_SCRIPT, MEDIA_WATCH_RESOURCE, ScriptWorldId.ApplicationWorld)
POPUP_GUARD = PageScript(POPUP_GUARD_SCRIPT, POPUP_GUARD_RESOURCE, ScriptWorldId.MainWorld)
POPUP_WATCH = PageScript(POPUP_WATCH_SCRIPT, POPUP_WATCH_RESOURCE, ScriptWorldId.ApplicationWorld)
TRANSLATE_COLLECT = PageScript(
    "kondor-translate-collect", ":/scripts/translatecollect.js", ScriptWorldId.ApplicationWorld
)
TRANSLATE_PAGE = PageScript(
    "kondor-translate-page", ":/scripts/translatepage.js", ScriptWorldId.ApplicationWorld
)
DEVTOOLS_ROUTING = PageScript(
    DEVTOOLS_ROUTING_SCRIPT, DEVTOOLS_ROUTING_RESOURCE, ScriptWorldId.MainWorld
)


def install_page_script(collection: QObject | None, script: PageScript, feature: str) -> None:
    source = read_resource(script.resource)
    if source is None:
        qWarning(f"Page script resource {script.resource} not found: {feature} is off")
        return
    spec = ScriptSpec(script.name, source, InjectionPoint.DocumentCreation, script.world, False)
    insert_script(collection, make_script(spec))


def install_media_scripts(collection: QObject | None) -> None:
    install_page_script(collection, MEDIA_SESSION, "media controls")
    install_page_script(collection, MEDIA_WATCH, "media controls")


def install_popup_scripts(collection: QObject | None) -> None:
    install_page_script(collection, POPUP_GUARD, "the blocked pop-ups list")
    install_page_script(collection, POPUP_WATCH, "the blocked pop-ups list")


def install_translate_scripts(collection: QObject | None) -> None:
    install_page_script(collection, TRANSLATE_COLLECT, "page translation")
    install_page_script(collection, TRANSLATE_PAGE, "page translation")


def install_devtools_routing(collection: QObject | None) -> None:
    install_page_script(collection, DEVTOOLS_ROUTING, "responsive design mode in Developer Tools")


def keep_cpp_ownership(target: QObject | None) -> None:
    if target is not None:
        QJSEngine.setObjectOwnership(target, QJSEngine.ObjectOwnership.CppOwnership)


def user_scripts(profile: QQuickWebEngineProfile) -> QObject | None:
    keep_cpp_ownership(profile)
    engine = QJSEngine()
    collection = engine.newQObject(profile).property(USER_SCRIPTS_PROPERTY).toQObject()
    keep_cpp_ownership(collection)
    return collection


def install(profile: QQuickWebEngineProfile) -> None:
    collection = user_scripts(profile)
    if not install_channel_script(collection):
        return
    install_media_scripts(collection)
    install_popup_scripts(collection)
    install_translate_scripts(collection)
    install_devtools_routing(collection)
    if not profile.isOffTheRecord():
        install_passwords_script(collection)
