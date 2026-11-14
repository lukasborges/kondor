from PySide6.QtCore import QFile

from kondor.extensions import extensioninstall, extensionupdate
from kondor.extensions.installedextension import JsonMap
from kondor.extensions.installresult import InstallResult
from kondor.extensions.manager.extensionrows import ExtensionRows
from kondor.extensions.package.extensionpackage import ExtensionPackage
from kondor.extensions.package.packagefile import PackageFile, StagedPackage
from kondor.extensions.package.packagesuffix import has_package_suffix
from kondor.extensions.userscripts.userscriptpackage import UserScriptSource


class ExtensionInstalls(ExtensionRows):
    def __init__(self) -> None:
        super().__init__()
        self._staged: StagedPackage | None = None

    def cancel_staged(self) -> None:
        self.discard_staged()
        if self._pending_preview:
            self.set_pending({})

    def confirm_staged(self) -> None:
        if self._staged is None:
            return self.set_pending({})
        staged, self._staged = self._staged, None
        error = self.install_staged(staged)
        self.installer().discard(staged)
        return self.set_pending(
            extensioninstall.failed_preview(staged.file, error) if error else {}
        )

    def stage_user_script(self, source: UserScriptSource, error: str) -> None:
        file, error = extensioninstall.user_script_package_file(source, error)
        if error:
            return self.refuse_package(file, error)
        self.prepare_install(file)
        return None

    def discard_staged(self) -> None:
        if self._staged is not None:
            self.installer().discard(self._staged)
            self._staged = None

    def set_pending(self, preview: JsonMap) -> None:
        self._pending_preview = preview
        self.pendingInstallChanged.emit()

    def refuse_package(self, file: PackageFile, error: str) -> None:
        if file.is_temporary:
            QFile.remove(file.zip_path)
        self.set_pending(extensioninstall.failed_preview(file, error))

    def prepare_install(self, file: PackageFile) -> bool:
        self.discard_staged()
        self._staged, error = self.installer().stage(file)
        if self._staged is None:
            self.refuse_package(file, error)
            return False
        self.set_pending(extensioninstall.preview_of(self._context, self._staged))
        return True

    @staticmethod
    def is_package_file(path: str) -> bool:
        return has_package_suffix(path)

    def install_staged(self, staged: StagedPackage) -> str:
        return self.installer().commit(staged) or self.add_installed(staged)

    def add_installed(self, staged: StagedPackage) -> str:
        extension_id = staged.package.id()
        package, error = ExtensionPackage.load(f"{self.extensions_directory()}/{extension_id}")
        if not package.is_valid():
            return error
        self._context.state.set_source(extension_id, staged.file.source)
        self._context.state.sync()
        self.put_entry(self.make_entry(package))
        self.changed()
        return ""

    def finish_install(self, staged: StagedPackage, refusal: InstallResult) -> InstallResult:
        error = "" if refusal.is_refused() else self.install_staged(staged)
        if not refusal.is_refused() and not error:
            return InstallResult(True, False, "")
        self.installer().discard(staged)
        return refusal if refusal.is_refused() else InstallResult(False, False, error)

    def install_package(self, file: PackageFile, expected_id: str) -> InstallResult:
        staged, error = self.installer().stage(file)
        if staged is None:
            return InstallResult(False, False, error)
        refusal = extensionupdate.refusal_for_wrong_id(staged, expected_id)
        return self.finish_install(staged, refusal)

    def update_package(self, file: PackageFile, expected_id: str) -> InstallResult:
        staged, error = self.installer().stage(file)
        if staged is None:
            return InstallResult(False, False, error)
        refusal = extensionupdate.refusal_for_wrong_id(staged, expected_id)
        if not refusal.is_refused():
            refusal = extensionupdate.refusal_for_broader_access(self._context, staged, expected_id)
        return self.finish_install(staged, refusal)
