#include "addressresolver.h"

#include <QRegularExpression>
#include <QStringList>

namespace {

bool isLocalHost(const QString &host)
{
    if (host.compare(QLatin1String("localhost"), Qt::CaseInsensitive) == 0)
        return true;

    // IPv4 only: loopback and the private ranges dev servers usually use.
    const QStringList parts = host.split(QLatin1Char('.'));
    if (parts.size() != 4)
        return false;

    int octets[4] = {0, 0, 0, 0};
    for (int i = 0; i < 4; ++i) {
        bool ok = false;
        octets[i] = parts.at(i).toInt(&ok);
        if (!ok || octets[i] < 0 || octets[i] > 255)
            return false;
    }

    if (octets[0] == 127)
        return true;
    if (octets[0] == 10)
        return true;
    if (octets[0] == 192 && octets[1] == 168)
        return true;
    if (octets[0] == 172 && octets[1] >= 16 && octets[1] <= 31)
        return true;

    return false;
}

} // namespace

QUrl addressUrl(const QString &text)
{
    const QString input = text.trimmed();
    if (input.isEmpty())
        return QUrl();

    if (input.contains(QLatin1String("://"))
        || input.startsWith(QLatin1String("about:"))
        || input.startsWith(QLatin1String("data:"))) {
        return QUrl::fromUserInput(input);
    }

    // IP, localhost or domain with a TLD -> assume https, except for local
    // hosts, which rarely have TLS.
    static const QRegularExpression hostRe(QStringLiteral(
        R"(^(([0-9]{1,3}\.){3}[0-9]{1,3}|localhost|[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)*\.[a-zA-Z]{2,})(:\d+)?(/.*)?$)"));
    const QRegularExpressionMatch match = hostRe.match(input);
    if (match.hasMatch()) {
        const QString host = match.captured(1);
        const QString scheme = isLocalHost(host) ? QStringLiteral("http://")
                                                 : QStringLiteral("https://");
        return QUrl(scheme + input);
    }

    return QUrl();
}

QUrl searchUrl(const QString &text, const QString &searchTemplate)
{
    QString url = searchTemplate;
    url.replace(QLatin1String("%1"),
                QString::fromUtf8(QUrl::toPercentEncoding(text.trimmed())));
    return QUrl(url);
}

QUrl resolveAddress(const QString &text, const QUrl &homePage, const QString &searchTemplate)
{
    if (text.trimmed().isEmpty())
        return homePage;

    const QUrl url = addressUrl(text);
    if (!url.isEmpty())
        return url;

    // Otherwise search with the configured engine.
    return searchUrl(text, searchTemplate);
}
