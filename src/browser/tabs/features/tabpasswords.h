#pragma once

#include <QObject>
#include <QString>
#include <QStringList>
#include <QUrl>
#include <QtQmlIntegration/qqmlintegration.h>

class TabPasswords : public QObject
{
    Q_OBJECT
    QML_ELEMENT
    QML_UNCREATABLE("Owned by Tab")

    Q_PROPERTY(QString prompt READ prompt NOTIFY promptChanged)
    Q_PROPERTY(QString promptUsername READ promptUsername NOTIFY promptChanged)
    Q_PROPERTY(QString promptHost READ promptHost NOTIFY promptChanged)
    Q_PROPERTY(QString host READ host NOTIFY usernamesChanged)
    Q_PROPERTY(QStringList usernames READ usernames NOTIFY usernamesChanged)

public:
    explicit TabPasswords(bool isPrivate, QObject *parent = nullptr);

    QString prompt() const { return m_prompt; }
    QString promptUsername() const { return m_username; }
    QString promptHost() const;
    QString host() const;
    QStringList usernames() const { return m_usernames; }

    void offerSave(const QString &origin, const QString &username, const QString &password);
    void showWalletNotice();
    void updateUsernamesFor(const QUrl &url);
    Q_INVOKABLE void savePending();
    Q_INVOKABLE void neverSavePending();
    Q_INVOKABLE void dismissPrompt();
    Q_INVOKABLE void fill(const QString &username);
    Q_INVOKABLE void copyUsername(const QString &username);
    Q_INVOKABLE void copyPassword(const QString &username);

signals:
    void promptChanged();
    void usernamesChanged();
    void fillRequested(const QString &username);

private:
    void clearPrompt();
    void showPrompt(const QString &prompt);
    void addOriginToNeverSaveSites();

    bool m_isPrivate = false;
    QUrl m_url;
    QString m_prompt;
    QString m_origin;
    QString m_username;
    QString m_password;
    QStringList m_usernames;
};
