#pragma once

#include <QList>
#include <QObject>
#include <QPointer>
#include <QStringList>
#include <QUrl>
#include <QtQmlIntegration/qqmlintegration.h>

#include <memory>

class QQmlComponent;
class QQmlEngine;
class QJSEngine;

// QML singleton `WindowManager`: creates the browser windows, so the app can
// have several of them (normal and private) and move tabs between them.
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

    // The engine that owns the QML component; main.cpp sets it before the first
    // window is created.
    void setEngine(QQmlEngine *engine);

    // Opens a new window with the given tabs (the New Tab page for empty URLs)
    // or, without URLs, with the home page (a private window starts on the New
    // Tab page instead).
    Q_INVOKABLE QObject *newWindow(bool privateWindow = false, const QList<QUrl> &urls = {});

    // A window that finished closing: drops it from the list and deletes it.
    Q_INVOKABLE void closeWindow(QObject *window);

    // Opens the windows of the last session or, when there is nothing to
    // restore, the command-line URLs or a single window with the home page.
    void openStartupWindows();

    int windowCount() const { return int(m_windows.size()); }

signals:
    void windowCountChanged();

private:
    explicit WindowManager(QObject *parent = nullptr);

    QObject *createWindow(bool privateWindow, const QList<QUrl> &urls,
                          const QStringList &titles, int currentIndex);
    QQmlComponent *component();

    QQmlEngine *m_engine = nullptr;
    std::unique_ptr<QQmlComponent> m_component;
    QList<QPointer<QObject>> m_windows;
};
