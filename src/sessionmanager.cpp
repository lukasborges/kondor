#include "sessionmanager.h"

#include "tab.h"
#include "tabmodel.h"

#include <QCoreApplication>
#include <QDir>
#include <QFile>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonParseError>
#include <QQmlEngine>
#include <QSaveFile>
#include <QStandardPaths>

#include <algorithm>
#include <utility>

namespace {
// 2 adds the "windows" array; version 1 is a single window at the root and is
// still read, so an older session is not lost.
constexpr int kSessionVersion = 2;
constexpr int kAutosaveDelayMs = 2000;
// Session marker for a tab on the New Tab page (it has no real URL).
constexpr auto kNewTabPageUrl = "about:newtab";

SessionTab tabFromJson(const QJsonObject &entry)
{
    SessionTab tab;
    const QString urlString = entry.value(QStringLiteral("url")).toString();
    if (urlString != QLatin1String(kNewTabPageUrl))
        tab.url = QUrl(urlString);
    tab.title = entry.value(QStringLiteral("title")).toString();
    return tab;
}
} // namespace

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
    const QString dir =
        QStandardPaths::writableLocation(QStandardPaths::AppDataLocation);
    QDir().mkpath(dir);
    return dir + QStringLiteral("/session.json");
}

void SessionManager::watch(TabModel *model)
{
    if (!model || m_models.contains(model))
        return;

    pruneModels();
    m_models.append(model);

    connect(model, &TabModel::countChanged, this, &SessionManager::scheduleSave);
    connect(model, &TabModel::currentIndexChanged, this, &SessionManager::scheduleSave);
    connect(model, &QObject::destroyed, this, [this]() {
        pruneModels();
        scheduleSave();
    });

    // New tabs appear through the model; follow their URL changes as well.
    connect(model, &QAbstractItemModel::rowsInserted, this,
            [this, model](const QModelIndex &, int first, int last) {
                for (int row = first; row <= last && row < model->count(); ++row) {
                    Tab *tab = model->data(model->index(row), TabModel::TabRole)
                                   .value<Tab *>();
                    trackTab(tab);
                }
                scheduleSave();
            });
    connect(model, &QAbstractItemModel::rowsRemoved, this, &SessionManager::scheduleSave);

    for (int row = 0; row < model->count(); ++row) {
        Tab *tab = model->data(model->index(row), TabModel::TabRole).value<Tab *>();
        trackTab(tab);
    }
}

void SessionManager::trackTab(Tab *tab)
{
    if (!tab)
        return;
    // Connections die with either side, so each tab is tracked exactly once.
    connect(tab, &Tab::urlChanged, this, &SessionManager::scheduleSave);
}

void SessionManager::pruneModels()
{
    for (int i = int(m_models.size()) - 1; i >= 0; --i) {
        if (m_models.at(i).isNull())
            m_models.removeAt(i);
    }
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

void SessionManager::saveNow()
{
    m_saveTimer.stop();
    pruneModels();

    // Every window is gone and the app is quitting: the session saved when the
    // last window closed is the one to keep.
    if (m_models.isEmpty())
        return;

    // The last normal window closed while a private one is still open: keep the
    // session saved when that window closed instead of overwriting it with the
    // empty session of a window that never restores.
    const bool anyNormalWindow =
        std::any_of(m_models.cbegin(), m_models.cend(), [](const QPointer<TabModel> &model) {
            return model && !model->privateTabs();
        });
    if (!anyNormalWindow)
        return;

    QJsonArray windows;
    for (const QPointer<TabModel> &model : std::as_const(m_models)) {
        QJsonArray tabs;
        int currentIndex = 0;
        for (int row = 0; row < model->count(); ++row) {
            Tab *tab = model->data(model->index(row), TabModel::TabRole).value<Tab *>();
            if (!tab || tab->isPrivate())
                continue;

            QJsonObject entry;
            if (tab->newTabPage())
                entry.insert(QStringLiteral("url"), QStringLiteral("about:newtab"));
            else
                entry.insert(QStringLiteral("url"), tab->url().toString());
            entry.insert(QStringLiteral("title"), tab->title());
            if (row == model->currentIndex())
                currentIndex = int(tabs.size());
            tabs.append(entry);
        }

        // A private window, or one whose normal tabs are all gone, is not a
        // window to bring back.
        if (tabs.isEmpty())
            continue;

        QJsonObject window;
        window.insert(QStringLiteral("currentIndex"), currentIndex);
        window.insert(QStringLiteral("tabs"), tabs);
        windows.append(window);
    }

    QJsonObject root;
    root.insert(QStringLiteral("version"), kSessionVersion);
    root.insert(QStringLiteral("windows"), windows);

    QSaveFile file(sessionFilePath());
    if (!file.open(QIODevice::WriteOnly)) {
        qWarning("Kondor: cannot write the session file %s",
                 qUtf8Printable(file.fileName()));
        return;
    }
    file.write(QJsonDocument(root).toJson(QJsonDocument::Compact));
    if (!file.commit())
        qWarning("Kondor: cannot commit the session file %s",
                 qUtf8Printable(file.fileName()));
}

QList<SessionWindow> SessionManager::savedWindows()
{
    QList<SessionWindow> windows;

    QFile file(sessionFilePath());
    if (!file.open(QIODevice::ReadOnly))
        return windows;

    QJsonParseError error;
    const QJsonDocument document = QJsonDocument::fromJson(file.readAll(), &error);
    if (error.error != QJsonParseError::NoError || !document.isObject()) {
        qWarning("Kondor: ignoring invalid session file: %s",
                 qUtf8Printable(error.errorString()));
        return windows;
    }

    const QJsonObject root = document.object();
    const int version = root.value(QStringLiteral("version")).toInt();
    if (version < 1 || version > kSessionVersion) {
        qWarning("Kondor: ignoring unsupported session file version");
        return windows;
    }

    // One entry per window; the old format had a single window at the root.
    QList<QJsonObject> entries;
    if (version >= 2) {
        const QJsonArray array = root.value(QStringLiteral("windows")).toArray();
        entries.reserve(array.size());
        for (const QJsonValue &value : array)
            entries.append(value.toObject());
    } else {
        entries.append(root);
    }

    for (const QJsonObject &entry : std::as_const(entries)) {
        SessionWindow window;
        window.currentIndex = entry.value(QStringLiteral("currentIndex")).toInt();
        const QJsonArray tabs = entry.value(QStringLiteral("tabs")).toArray();
        for (const QJsonValue &value : tabs)
            window.tabs.append(tabFromJson(value.toObject()));
        if (!window.tabs.isEmpty())
            windows.append(window);
    }

    return windows;
}
