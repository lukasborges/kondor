import re

from PySide6.QtCore import QT_TRANSLATE_NOOP, QCoreApplication

from kondor.extensions.installedextension import ExtensionContext, find
from kondor.extensions.installresult import InstallResult
from kondor.extensions.package.packagefile import StagedPackage
from kondor.extensions.state.extensionaccess import is_silent_update

CONTEXT = "ExtensionManager"
WRONG_ID = QT_TRANSLATE_NOOP("ExtensionManager", "The package is for “%1”, not “%2”")
BROADER_ACCESS = QT_TRANSLATE_NOOP(
    "ExtensionManager", "The package asks for more permissions than the installed version"
)


def filled(template: str, *values: str) -> str:
    return re.sub(r"%(\d)", lambda found: values[int(found.group(1)) - 1], template)


def refusal_for_wrong_id(staged: StagedPackage, expected_id: str) -> InstallResult:
    if not expected_id or staged.package.id() == expected_id:
        return InstallResult()
    template = QCoreApplication.translate(CONTEXT, WRONG_ID)
    return InstallResult(False, False, filled(template, staged.package.id(), expected_id))


def refusal_for_broader_access(
    context: ExtensionContext, staged: StagedPackage, extension_id: str
) -> InstallResult:
    installed = find(context.entries, extension_id)
    if installed is None or is_silent_update(staged.package.access(), installed.package.access()):
        return InstallResult()
    return InstallResult(False, True, QCoreApplication.translate(CONTEXT, BROADER_ACCESS))
