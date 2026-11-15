from dataclasses import dataclass, field
from functools import cache
from typing import Any

from PySide6.QtCore import QFile, QIODevice, QJsonDocument, QLocale, qWarning
from PySide6.QtWebEngineCore import QWebEngineScript

from kondor.extensions.package.contentscript import ExtensionContentScript
from kondor.extensions.package.extensionpackage import ExtensionPackage
from kondor.extensions.scripts.matchpatternglobs import match_pattern_as_globs

RUNTIME_RESOURCE = ":/scripts/extensionruntime.js"
InjectionPoint = QWebEngineScript.InjectionPoint
INJECTION_POINTS = {
    "document-start": InjectionPoint.DocumentCreation,
    "document-end": InjectionPoint.DocumentReady,
}
SITE_CHECK = (
    "\nif (__cfg.disabledSites.indexOf(location.origin) !== -1)\n    return;\n"
    "const kondor = __kondorCreateRuntime(__cfg);\n"
)
STYLE_INJECTOR = (
    "(function (styles) {\n"
    "    if (styles.length === 0) return;\n"
    "    function add() {\n"
    "        styles.forEach(function (text) {\n"
    '            const style = document.createElement("style");\n'
    "            style.textContent = text;\n"
    "            document.documentElement.appendChild(style);\n"
    "        });\n"
    "    }\n"
    "    if (document.documentElement) { add(); return; }\n"
    "    new MutationObserver(function (records, observer) {\n"
    "        if (document.documentElement) { observer.disconnect(); add(); }\n"
    "    }).observe(document, { childList: true });\n"
    "})(__cfg.css);\n"
)


@dataclass
class ContentScriptContext:
    package: ExtensionPackage
    index: int = 0
    token: str = ""
    locale: str = ""
    is_private: bool = False
    settings: dict[str, Any] = field(default_factory=dict)
    disabled_sites: list[str] = field(default_factory=list)


@cache
def runtime_source() -> str:
    file = QFile(RUNTIME_RESOURCE)
    if file.open(QIODevice.OpenModeFlag.ReadOnly):
        return bytes(file.readAll().data()).decode()
    qWarning("Extension runtime script not found: extensions are off")
    return ""


def compact_json(value: dict[str, Any]) -> str:
    document = QJsonDocument(value)
    return bytes(document.toJson(QJsonDocument.JsonFormat.Compact).data()).decode()


def file_text(package: ExtensionPackage, file: str) -> str:
    return package.read_file(file).decode(errors="replace")


def include_globs(content: ExtensionContentScript) -> list[str]:
    globs = list(content.include)
    for match in content.matches:
        globs += match_pattern_as_globs(match)
    return globs


def directive_lines(name: str, values: list[str]) -> str:
    return "".join(f"// @{name} {value}\n" for value in values)


def metadata_block(content: ExtensionContentScript) -> str:
    if content.include:
        url_lines = directive_lines("include", include_globs(content))
    else:
        url_lines = directive_lines("match", content.matches)
    run_at = directive_lines("run-at", [content.run_at])
    exclude = directive_lines("exclude", content.exclude)
    return f"// ==UserScript==\n{url_lines}{exclude}{run_at}// ==/UserScript==\n"


def package_fields(package: ExtensionPackage, content: ExtensionContentScript) -> dict[str, Any]:
    css = [file_text(package, file) for file in content.css]
    return {"id": package.id(), "version": package.version(), "css": css}


def configuration_object(context: ContentScriptContext, content: ExtensionContentScript) -> str:
    return compact_json(
        {
            **package_fields(context.package, content),
            "token": context.token,
            "locale": context.locale or QLocale.system().name(),
            "isPrivate": context.is_private,
            "settings": context.settings,
            "disabledSites": context.disabled_sites,
        }
    )


def javascript_files(package: ExtensionPackage, content: ExtensionContentScript) -> str:
    if not content.js:
        return ""
    files = "".join(file_text(package, file) + "\n;\n" for file in content.js)
    return "(function (kondor) {\n" + files + "})(kondor);\n"


def script_body(context: ContentScriptContext, content: ExtensionContentScript) -> str:
    configuration = configuration_object(context, content)
    start = "(function () {\nconst __cfg = " + configuration + ";\n"
    middle = runtime_source() + SITE_CHECK + STYLE_INJECTOR
    return start + middle + javascript_files(context.package, content) + "})();\n"


def content_of(context: ContentScriptContext) -> ExtensionContentScript:
    return context.package.content_scripts()[context.index]


def content_script_source(context: ContentScriptContext) -> str:
    content = content_of(context)
    return metadata_block(content) + script_body(context, content)


def content_script(context: ContentScriptContext) -> QWebEngineScript:
    content = content_of(context)
    script = QWebEngineScript()
    script.setName(f"kondor-ext:{context.package.id()}:{context.index}")
    script.setSourceCode(content_script_source(context))
    script.setWorldId(QWebEngineScript.ScriptWorldId.ApplicationWorld.value)
    script.setRunsOnSubFrames(content.all_frames)
    script.setInjectionPoint(INJECTION_POINTS.get(content.run_at, InjectionPoint.Deferred))
    return script
