#include "extensions/userscripts/userscriptdownload.h"

#include <QCoreApplication>
#include <QNetworkReply>
#include <QNetworkRequest>

#include "extensions/package/extensionpackage.h"

namespace {

QNetworkRequest requestFor(const QUrl &url)
{
    QNetworkRequest request(url);
    request.setAttribute(QNetworkRequest::RedirectPolicyAttribute,
                         QNetworkRequest::NoLessSafeRedirectPolicy);
    return request;
}

}

bool isWebUrl(const QUrl &url)
{
    return url.scheme() == QLatin1String("https") || url.scheme() == QLatin1String("http");
}

bool isFetchableUserScriptUrl(const QUrl &url)
{
    return isWebUrl(url) || url.isLocalFile();
}

UserScriptDownload::UserScriptDownload(QNetworkAccessManager &network, QObject *parent)
    : QObject(parent)
    , m_network(network)
    , m_remainingBytes(ExtensionPackage::kMaxPackageBytes)
{
}

void UserScriptDownload::start(const QUrl &url)
{
    m_wantsRequirements = true;
    fetchScript(url);
}

void UserScriptDownload::startMetadataOnly(const QUrl &url)
{
    m_wantsRequirements = false;
    fetchScript(url);
}

void UserScriptDownload::fetchScript(const QUrl &url)
{
    m_source.installUrl = url;
    fetch(url, [this](const QByteArray &body) { acceptScript(body); });
}

void UserScriptDownload::fetch(const QUrl &url, const BodyHandler &handler)
{
    if (!isFetchableUserScriptUrl(url))
        return fail(QCoreApplication::translate("UserScript", "Unsupported address: %1")
                        .arg(url.toString()));
    QNetworkReply *reply = m_network.get(requestFor(url));
    connect(reply, &QNetworkReply::downloadProgress, this, [this, reply](qint64 received, qint64) {
        m_isTooLarge = m_isTooLarge || received > m_remainingBytes;
        if (m_isTooLarge)
            reply->abort();
    });
    connect(reply, &QNetworkReply::finished, this, [this, reply, handler]() { receive(reply, handler); });
}

void UserScriptDownload::receive(QNetworkReply *reply, const BodyHandler &handler)
{
    reply->deleteLater();
    const QByteArray body = reply->readAll();
    if (m_isTooLarge)
        return fail(QCoreApplication::translate("UserScript", "The script is larger than 5 MiB"));
    if (reply->error() != QNetworkReply::NoError)
        return fail(reply->errorString());
    m_remainingBytes -= body.size();
    handler(body);
}

void UserScriptDownload::acceptScript(const QByteArray &body)
{
    QString error;
    const auto metadata = parseUserScriptMetadata(QString::fromUtf8(body), error);
    if (!metadata)
        return fail(error);
    m_source.script = body;
    m_source.metadata = *metadata;
    if (m_wantsRequirements)
        fetchNextRequirement();
    else
        succeed();
}

void UserScriptDownload::fetchNextRequirement()
{
    if (m_source.isComplete())
        return succeed();
    const QString address = m_source.metadata.requiredUrls.at(m_source.requiredScripts.size());
    fetch(m_source.installUrl.resolved(QUrl(address)), [this](const QByteArray &body) {
        m_source.requiredScripts.append(body);
        fetchNextRequirement();
    });
}

void UserScriptDownload::succeed()
{
    emit finished(m_source, QString());
    deleteLater();
}

void UserScriptDownload::fail(const QString &error)
{
    emit finished(m_source, error);
    deleteLater();
}
