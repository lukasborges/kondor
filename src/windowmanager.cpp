#include "windowmanager.h"

#include "sessionmanager.h"
#include "settings.h"
#include "startupargs.h"

#include <QQmlComponent>
#include <QQmlEngine>
#include <QVariantMap>

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
    if (!m_engine) {
        qWarning("Kondor: cannot create a window before the QML engine is set");
        return nullptr;
    }

    m_component = std::make_unique<QQmlComponent>(m_engine, QStringLiteral("Kondor"),
                                                  QStringLiteral("BrowserWindow"));
    if (m_component->isError()) {
        qWarning("Kondor: cannot load the browser window: %s",
                 qUtf8Printable(m_component->errorString()));
        m_component.reset();
        return nullptr;
    }
    return m_component.get();
}

QObject *WindowManager::newWindow(bool privateWindow, const QList<QUrl> &urls)
{
    return createWindow(privateWindow, urls, QStringList(), -1);
}

void WindowManager::closeWindow(QObject *window)
{
    if (!window)
        return;
    // Deferred: the close event is still being handled here.
    window->deleteLater();
}

QObject *WindowManager::createWindow(bool privateWindow, const QList<QUrl> &urls,
                                     const QStringList &titles, int currentIndex)
{
    QQmlComponent *windowComponent = component();
    if (!windowComponent)
        return nullptr;

    QVariantMap properties;
    properties.insert(QStringLiteral("privateWindow"), privateWindow);
    properties.insert(QStringLiteral("initialUrls"), QVariant::fromValue(urls));
    properties.insert(QStringLiteral("initialTitles"), QVariant::fromValue(titles));
    properties.insert(QStringLiteral("initialCurrentIndex"), currentIndex);

    QObject *window = windowComponent->createWithInitialProperties(properties);
    if (!window) {
        qWarning("Kondor: cannot create the browser window: %s",
                 qUtf8Printable(windowComponent->errorString()));
        return nullptr;
    }

    m_windows.append(window);
    emit windowCountChanged();
    connect(window, &QObject::destroyed, this, [this]() {
        for (int i = int(m_windows.size()) - 1; i >= 0; --i) {
            if (m_windows.at(i).isNull())
                m_windows.removeAt(i);
        }
        emit windowCountChanged();
    });
    return window;
}

void WindowManager::openStartupWindows()
{
    const QList<QUrl> startupUrls = StartupArgs::instance()->startupUrls();
    const bool startupPrivate = StartupArgs::instance()->startupPrivate();
    const bool restore = Settings::instance()->startupBehavior() == QLatin1String("restore");

    bool opened = false;
    if (restore) {
        const QList<SessionWindow> windows = SessionManager::instance()->savedWindows();
        for (const SessionWindow &state : windows) {
            QList<QUrl> urls;
            QStringList titles;
            urls.reserve(state.tabs.size());
            titles.reserve(state.tabs.size());
            for (const SessionTab &tab : state.tabs) {
                urls.append(tab.url);
                titles.append(tab.title);
            }
            opened = createWindow(false, urls, titles, state.currentIndex) || opened;
        }
    }

    // Command-line URLs get their own window, private with --private, the way
    // the "New Private Window" desktop action expects.
    if (!startupUrls.isEmpty() || startupPrivate) {
        opened = createWindow(startupPrivate, startupUrls, QStringList(), -1) || opened;
    }

    if (!opened)
        createWindow(false, {}, QStringList(), -1);
}
