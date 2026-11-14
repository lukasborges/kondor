from dataclasses import dataclass

from PySide6.QtWebEngineCore import QWebEngineScript

from kondor.extensions.extensionconfiguration import setting_values
from kondor.extensions.installedextension import ExtensionContext, InstalledExtension
from kondor.extensions.scripts.contentscriptbuilder import (
    ContentScriptContext,
    content_script,
    content_script_source,
)


@dataclass
class ScriptTarget:
    entry: InstalledExtension
    index: int
    is_private: bool


def runs_in_profile(entry: InstalledExtension, is_private: bool) -> bool:
    return entry.enabled and (not is_private or entry.private_allowed)


def script_context(context: ExtensionContext, target: ScriptTarget) -> ContentScriptContext:
    extension_id = target.entry.package.id()
    return ContentScriptContext(
        package=target.entry.package,
        index=target.index,
        token=target.entry.token,
        locale=context.locale,
        is_private=target.is_private,
        settings=setting_values(context, extension_id),
        disabled_sites=context.state.disabled_sites(extension_id),
    )


def script_source(context: ExtensionContext, target: ScriptTarget | None) -> str:
    if target is None:
        return ""
    return content_script_source(script_context(context, target))


def source_target(
    entry: InstalledExtension | None, index: int, is_private: bool
) -> ScriptTarget | None:
    if entry is None or not 0 <= index < len(entry.package.content_scripts()):
        return None
    return ScriptTarget(entry, index, is_private)


def scripts_for(context: ExtensionContext, is_private: bool) -> list[QWebEngineScript]:
    scripts: list[QWebEngineScript] = []
    for entry in context.entries:
        if runs_in_profile(entry, is_private):
            scripts.extend(entry_scripts(context, entry, is_private))
    return scripts


def entry_scripts(
    context: ExtensionContext, entry: InstalledExtension, is_private: bool
) -> list[QWebEngineScript]:
    indexes = range(len(entry.package.content_scripts()))
    targets = [ScriptTarget(entry, index, is_private) for index in indexes]
    return [content_script(script_context(context, target)) for target in targets]
