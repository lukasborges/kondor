#include "bookmarks/bookmarkhtmltext.h"

#include <QRegularExpression>

namespace BookmarkHtmlText {

namespace {

struct NamedEntity {
    QLatin1String name;
    QLatin1String text;
};

constexpr NamedEntity kNamedEntities[] = {
    {QLatin1String("&amp;"), QLatin1String("&")},   {QLatin1String("&lt;"), QLatin1String("<")},
    {QLatin1String("&gt;"), QLatin1String(">")},    {QLatin1String("&quot;"), QLatin1String("\"")},
    {QLatin1String("&#39;"), QLatin1String("'")},   {QLatin1String("&apos;"), QLatin1String("'")},
    {QLatin1String("&nbsp;"), QLatin1String(" ")},
};

bool isValidCodePoint(uint codePoint)
{
    return codePoint != 0 && codePoint <= 0x10FFFF && (codePoint < 0xD800 || codePoint > 0xDFFF);
}

QString decodedEntity(const QRegularExpressionMatch &match)
{
    bool ok = false;
    const int base = match.captured(1).isEmpty() ? 10 : 16;
    const uint codePoint = match.captured(2).toUInt(&ok, base);
    if (!ok || !isValidCodePoint(codePoint))
        return match.captured(0);
    const char32_t value = char32_t(codePoint);
    return QString::fromUcs4(&value, 1);
}

QString decodeNumericEntities(const QString &text)
{
    static const QRegularExpression numeric(QStringLiteral("&#(x?)([0-9a-fA-F]+);"));
    QString decoded;
    int last = 0;
    auto it = numeric.globalMatch(text);
    while (it.hasNext()) {
        const auto match = it.next();
        decoded += text.mid(last, match.capturedStart() - last) + decodedEntity(match);
        last = match.capturedEnd();
    }
    return decoded + text.mid(last);
}

}

QString decodeEntities(QString text)
{
    for (const NamedEntity &entity : kNamedEntities)
        text.replace(entity.name, entity.text);
    return decodeNumericEntities(text);
}

QString cleanTitle(QString text)
{
    text.remove(QRegularExpression(QStringLiteral("<[^>]*>")));
    return decodeEntities(text).simplified();
}

QString attributeValue(const QString &tag, const QString &name)
{
    const QRegularExpression re(
        QStringLiteral("\\b%1\\s*=\\s*(?:\"([^\"]*)\"|'([^']*)')").arg(name),
        QRegularExpression::CaseInsensitiveOption);
    const auto match = re.match(tag);
    if (!match.hasMatch())
        return {};
    return match.captured(1).isEmpty() ? match.captured(2) : match.captured(1);}

}
