#pragma once

#include <QNetworkAccessManager>
#include <QObject>
#include <QPointer>
#include <QTemporaryFile>

#include "extensions/catalogentry.h"

class QNetworkReply;

class PackageDownload : public QObject
{
    Q_OBJECT

public:
    PackageDownload(QNetworkAccessManager &network, QObject *parent);

    void start(const CatalogEntry &entry);

signals:
    void finished(const QString &path, const QString &error);

private:
    void abandon(const QString &message);
    void receive();
    void complete();
    void finishWith(const QString &path, const QString &error);
    QString failureOf() const;
    QString checksumError() const;

    QNetworkAccessManager &m_network;
    QTemporaryFile m_file;
    QPointer<QNetworkReply> m_reply;
    qint64 m_limit = 0;
    qint64 m_received = 0;
    QString m_expectedHash;
    QString m_failure;
};
