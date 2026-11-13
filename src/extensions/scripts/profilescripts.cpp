#include "extensions/profilescripts.h"

#include <QQuickWebEngineProfile>

#include "extensions/extensionmanager.h"

ProfileScripts::ProfileScripts(ExtensionManager *manager)
    : QObject(manager)
    , m_manager(manager)
{
}

void ProfileScripts::registerProfile(QQuickWebEngineProfile *profile)
{
    if (!profile)
        return;
    m_profiles.append(profile);
    connect(profile, &QObject::destroyed, this, [this, profile]() { m_inserted.remove(profile); });
    applyScripts(profile);
}

void ProfileScripts::removeInserted(QQuickWebEngineProfile *profile, QObject *collection)
{
    const QList<QWebEngineScript> old = m_inserted.take(profile);
    for (const QWebEngineScript &script : old)
        QMetaObject::invokeMethod(collection, "remove", Q_ARG(QWebEngineScript, script));
}

void ProfileScripts::applyScripts(QQuickWebEngineProfile *profile)
{
    QObject *collection = profile->property("userScripts").value<QObject *>();
    if (!collection)
        return;
    removeInserted(profile, collection);
    const QList<QWebEngineScript> scripts = m_manager->scriptsFor(profile->isOffTheRecord());
    for (const QWebEngineScript &script : scripts)
        QMetaObject::invokeMethod(collection, "insert", Q_ARG(QWebEngineScript, script));
    m_inserted.insert(profile, scripts);
}

void ProfileScripts::rebuildAll()
{
    m_isRebuildQueued = false;
    for (const QPointer<QQuickWebEngineProfile> &profile : std::as_const(m_profiles)) {
        if (profile)
            applyScripts(profile);
    }
}

void ProfileScripts::rebuildOnceAfterSeveralChanges()
{
    if (m_isRebuildQueued)
        return;
    m_isRebuildQueued = true;
    QMetaObject::invokeMethod(this, &ProfileScripts::rebuildAll, Qt::QueuedConnection);
}
