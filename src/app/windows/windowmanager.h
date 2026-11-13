#pragma once

#include <QList>
#include <QObject>
#include <QPointer>
#include <QStringList>
#include <QUrl>
#include <QtQmlIntegration/qqmlintegration.h>

#include <memory>

#include "app/instance/singleinstance.h"

class QQmlComponent;
class QQmlEngine;
class QJSEngine;

struct WindowContents
{
    bool isPrivate = false;
    QList<QUrl> urls;
    QStringList titles;
    int currentIndex = -1;
};

class WindowManager : public QObject
{
    Q_OBJECT
    QML_ELEMENT
    QML_SINGLETON

    Q_PROPERTY(int windowCount READ windowCount NOTIFY windowCountChanged)

public:
    ~WindowManager() override;

    static WindowManager *instance();
    static WindowManager *create(QQmlEngine *engine, QJSEngine *jsEngine);

    void setEngine(QQmlEngine *engine);

    Q_INVOKABLE QObject *newWindow(bool privateWindow = false, const QList<QUrl> &urls = {});
    Q_INVOKABLE void closeWindow(QObject *window);

    void handleSingleInstanceMessage(const SingleInstanceMessage &message);
    void openStartupWindows();

    int windowCount() const { return int(m_windows.size()); }

signals:
    void windowCountChanged();

private:
    explicit WindowManager(QObject *parent = nullptr);

    QObject *createWindow(const WindowContents &contents);
    QQmlComponent *component();
    QQmlComponent *loadComponent();
    void track(QObject *window);
    void followActivity(QObject *window);
    void forgetClosedWindows();

    QObject *windowForRequest(bool privateWindow) const;
    static bool isPrivateWindow(const QObject *window);

    void showExtensionPackage(QObject *window, const QString &path);
    QObject *showPackages(const QStringList &packages, QObject *window);
    QObject *openUrlsForLaunch(const SingleInstanceMessage &message, const QList<QUrl> &urls);
    QObject *normalWindow();
    void addTabs(QObject *window, const QList<QUrl> &urls);
    bool openRestoredWindows();
    bool openCommandLineWindow(const QList<QUrl> &urls);

    QQmlEngine *m_engine = nullptr;
    std::unique_ptr<QQmlComponent> m_component;
    QList<QPointer<QObject>> m_windows;
    QPointer<QObject> m_activeWindow;
};
