#include "extensions/extensionmanager.h"

#include "extensions/contentscriptbuilder.h"
#include "extensions/profilescripts.h"

namespace {

bool runsInProfile(const InstalledExtension &entry, bool privateProfile)
{
    return entry.enabled && (!privateProfile || entry.privateAllowed);
}

}

ContentScriptContext ExtensionManager::contentScriptContext(const InstalledExtension &entry,
                                                            int index, bool privateProfile) const
{
    const QString id = entry.package.id();
    return {&entry.package, index, entry.token, m_locale, privateProfile, settingValues(id),
            m_state.disabledSites(id)};
}

QString ExtensionManager::scriptSource(const QString &id, int index, bool privateProfile) const
{
    const InstalledExtension *entry = find(id);
    if (!entry || index < 0 || index >= entry->package.contentScripts().size())
        return QString();
    return contentScriptSource(contentScriptContext(*entry, index, privateProfile));
}

QList<QWebEngineScript> ExtensionManager::scriptsFor(bool privateProfile) const
{
    QList<QWebEngineScript> scripts;
    for (const InstalledExtension &entry : m_entries) {
        if (!runsInProfile(entry, privateProfile))
            continue;
        for (int i = 0; i < entry.package.contentScripts().size(); ++i)
            scripts.append(contentScript(contentScriptContext(entry, i, privateProfile)));
    }
    return scripts;
}

void ExtensionManager::registerProfile(QQuickWebEngineProfile *profile)
{
    m_scripts->registerProfile(profile);
}

void ExtensionManager::rebuildScripts()
{
    m_scripts->rebuildOnceAfterSeveralChanges();
}
