#pragma once

#include <QObject>
#include <QPointer>
#include <QVariantList>
#include "browser/tab.h"
#include <QtQmlIntegration/qqmlintegration.h>



// Object registered on each page's QWebChannel as "kondorPasswords". The
// page-side script (scripts/passwords.js, application world) calls it; one
// bridge belongs to one tab. A private tab's bridge refuses every call, and
// private views never get the script.
class PasswordBridge;

// The only object published on the web channel: just the page-facing API, with
// no property that could leak the tab, the profile or anything else.
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

    // The object to register on the web channel as "kondorPasswords".
    Q_INVOKABLE QObject *pageApi() const { return m_api; }

    // A login form was submitted: may turn into a "save password" prompt.
    void formSubmitted(const QString &origin, const QString &username, const QString &password);
    // `[{ username, password }]` saved for the origin.
    QVariantList credentialsFor(const QString &origin);

    // Fills the login form of the tab's page with a saved credential (key icon).
    Q_INVOKABLE void fill(const QString &username);

signals:
    void tabChanged();

private:
    bool allowed() const;

    QPointer<Tab> m_tab;
    PasswordPageApi *m_api;
};
