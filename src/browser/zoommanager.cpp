#include "browser/zoommanager.h"

#include <QtGlobal>

#include <algorithm>

namespace {
constexpr auto kGroup = "SiteZoom";
constexpr qreal kEpsilon = 0.001;

QString settingsPath(const QString &host)
{
    return QLatin1String(kGroup) + QLatin1Char('/') + QString(host).replace(QLatin1Char('/'), QLatin1Char('_'));
}

bool isDefaultZoom(qreal factor)
{
    return qAbs(factor - 1.0) < kEpsilon;
}

qreal nextLevelAbove(qreal current)
{
    const QList<qreal> all = ZoomManager::levels();
    const auto it = std::find_if(all.cbegin(), all.cend(),
                                 [current](qreal level) { return level > current + kEpsilon; });
    return it != all.cend() ? *it : all.last();
}

qreal nextLevelBelow(qreal current)
{
    const QList<qreal> all = ZoomManager::levels();
    const auto it = std::find_if(all.crbegin(), all.crend(),
                                 [current](qreal level) { return level < current - kEpsilon; });
    return it != all.crend() ? *it : all.first();
}
}

ZoomManager *ZoomManager::instance()
{
    static ZoomManager *manager = new ZoomManager;
    return manager;
}

ZoomManager *ZoomManager::create(QQmlEngine *, QJSEngine *)
{
    return instance();
}

ZoomManager::ZoomManager(QObject *parent)
    : QObject(parent)
    , m_settings(QStringLiteral("KDE"), QStringLiteral("Kondor"))
{
}

QList<qreal> ZoomManager::levels()
{
    return {0.3, 0.5, 0.67, 0.8, 0.9, 1.0, 1.1, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0, 4.0, 5.0};
}

QString ZoomManager::hostOf(const QUrl &url) const
{
    if (url.scheme() != QLatin1String("http") && url.scheme() != QLatin1String("https"))
        return {};
    return url.host().toLower();
}

qreal ZoomManager::zoomFor(const QString &host) const
{
    if (host.isEmpty())
        return 1.0;
    const qreal factor = m_settings.value(settingsPath(host), 1.0).toReal();
    return factor > 0 ? factor : 1.0;
}

void ZoomManager::storeZoom(const QString &host, qreal factor)
{
    if (isDefaultZoom(factor))
        m_settings.remove(settingsPath(host));
    else
        m_settings.setValue(settingsPath(host), factor);
    m_settings.sync();
}

void ZoomManager::setZoomFor(const QString &host, qreal factor)
{
    if (host.isEmpty() || qAbs(zoomFor(host) - factor) < kEpsilon / 10)
        return;
    storeZoom(host, factor);
    emit zoomChanged(host, isDefaultZoom(factor) ? 1.0 : factor);
}

qreal ZoomManager::step(qreal current, int direction) const
{
    return direction > 0 ? nextLevelAbove(current) : nextLevelBelow(current);
}
