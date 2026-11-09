#pragma once

#include <QObject>
#include <QPointer>
#include <QTimer>
#include <QtQmlIntegration/qqmlintegration.h>

#include "tab.h"
#include "tabmodel.h"

class QQmlEngine;
class QJSEngine;

// QML singleton `SessionManager`: keeps the normal tabs of the current window in
// <AppDataLocation>/session.json so they can be restored on startup. Private
// tabs are never written to disk.
class SessionManager : public QObject
{
    Q_OBJECT
    QML_ELEMENT
    QML_SINGLETON

public:
    static SessionManager *instance();
    static SessionManager *create(QQmlEngine *engine, QJSEngine *jsEngine);

    // Starts the autosave for this model: a change to the tab count, the current
    // tab or any tab URL saves the session once the changes settle.
    Q_INVOKABLE void watch(TabModel *model);
    // Writes the current session immediately.
    Q_INVOKABLE void save(TabModel *model);
    // Recreates the saved tabs in the model; false when there was nothing to
    // restore (no file, invalid JSON, or no normal tabs).
    Q_INVOKABLE bool restore(TabModel *model);

private:
    explicit SessionManager(QObject *parent = nullptr);

    void scheduleSave();
    void saveNow();
    void trackTab(Tab *tab);
    static QString sessionFilePath();

    QPointer<TabModel> m_model;
    QTimer m_saveTimer;
};
