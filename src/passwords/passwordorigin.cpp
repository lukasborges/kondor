#include "passwords/passwordorigin.h"

namespace PasswordOrigin {

namespace {

bool isWebScheme(const QString &scheme)
{
    return scheme == QLatin1String("http") || scheme == QLatin1String("https");
}

bool isDefaultPort(const QString &scheme, int port)
{
    const int defaultPort = scheme == QLatin1String("http") ? 80 : 443;
    return port == -1 || port == defaultPort;
}

QString portSuffix(const QString &scheme, int port)
{
    if (isDefaultPort(scheme, port))
        return {};
    return QLatin1Char(':') + QString::number(port);
}

bool isLocalhost(const QString &host)
{
    return host == QLatin1String("localhost") || host.endsWith(QLatin1String(".localhost"));
}

}

QString originOf(const QUrl &url)
{
    const QString scheme = url.scheme().toLower();
    if (!isWebScheme(scheme) || url.host().isEmpty())
        return {};
    const QString host = url.host(QUrl::FullyEncoded).toLower();
    return scheme + QLatin1String("://") + host + portSuffix(scheme, url.port());
}

bool canSaveFor(const QString &origin)
{
    const QUrl url(origin);
    const QString host = url.host(QUrl::FullyEncoded).toLower();
    if (url.scheme() == QLatin1String("https"))
        return !host.isEmpty();
    return url.scheme() == QLatin1String("http") && isLocalhost(host);
}

QString originFromInput(const QString &text)
{
    QString input = text.trimmed();
    if (input.isEmpty())
        return {};
    if (!input.contains(QLatin1String("://")))
        input.prepend(QLatin1String("https://"));
    const QString origin = originOf(QUrl(input));
    return canSaveFor(origin) ? origin : QString();
}

QString hostOfOrigin(const QString &origin)
{
    return QUrl(origin).host();
}

}
