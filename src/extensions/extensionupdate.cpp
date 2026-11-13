#include "extensions/extensionmanager.h"

#include <QCoreApplication>

#include "extensions/catalog/extensioncatalog.h"

InstallResult ExtensionManager::refusalForWrongId(const StagedPackage &staged,
                                                  const QString &expectedId) const
{
    if (expectedId.isEmpty() || staged.package.id() == expectedId)
        return {};
    return {false, false, QCoreApplication::translate("ExtensionManager",
                                                      "The package is for “%1”, not “%2”")
                              .arg(staged.package.id(), expectedId)};
}

InstallResult ExtensionManager::refusalForBroaderAccess(const StagedPackage &staged,
                                                        const QString &id) const
{
    const ExtensionAccess update = staged.package.access();
    if (!isInstalled(id) || ExtensionCatalog::isSilentUpdate(update, installedAccess(id)))
        return {};
    return {false, true, QCoreApplication::translate(
                             "ExtensionManager",
                             "The package asks for more permissions than the installed version")};
}

InstallResult ExtensionManager::finishInstall(const StagedPackage &staged,
                                              const InstallResult &refusal)
{
    QString error;
    if (!refusal.isRefused() && installStaged(staged, error))
        return {true, false, QString()};
    installer().discard(staged);
    return refusal.isRefused() ? refusal : InstallResult{false, false, error};
}

InstallResult ExtensionManager::installPackage(const PackageFile &file, const QString &expectedId)
{
    QString error;
    const std::optional<StagedPackage> staged = installer().stage(file, error);
    if (!staged)
        return {false, false, error};
    return finishInstall(*staged, refusalForWrongId(*staged, expectedId));
}

InstallResult ExtensionManager::updatePackage(const PackageFile &file, const QString &expectedId)
{
    QString error;
    const std::optional<StagedPackage> staged = installer().stage(file, error);
    if (!staged)
        return {false, false, error};
    const InstallResult wrongId = refusalForWrongId(*staged, expectedId);
    return finishInstall(*staged, wrongId.isRefused() ? wrongId
                                                      : refusalForBroaderAccess(*staged, expectedId));
}
