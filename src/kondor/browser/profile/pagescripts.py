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


class MediaScript(NamedTuple):
    name: str
    resource: str
    world: QWebEngineScript.ScriptWorldId


MEDIA_SESSION = MediaScript(MEDIA_SESSION_SCRIPT, MEDIA_SESSION_RESOURCE, ScriptWorldId.MainWorld)
MEDIA_WATCH = MediaScript(MEDIA_WATCH_SCRIPT, MEDIA_WATCH_RESOURCE, ScriptWorldId.ApplicationWorld)


def install_media_script(collection: QObject | None, media: MediaScript) -> None:
    source = read_resource(media.resource)
    if source is None:
        qWarning(f"Media script resource {media.resource} not found: media controls are off")
        return
    spec = ScriptSpec(media.name, source, InjectionPoint.DocumentCreation, media.world, False)
    insert_script(collection, make_script(spec))


def install_media_scripts(collection: QObject | None) -> None:
    install_media_script(collection, MEDIA_SESSION)
    install_media_script(collection, MEDIA_WATCH)


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
    if not profile.isOffTheRecord():
        install_passwords_script(collection)
