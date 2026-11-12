#include "browser/searchsuggestions.h"

#include "core/settings.h"

#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonValue>
#include <QNetworkAccessManager>
#include <QNetworkReply>
#include <QNetworkRequest>
#include <QUrl>
#include <QUrlQuery>

namespace {
// The dropdown only shows a few of them anyway.
constexpr int kMaxSuggestions = 6;
}

SearchSuggestions *SearchSuggestions::instance()
{
    static SearchSuggestions *suggestions = new SearchSuggestions;
    return suggestions;
}

SearchSuggestions *SearchSuggestions::create(QQmlEngine *engine, QJSEngine *jsEngine)
{
    Q_UNUSED(engine)
    Q_UNUSED(jsEngine)
    return instance();
}

SearchSuggestions::SearchSuggestions(QObject *parent)
    : QObject(parent)
    , m_manager(new QNetworkAccessManager(this))
{
}

void SearchSuggestions::request(const QString &text)
{
    const QString query = text.trimmed();
    cancel();
    if (query.isEmpty())
        return;

    m_pendingText = query;

    QNetworkRequest request(endpointUrl(query));
    request.setHeader(QNetworkRequest::UserAgentHeader,
                      QStringLiteral("Kondor Browser"));
    request.setAttribute(QNetworkRequest::RedirectPolicyAttribute,
                         QNetworkRequest::NoLessSafeRedirectPolicy);
    m_reply = m_manager->get(request);

    QNetworkReply *reply = m_reply;
    connect(reply, &QNetworkReply::finished, this, [this, reply]() {
        if (reply != m_reply)
            return;
        m_reply = nullptr;
        reply->deleteLater();

        QStringList items;
        if (reply->error() == QNetworkReply::NoError) {
            const QJsonDocument document = QJsonDocument::fromJson(reply->readAll());
            const QJsonArray root = document.array();
            // Both endpoints answer ["query", ["s1", "s2", …]].
            if (root.size() > 1 && root.at(1).isArray()) {
                const QJsonArray suggestions = root.at(1).toArray();
                items.reserve(qMin(kMaxSuggestions, int(suggestions.size())));
                for (const QJsonValue &value : suggestions) {
                    if (items.size() >= kMaxSuggestions)
                        break;
                    if (value.isString() && !value.toString().isEmpty())
                        items.append(value.toString());
                }
            }
        }

        emit suggestionsReady(m_pendingText, items);
    });
}

void SearchSuggestions::cancel()
{
    if (!m_reply)
        return;
    QNetworkReply *reply = m_reply;
    m_reply = nullptr;
    reply->abort();
    reply->deleteLater();
}

QUrl SearchSuggestions::endpointUrl(const QString &text) const
{
    // Google has a public completion endpoint; every other engine uses
    // DuckDuckGo's autocomplete service.
    const bool google = Settings::instance()->searchEngine() == QLatin1String("google");

    QUrl url(google ? QStringLiteral("https://suggestqueries.google.com/complete/search")
                    : QStringLiteral("https://duckduckgo.com/ac/"));
    QUrlQuery query;
    if (google) {
        query.addQueryItem(QStringLiteral("client"), QStringLiteral("firefox"));
    } else {
        query.addQueryItem(QStringLiteral("type"), QStringLiteral("list"));
    }
    query.addQueryItem(QStringLiteral("q"), text);
    url.setQuery(query);
    return url;
}
