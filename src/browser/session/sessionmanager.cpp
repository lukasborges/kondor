#include "browser/sessionmanager.h"

#include "browser/sessionformat.h"

#include <QCoreApplication>
#include <QDir>
#include <QFile>
#include <QQmlEngine>
#include <QSaveFile>
#include <QStandardPaths>

#include <algorithm>

namespace {
constexpr int kAutosaveDelayMs = 2000;

Tab *tabAt(const TabModel *model, int row)
{
    return model->data(model->index(row), TabModel::TabRole).value<Tab *>();
}

SessionTab sessionTabOf(const Tab *tab)
{
    return {tab->newTabPage() ? QUrl() : tab->url(), tab->title()};
}

SessionWindow sessionWindowOf(const TabModel *model)
{
    SessionWindow window;
    for (int row = 0; row < model->count(); ++row) {
        const Tab *tab = tabAt(model, row);
        if (!tab || tab->isPrivate())
            continue;
        if (row == model->currentIndex())
            window.currentIndex = int(window.tabs.size());
        window.tabs.append(sessionTabOf(tab));
    }
    return window;
}
}

SessionManager *SessionManager::instance()
{
    static SessionManager *manager = new SessionManager;
    return manager;
}

SessionManager *SessionManager::create(QQmlEngine *, QJSEngine *)
{
    auto *manager = instance();
    QQmlEngine::setObjectOwnership(manager, QQmlEngine::CppOwnership);
    return manager;
}

SessionManager::SessionManager(QObject *parent)
    : QObject(parent)
{
    m_saveTimer.setSingleShot(true);
    m_saveTimer.setInterval(kAutosaveDelayMs);
    connect(&m_saveTimer, &QTimer::timeout, this, &SessionManager::saveNow);
    if (auto *app = QCoreApplication::instance())
        connect(app, &QCoreApplication::aboutToQuit, this, &SessionManager::saveNow);
}

QString SessionManager::sessionFilePath()
{
    const QString dir = QStandardPaths::writableLocation(QStandardPaths::AppDataLocation);
    QDir().mkpath(dir);
    return dir + QStringLiteral("/session.json");
}

void SessionManager::watch(TabModel *model)
{
    if (!model || m_models.contains(model))
        return;
    pruneModels();
    m_models.append(model);
    connectModel(model);
    trackRows(model, 0, model->count() - 1);
}

void SessionManager::connectModel(TabModel *model)
{
    connect(model, &TabModel::countChanged, this, &SessionManager::scheduleSave);
    connect(model, &TabModel::currentIndexChanged, this, &SessionManager::scheduleSave);
    connect(model, &QAbstractItemModel::rowsRemoved, this, &SessionManager::scheduleSave);
    connect(model, &QObject::destroyed, this, &SessionManager::forgetDestroyedModel);
    connectInsertions(model);
}

void SessionManager::connectInsertions(TabModel *model)
{
    connect(model, &QAbstractItemModel::rowsInserted, this,
            [this, model](const QModelIndex &, int first, int last) {
                trackRows(model, first, last);
                scheduleSave();
            });
}

void SessionManager::forgetDestroyedModel()
{
    pruneModels();
    scheduleSave();
}

void SessionManager::trackRows(TabModel *model, int first, int last)
{
    for (int row = first; row <= last && row < model->count(); ++row)
        trackTab(tabAt(model, row));
}

void SessionManager::trackTab(Tab *tab)
{
    if (tab)
        connect(tab, &Tab::urlChanged, this, &SessionManager::scheduleSave);
}

void SessionManager::pruneModels()
{
    m_models.removeIf([](const QPointer<TabModel> &model) { return model.isNull(); });
}

void SessionManager::scheduleSave()
{
    m_saveTimer.start();
}

void SessionManager::save(TabModel *model)
{
    if (model)
        watch(model);
    saveNow();
}

bool SessionManager::hasNormalWindow() const
{
    return std::any_of(m_models.cbegin(), m_models.cend(),
                       [](const QPointer<TabModel> &model) { return model && !model->privateTabs(); });
}

QList<SessionWindow> SessionManager::collectWindows() const
{
    QList<SessionWindow> windows;
    for (const QPointer<TabModel> &model : m_models) {
        const SessionWindow window = sessionWindowOf(model);
        if (!window.tabs.isEmpty())
            windows.append(window);
    }
    return windows;
}

void SessionManager::writeSessionFile(const QByteArray &content) const
{
    QSaveFile file(sessionFilePath());
    if (!file.open(QIODevice::WriteOnly)) {
        qWarning("Kondor: cannot write the session file %s", qUtf8Printable(file.fileName()));
        return;
    }
    file.write(content);
    if (!file.commit())
        qWarning("Kondor: cannot commit the session file %s", qUtf8Printable(file.fileName()));
}

void SessionManager::saveNow()
{
    m_saveTimer.stop();
    pruneModels();
    if (hasNormalWindow())
        writeSessionFile(SessionFormat::toJson(collectWindows()));
}

QList<SessionWindow> SessionManager::savedWindows()
{
    QFile file(sessionFilePath());
    if (!file.open(QIODevice::ReadOnly))
        return {};
    return SessionFormat::fromJson(file.readAll());
}
