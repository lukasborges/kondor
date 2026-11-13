#include "app/windowmanager.h"

#include <QQmlComponent>
#include <QQmlEngine>
#include <QQuickWindow>
#include <QVariantMap>

namespace {
QVariantMap initialProperties(const WindowContents &contents)
{
    QVariantMap properties;
    properties.insert(QStringLiteral("privateWindow"), contents.isPrivate);
    properties.insert(QStringLiteral("initialUrls"), QVariant::fromValue(contents.urls));
    properties.insert(QStringLiteral("initialTitles"), QVariant::fromValue(contents.titles));
    properties.insert(QStringLiteral("initialCurrentIndex"), contents.currentIndex);
    return properties;
}

void warnCreationFailed(const QQmlComponent &component)
{
    qWarning("Kondor: cannot create the browser window: %s",
             qUtf8Printable(component.errorString()));
}
}

WindowManager *WindowManager::instance()
{
    static WindowManager *manager = new WindowManager;
    return manager;
}

WindowManager *WindowManager::create(QQmlEngine *engine, QJSEngine *)
{
    auto *manager = instance();
    manager->setEngine(engine);
    QQmlEngine::setObjectOwnership(manager, QQmlEngine::CppOwnership);
    return manager;
}

WindowManager::WindowManager(QObject *parent)
    : QObject(parent)
{
}

WindowManager::~WindowManager() = default;

void WindowManager::setEngine(QQmlEngine *engine)
{
    if (engine && !m_engine)
        m_engine = engine;
}

QQmlComponent *WindowManager::component()
{
    if (m_component)
        return m_component.get();
    if (m_engine)
        return loadComponent();
    qWarning("Kondor: cannot create a window before the QML engine is set");
    return nullptr;
}

QQmlComponent *WindowManager::loadComponent()
{
    m_component = std::make_unique<QQmlComponent>(m_engine, QStringLiteral("Kondor"),
                                                  QStringLiteral("BrowserWindow"));
    if (!m_component->isError())
        return m_component.get();
    qWarning("Kondor: cannot load the browser window: %s",
             qUtf8Printable(m_component->errorString()));
    m_component.reset();
    return nullptr;
}

QObject *WindowManager::newWindow(bool privateWindow, const QList<QUrl> &urls)
{
    return createWindow({privateWindow, urls, {}, -1});
}

void WindowManager::closeWindow(QObject *window)
{
    if (window)
        window->deleteLater();
}

QObject *WindowManager::createWindow(const WindowContents &contents)
{
    QQmlComponent *windowComponent = component();
    if (!windowComponent)
        return nullptr;
    QObject *window = windowComponent->createWithInitialProperties(initialProperties(contents));
    if (!window)
        warnCreationFailed(*windowComponent);
    else
        track(window);
    return window;
}

void WindowManager::track(QObject *window)
{
    m_windows.append(window);
    m_activeWindow = window;
    followActivity(window);
    emit windowCountChanged();
    connect(window, &QObject::destroyed, this, &WindowManager::forgetClosedWindows);
}

void WindowManager::followActivity(QObject *window)
{
    auto *quickWindow = qobject_cast<QQuickWindow *>(window);
    if (!quickWindow)
        return;
    connect(quickWindow, &QQuickWindow::activeChanged, this, [this, quickWindow]() {
        if (quickWindow->isActive())
            m_activeWindow = quickWindow;
    });
}

void WindowManager::forgetClosedWindows()
{
    m_windows.removeIf([](const QPointer<QObject> &window) { return window.isNull(); });
    if (m_activeWindow.isNull() && !m_windows.isEmpty())
        m_activeWindow = m_windows.last().data();
    emit windowCountChanged();
}

QObject *WindowManager::windowForRequest(bool privateWindow) const
{
    if (m_activeWindow && isPrivateWindow(m_activeWindow) == privateWindow)
        return m_activeWindow;
    for (auto it = m_windows.crbegin(); it != m_windows.crend(); ++it) {
        if (it->data() && isPrivateWindow(it->data()) == privateWindow)
            return it->data();
    }
    return nullptr;
}

bool WindowManager::isPrivateWindow(const QObject *window)
{
    return window && window->property("privateWindow").toBool();
}
