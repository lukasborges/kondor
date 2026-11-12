#pragma once

#include <QObject>
#include <QString>
#include <QStringList>
#include <QtQmlIntegration/qqmlintegration.h>

class QNetworkAccessManager;
class QNetworkReply;
class QQmlEngine;
class QJSEngine;

// QML singleton `SearchSuggestions`: fetches the configured search engine's
// completion list for the text typed in the address bar. Requests are canceled
// as soon as a new one starts, and QML never calls this for private tabs (the
// privacy barrier lives there, like for HistoryManager).
class SearchSuggestions : public QObject
{
    Q_OBJECT
    QML_ELEMENT
    QML_SINGLETON

public:
    static SearchSuggestions *instance();
    static SearchSuggestions *create(QQmlEngine *engine, QJSEngine *jsEngine);

    // Starts a request for the whole text; cancels the previous one.
    Q_INVOKABLE void request(const QString &text);
    // Drops the pending request without emitting anything.
    Q_INVOKABLE void cancel();

signals:
    // `text` is the text the request was made for, so the caller can ignore
    // answers that arrive after the field changed.
    void suggestionsReady(const QString &text, const QStringList &items);

private:
    explicit SearchSuggestions(QObject *parent = nullptr);

    QUrl endpointUrl(const QString &text) const;

    QNetworkAccessManager *m_manager = nullptr;
    QNetworkReply *m_reply = nullptr;
    QString m_pendingText;
};
