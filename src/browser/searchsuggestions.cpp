#include "browser/searchsuggestions.h"

#include "browser/suggestionlist.h"
#include "core/settings.h"

#include <QNetworkAccessManager>
#include <QNetworkReply>
#include <QNetworkRequest>
#include <QUrl>
#include <QUrlQuery>

namespace {
struct Endpoint
{
    QString address;
    QString parameter;
    QString value;
};

const Endpoint &endpointFor(const QString &searchEngine)
{
    static const Endpoint google{QStringLiteral("https://suggestqueries.google.com/complete/search"),
                                 QStringLiteral("client"), QStringLiteral("firefox")};
    static const Endpoint duckDuckGo{QStringLiteral("https://duckduckgo.com/ac/"),
                                     QStringLiteral("type"), QStringLiteral("list")};
    return searchEngine == QLatin1String("google") ? google : duckDuckGo;
}

QUrl endpointUrl(const QString &text)
{
    const Endpoint &endpoint = endpointFor(Settings::instance()->searchEngine());
    QUrlQuery query;
    query.addQueryItem(endpoint.parameter, endpoint.value);
    query.addQueryItem(QStringLiteral("q"), text);
    QUrl url(endpoint.address);
    url.setQuery(query);
    return url;
}

QNetworkRequest buildRequest(const QString &text)
{
    QNetworkRequest request(endpointUrl(text));
    request.setHeader(QNetworkRequest::UserAgentHeader, QStringLiteral("Kondor Browser"));
    request.setAttribute(QNetworkRequest::RedirectPolicyAttribute,
                         QNetworkRequest::NoLessSafeRedirectPolicy);
    return request;
}
}

SearchSuggestions *SearchSuggestions::instance()
{
    static SearchSuggestions *suggestions = new SearchSuggestions;
    return suggestions;
}

SearchSuggestions *SearchSuggestions::create(QQmlEngine *, QJSEngine *)
{
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
    send(buildRequest(query));
}

void SearchSuggestions::send(const QNetworkRequest &request)
{
    m_reply = m_manager->get(request);
    QNetworkReply *reply = m_reply;
    connect(reply, &QNetworkReply::finished, this, [this, reply] { handleReply(reply); });
}

void SearchSuggestions::handleReply(QNetworkReply *reply)
{
    if (reply != m_reply)
        return;
    m_reply = nullptr;
    reply->deleteLater();
    const bool succeeded = reply->error() == QNetworkReply::NoError;
    emit suggestionsReady(m_pendingText,
                          succeeded ? suggestionsFromJson(reply->readAll()) : QStringList());
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
