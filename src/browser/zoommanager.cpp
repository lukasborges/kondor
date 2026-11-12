#include "browser/zoommanager.h"

#include <QtGlobal>

namespace {
constexpr auto kGroup = "SiteZoom";
constexpr qreal kEpsilon = 0.001;

QString key(const QString &host)
{
    // '/' would create a sub-group in QSettings.
    return QString(host).replace(QLatin1Char('/'), QLatin1Char('_'));
}
}

ZoomManager *ZoomManager::instance()
{
    static ZoomManager *manager = new ZoomManager;
    return manager;
}

ZoomManager *ZoomManager::create(QQmlEngine *engine, QJSEngine *jsEngine)
{
    Q_UNUSED(engine)
    Q_UNUSED(jsEngine)
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
    const qreal factor = m_settings.value(QLatin1String(kGroup) + QLatin1Char('/') + key(host), 1.0)
                             .toReal();
    return factor > 0 ? factor : 1.0;
}

void ZoomManager::setZoomFor(const QString &host, qreal factor)
{
    if (host.isEmpty())
        return;
    if (qAbs(zoomFor(host) - factor) < kEpsilon / 10)
        return;
    const QString path = QLatin1String(kGroup) + QLatin1Char('/') + key(host);
    if (qAbs(factor - 1.0) < kEpsilon)
        m_settings.remove(path);
    else
        m_settings.setValue(path, factor);
    m_settings.sync();
    emit zoomChanged(host, qAbs(factor - 1.0) < kEpsilon ? 1.0 : factor);
}

qreal ZoomManager::step(qreal current, int direction) const
{
    const QList<qreal> all = levels();
    if (direction > 0) {
        for (const qreal level : all)
            if (level > current + kEpsilon)
                return level;
        return all.last();
    }
    for (auto it = all.crbegin(); it != all.crend(); ++it)
        if (*it < current - kEpsilon)
            return *it;
    return all.first();
}
