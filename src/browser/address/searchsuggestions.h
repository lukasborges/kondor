#pragma once

#include <QObject>
#include <QString>
#include <QStringList>
#include <QtQmlIntegration/qqmlintegration.h>

class QNetworkAccessManager;
class QNetworkReply;
class QNetworkRequest;
class QQmlEngine;
class QJSEngine;

class SearchSuggestions : public QObject
{
    Q_OBJECT
    QML_ELEMENT
    QML_SINGLETON

public:
    static SearchSuggestions *instance();
    static SearchSuggestions *create(QQmlEngine *engine, QJSEngine *jsEngine);

    Q_INVOKABLE void request(const QString &text);
    Q_INVOKABLE void cancel();

signals:
    void suggestionsReady(const QString &text, const QStringList &items);

private:
    explicit SearchSuggestions(QObject *parent = nullptr);

    void send(const QNetworkRequest &request);
    void handleReply(QNetworkReply *reply);

    QNetworkAccessManager *m_manager = nullptr;
    QNetworkReply *m_reply = nullptr;
    QString m_pendingText;
};
