#include "extensions/install/packagedownload.h"

#include <QCoreApplication>
#include <QCryptographicHash>
#include <QDir>
#include <QNetworkReply>
#include <QNetworkRequest>

#include "extensions/package/extensionpackage.h"

namespace {

QNetworkRequest requestFor(const CatalogEntry &entry)
{
    QNetworkRequest request(entry.package);
    request.setAttribute(QNetworkRequest::RedirectPolicyAttribute,
                         QNetworkRequest::NoLessSafeRedirectPolicy);
    return request;
}

qint64 limitFor(const CatalogEntry &entry)
{
    const qint64 maximum = ExtensionPackage::kMaxPackageBytes;
    return entry.size > 0 ? qMin(entry.size, maximum) : maximum;
}

QString templatePath()
{
    return QDir::tempPath() + QStringLiteral("/kondor-extension-XXXXXX.kondorext");
}

}

PackageDownload::PackageDownload(QNetworkAccessManager &network, QObject *parent)
    : QObject(parent)
    , m_network(network)
    , m_file(templatePath())
{
    m_file.setAutoRemove(false);
}

void PackageDownload::start(const CatalogEntry &entry)
{
    m_reply = m_network.get(requestFor(entry));
    m_limit = limitFor(entry);
    m_expectedHash = entry.sha256;
    if (!m_file.open())
        return abandon(QCoreApplication::translate("ExtensionCatalog", "Cannot create a temporary file"));
    connect(m_reply, &QNetworkReply::readyRead, this, &PackageDownload::receive);
    connect(m_reply, &QNetworkReply::finished, this, &PackageDownload::complete);
}

void PackageDownload::abandon(const QString &message)
{
    m_reply->abort();
    m_reply->deleteLater();
    finishWith(QString(), message);
}

void PackageDownload::receive()
{
    const QByteArray chunk = m_reply->readAll();
    m_received += chunk.size();
    if (m_received <= m_limit) {
        m_file.write(chunk);
        return;
    }
    m_failure = QCoreApplication::translate("ExtensionCatalog", "The package is larger than expected");
    m_reply->abort();
}

QString PackageDownload::checksumError() const
{
    QFile check(m_file.fileName());
    if (!check.open(QIODevice::ReadOnly))
        return QCoreApplication::translate("ExtensionCatalog", "Cannot read the downloaded package");
    QCryptographicHash hash(QCryptographicHash::Sha256);
    hash.addData(&check);
    if (QString::fromLatin1(hash.result().toHex()) == m_expectedHash)
        return QString();
    return QCoreApplication::translate("ExtensionCatalog",
                                       "The downloaded package does not match its checksum");
}

QString PackageDownload::failureOf() const
{
    if (!m_failure.isEmpty())
        return m_failure;
    if (m_reply->error() != QNetworkReply::NoError)
        return m_reply->errorString();
    return checksumError();
}

void PackageDownload::complete()
{
    m_reply->deleteLater();
    m_file.write(m_reply->readAll());
    m_file.close();
    const QString error = failureOf();
    if (!error.isEmpty())
        QFile::remove(m_file.fileName());
    finishWith(error.isEmpty() ? m_file.fileName() : QString(), error);
}

void PackageDownload::finishWith(const QString &path, const QString &error)
{
    emit finished(path, error);
    deleteLater();
}
