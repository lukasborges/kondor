#pragma once

#include <QObject>
#include <QPointer>
#include <QVariantList>
#include "browser/tabs/tab.h"
#include <QtQmlIntegration/qqmlintegration.h>

class PasswordBridge;

class PasswordPageApi : public QObject
{
    Q_OBJECT
public:
    explicit PasswordPageApi(PasswordBridge *bridge);

    Q_INVOKABLE void formSubmitted(const QString &origin, const QString &username,
                                   const QString &password);
    Q_INVOKABLE QVariantList credentialsFor(const QString &origin);

signals:
    void credentialsChanged();
    void fillRequested(const QString &origin, const QString &username, const QString &password);

private:
    PasswordBridge *m_bridge;
};

class PasswordBridge : public QObject
{
    Q_OBJECT
    QML_ELEMENT

    Q_PROPERTY(Tab *tab READ tab WRITE setTab NOTIFY tabChanged)

public:
    explicit PasswordBridge(QObject *parent = nullptr);

    Tab *tab() const { return m_tab; }
    void setTab(Tab *tab);

    Q_INVOKABLE QObject *pageApi() const { return m_api; }

    void formSubmitted(const QString &origin, const QString &username, const QString &password);
    QVariantList credentialsFor(const QString &origin);

    Q_INVOKABLE void fill(const QString &username);

signals:
    void tabChanged();

private:
    bool allowed() const;
    bool mayOfferSave(const QString &origin, const QString &password) const;
    void showWalletNoticeOnce();
    bool isAlreadySaved(const QString &origin, const QString &username, const QString &password) const;

    QPointer<Tab> m_tab;
    PasswordPageApi *m_api;
};
