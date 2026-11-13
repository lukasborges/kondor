#pragma once

#include <QList>
#include <QObject>
#include <QPointer>
#include <QString>
#include <QTimer>
#include <QtQmlIntegration/qqmlintegration.h>

#include "browser/sessionwindow.h"
#include "browser/tab.h"
#include "browser/tabmodel.h"

class QQmlEngine;
class QJSEngine;

class SessionManager : public QObject
{
    Q_OBJECT
    QML_ELEMENT
    QML_SINGLETON

public:
    static SessionManager *instance();
    static SessionManager *create(QQmlEngine *engine, QJSEngine *jsEngine);

    Q_INVOKABLE void watch(TabModel *model);
    Q_INVOKABLE void save(TabModel *model);
    QList<SessionWindow> savedWindows();

private:
    explicit SessionManager(QObject *parent = nullptr);

    void scheduleSave();
    void saveNow();
    void connectModel(TabModel *model);
    void connectInsertions(TabModel *model);
    void forgetDestroyedModel();
    void trackRows(TabModel *model, int first, int last);
    void trackTab(Tab *tab);
    void pruneModels();
    bool hasNormalWindow() const;
    QList<SessionWindow> collectWindows() const;
    void writeSessionFile(const QByteArray &content) const;
    static QString sessionFilePath();

    QList<QPointer<TabModel>> m_models;
    QTimer m_saveTimer;
};
