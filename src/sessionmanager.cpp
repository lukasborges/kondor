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

namespace {
constexpr int kSessionVersion = 1;
constexpr int kAutosaveDelayMs = 2000;
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
    if (!model || model == m_model)
        return;

    m_model = model;

    connect(model, &TabModel::countChanged, this, &SessionManager::scheduleSave);
    connect(model, &TabModel::currentIndexChanged, this, &SessionManager::scheduleSave);

    // New tabs appear through the model; follow their URL changes as well.
    connect(model, &QAbstractItemModel::rowsInserted, this,
            [this](const QModelIndex &, int first, int last) {
                for (int row = first; row <= last && row < m_model->count(); ++row) {
                    Tab *tab = m_model->data(m_model->index(row), TabModel::TabRole)
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

void SessionManager::scheduleSave()
{
    if (m_model)
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
    if (!m_model)
        return;

    QJsonArray tabs;
    int currentIndex = 0;
    for (int row = 0; row < m_model->count(); ++row) {
        Tab *tab = m_model->data(m_model->index(row), TabModel::TabRole).value<Tab *>();
        if (!tab || tab->isPrivate())
            continue;

        QJsonObject entry;
        entry.insert(QStringLiteral("url"), tab->url().toString());
        entry.insert(QStringLiteral("title"), tab->title());
        if (row == m_model->currentIndex())
            currentIndex = int(tabs.size());
        tabs.append(entry);
    }

    QJsonObject root;
    root.insert(QStringLiteral("version"), kSessionVersion);
    root.insert(QStringLiteral("currentIndex"), currentIndex);
    root.insert(QStringLiteral("tabs"), tabs);

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

bool SessionManager::restore(TabModel *model)
{
    if (!model)
        return false;
    watch(model);

    QFile file(sessionFilePath());
    if (!file.open(QIODevice::ReadOnly))
        return false;

    QJsonParseError error;
    const QJsonDocument document = QJsonDocument::fromJson(file.readAll(), &error);
    if (error.error != QJsonParseError::NoError || !document.isObject()) {
        qWarning("Kondor: ignoring invalid session file: %s",
                 qUtf8Printable(error.errorString()));
        return false;
    }

    const QJsonObject root = document.object();
    if (root.value(QStringLiteral("version")).toInt() != kSessionVersion) {
        qWarning("Kondor: ignoring unsupported session file version");
        return false;
    }

    const QJsonArray tabs = root.value(QStringLiteral("tabs")).toArray();
    int restored = 0;
    for (const QJsonValue &value : tabs) {
        const QJsonObject entry = value.toObject();
        const QUrl url(entry.value(QStringLiteral("url")).toString());
        if (url.isEmpty())
            continue;

        Tab *tab = model->addTab(false, url);
        const QString title = entry.value(QStringLiteral("title")).toString();
        if (tab && !title.isEmpty())
            tab->setTitle(title);
        ++restored;
    }

    if (restored == 0)
        return false;

    const int currentIndex = root.value(QStringLiteral("currentIndex")).toInt();
    model->setCurrentIndex(qBound(0, currentIndex, restored - 1));
    return true;
}
