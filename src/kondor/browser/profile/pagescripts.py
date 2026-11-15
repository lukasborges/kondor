from typing import NamedTuple

from PySide6.QtCore import Q_ARG, QFile, QIODevice, QMetaObject, QObject, qWarning
from PySide6.QtQml import QJSEngine
from PySide6.QtWebEngineCore import QWebEngineScript
from PySide6.QtWebEngineQuick import QQuickWebEngineProfile

WEB_CHANNEL_RESOURCE = ":/qtwebchannel/qwebchannel.js"
CHANNEL_RESOURCE = ":/scripts/channel.js"
USERNAME_FIELD_RESOURCE = ":/scripts/usernamefield.js"
PASSWORDS_RESOURCE = ":/scripts/passwords.js"
CHANNEL_SCRIPT = "kondor-channel"
PASSWORDS_SCRIPT = "kondor-passwords"
USER_SCRIPTS_PROPERTY = "userScripts"
InjectionPoint = QWebEngineScript.InjectionPoint


class ScriptSpec(NamedTuple):
    name: str
    source: str
    injection_point: QWebEngineScript.InjectionPoint


def read_resource(path: str) -> str | None:
    file = QFile(path)
    if not file.open(QIODevice.OpenModeFlag.ReadOnly):
        return None
    return bytes(file.readAll().data()).decode()


def joined_resources(first_path: str, second_path: str) -> str | None:
    first, second = read_resource(first_path), read_resource(second_path)
    if first is None or second is None:
        return None
    return first + "\n" + second


def make_script(spec: ScriptSpec) -> QWebEngineScript:
    script = QWebEngineScript()
    script.setName(spec.name)
    script.setSourceCode(spec.source)
    script.setInjectionPoint(spec.injection_point)
    script.setWorldId(QWebEngineScript.ScriptWorldId.ApplicationWorld.value)
    script.setRunsOnSubFrames(True)
    return script


def insert_script(collection: QObject | None, script: QWebEngineScript) -> bool:
    if collection is not None and QMetaObject.invokeMethod(
        collection, "insert", Q_ARG(QWebEngineScript, script)
    ):
        return True
    qWarning(f"Cannot install the page script {script.name()}")
    return False


def install_channel_script(collection: QObject | None) -> bool:
    source = joined_resources(WEB_CHANNEL_RESOURCE, CHANNEL_RESOURCE)
    if source is None:
        qWarning("Web channel script resources not found: autofill and extensions are off")
        return False
    spec = ScriptSpec(CHANNEL_SCRIPT, source, InjectionPoint.DocumentCreation)
    return insert_script(collection, make_script(spec))


def install_passwords_script(collection: QObject | None) -> None:
    source = joined_resources(USERNAME_FIELD_RESOURCE, PASSWORDS_RESOURCE)
    if source is None:
        qWarning("Password script resource not found: autofill is off")
        return
    spec = ScriptSpec(PASSWORDS_SCRIPT, source, InjectionPoint.DocumentReady)
    insert_script(collection, make_script(spec))


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
    if not profile.isOffTheRecord():
        install_passwords_script(collection)
