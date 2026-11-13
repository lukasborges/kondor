#include "browser/address/addressresolver.h"

#include <QRegularExpression>
#include <QStringList>

#include <array>
#include <optional>

namespace {
using Octets = std::array<int, 4>;

constexpr int kInvalidOctet = -1;

int parseOctet(const QString &text)
{
    bool ok = false;
    const int octet = text.toInt(&ok);
    return ok && octet >= 0 && octet <= 255 ? octet : kInvalidOctet;
}

std::optional<Octets> parseIPv4(const QString &host)
{
    const QStringList parts = host.split(QLatin1Char('.'));
    if (parts.size() != 4)
        return std::nullopt;
    Octets octets{};
    for (int i = 0; i < 4; ++i) {
        octets[i] = parseOctet(parts.at(i));
        if (octets[i] == kInvalidOctet)
            return std::nullopt;
    }
    return octets;
}

bool isPrivateRange(const Octets &octets)
{
    return octets[0] == 127 || octets[0] == 10 || (octets[0] == 192 && octets[1] == 168)
            || (octets[0] == 172 && octets[1] >= 16 && octets[1] <= 31);
}

bool isLocalHost(const QString &host)
{
    if (host.compare(QLatin1String("localhost"), Qt::CaseInsensitive) == 0)
        return true;
    const std::optional<Octets> octets = parseIPv4(host);
    return octets && isPrivateRange(*octets);
}

bool hasExplicitScheme(const QString &input)
{
    return input.contains(QLatin1String("://")) || input.startsWith(QLatin1String("about:"))
            || input.startsWith(QLatin1String("data:"));
}

QUrl urlForHostPattern(const QString &input)
{
    static const QRegularExpression hostRe(QStringLiteral(
        R"(^(([0-9]{1,3}\.){3}[0-9]{1,3}|localhost|[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)*\.[a-zA-Z]{2,})(:\d+)?(/.*)?$)"));
    const QRegularExpressionMatch match = hostRe.match(input);
    if (!match.hasMatch())
        return QUrl();
    const bool isLocal = isLocalHost(match.captured(1));
    return QUrl((isLocal ? QStringLiteral("http://") : QStringLiteral("https://")) + input);
}
}

QUrl addressUrl(const QString &text)
{
    const QString input = text.trimmed();
    if (input.isEmpty())
        return QUrl();
    if (hasExplicitScheme(input))
        return QUrl::fromUserInput(input);
    return urlForHostPattern(input);
}

QUrl searchUrl(const QString &text, const QString &searchTemplate)
{
    QString url = searchTemplate;
    url.replace(QLatin1String("%1"), QString::fromUtf8(QUrl::toPercentEncoding(text.trimmed())));
    return QUrl(url);
}

QUrl resolveAddress(const QString &text, const QUrl &homePage, const QString &searchTemplate)
{
    if (text.trimmed().isEmpty())
        return homePage;
    const QUrl url = addressUrl(text);
    return url.isEmpty() ? searchUrl(text, searchTemplate) : url;
}
