#include "browser/sessionformat.h"

#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonParseError>

#include <optional>

namespace {
constexpr int kSessionVersion = 2;
constexpr auto kNewTabPageUrl = "about:newtab";

QJsonObject tabToJson(const SessionTab &tab)
{
    const QString url = tab.url.isEmpty() ? QLatin1String(kNewTabPageUrl) : tab.url.toString();
    return {{QStringLiteral("url"), url}, {QStringLiteral("title"), tab.title}};
}

QJsonObject windowToJson(const SessionWindow &window)
{
    QJsonArray tabs;
    for (const SessionTab &tab : window.tabs)
        tabs.append(tabToJson(tab));
    return {{QStringLiteral("currentIndex"), window.currentIndex},
            {QStringLiteral("tabs"), tabs}};
}

SessionTab tabFromJson(const QJsonObject &entry)
{
    SessionTab tab;
    const QString urlString = entry.value(QStringLiteral("url")).toString();
    if (urlString != QLatin1String(kNewTabPageUrl))
        tab.url = QUrl(urlString);
    tab.title = entry.value(QStringLiteral("title")).toString();
    return tab;
}

SessionWindow windowFromJson(const QJsonObject &entry)
{
    SessionWindow window;
    window.currentIndex = entry.value(QStringLiteral("currentIndex")).toInt();
    const QJsonArray tabs = entry.value(QStringLiteral("tabs")).toArray();
    for (const QJsonValue &value : tabs)
        window.tabs.append(tabFromJson(value.toObject()));
    return window;
}

std::optional<QJsonObject> parseRoot(const QByteArray &json)
{
    QJsonParseError error;
    const QJsonDocument document = QJsonDocument::fromJson(json, &error);
    if (error.error == QJsonParseError::NoError && document.isObject())
        return document.object();
    qWarning("Kondor: ignoring invalid session file: %s", qUtf8Printable(error.errorString()));
    return std::nullopt;
}

QList<QJsonObject> windowEntries(const QJsonObject &root)
{
    if (root.value(QStringLiteral("version")).toInt() < 2)
        return {root};
    QList<QJsonObject> entries;
    const QJsonArray array = root.value(QStringLiteral("windows")).toArray();
    for (const QJsonValue &value : array)
        entries.append(value.toObject());
    return entries;
}

bool isSupportedVersion(const QJsonObject &root)
{
    const int version = root.value(QStringLiteral("version")).toInt();
    if (version >= 1 && version <= kSessionVersion)
        return true;
    qWarning("Kondor: ignoring unsupported session file version");
    return false;
}
}

QByteArray SessionFormat::toJson(const QList<SessionWindow> &windows)
{
    QJsonArray array;
    for (const SessionWindow &window : windows)
        array.append(windowToJson(window));
    const QJsonObject root{{QStringLiteral("version"), kSessionVersion},
                           {QStringLiteral("windows"), array}};
    return QJsonDocument(root).toJson(QJsonDocument::Compact);
}

QList<SessionWindow> SessionFormat::fromJson(const QByteArray &json)
{
    const std::optional<QJsonObject> root = parseRoot(json);
    if (!root || !isSupportedVersion(*root))
        return {};
    QList<SessionWindow> windows;
    for (const QJsonObject &entry : windowEntries(*root)) {
        const SessionWindow window = windowFromJson(entry);
        if (!window.tabs.isEmpty())
            windows.append(window);
    }
    return windows;
}
