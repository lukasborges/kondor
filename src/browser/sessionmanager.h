#pragma once

#include <QList>
#include <QObject>
#include <QPointer>
#include <QString>
#include <QTimer>
#include <QUrl>
#include <QtQmlIntegration/qqmlintegration.h>

#include "tab.h"
#include "tabmodel.h"

class QQmlEngine;
class QJSEngine;

// One tab of a saved session: its URL (empty for the New Tab page) and title.
struct SessionTab
{
    QUrl url;
    QString title;
};

// One window of a saved session, with the tab selected when it was closed.
struct SessionWindow
{
    QList<SessionTab> tabs;
    int currentIndex = 0;
};

// QML singleton `SessionManager`: keeps the normal tabs of every window in
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

    // Starts the autosave for this window's model: a change to the tab count,
    // the current tab or any tab URL saves the session once the changes settle.
    Q_INVOKABLE void watch(TabModel *model);
    // Writes the current session immediately.
    Q_INVOKABLE void save(TabModel *model);
    // Reads the saved windows, in the old single-window format as well; empty
    // when there is no file, invalid JSON or no normal tab.
    QList<SessionWindow> savedWindows();

private:
    explicit SessionManager(QObject *parent = nullptr);

    void scheduleSave();
    void saveNow();
    void trackTab(Tab *tab);
    void pruneModels();
    static QString sessionFilePath();

    QList<QPointer<TabModel>> m_models;
    QTimer m_saveTimer;
};
