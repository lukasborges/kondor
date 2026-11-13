#pragma once

#include <QHash>
#include <QList>
#include <QObject>
#include <QPointer>
#include <QWebEngineScript>

class ExtensionManager;
class QQuickWebEngineProfile;

class ProfileScripts : public QObject
{
    Q_OBJECT

public:
    explicit ProfileScripts(ExtensionManager *manager);

    void registerProfile(QQuickWebEngineProfile *profile);
    void rebuildOnceAfterSeveralChanges();

private:
    void applyScripts(QQuickWebEngineProfile *profile);
    void removeInserted(QQuickWebEngineProfile *profile, QObject *collection);
    void rebuildAll();

    ExtensionManager *m_manager;
    QList<QPointer<QQuickWebEngineProfile>> m_profiles;
    QHash<QQuickWebEngineProfile *, QList<QWebEngineScript>> m_inserted;
    bool m_isRebuildQueued = false;
};
