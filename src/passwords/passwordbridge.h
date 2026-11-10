#pragma once

#include <QObject>
#include <QPointer>
#include <QVariantList>
#include "tab.h"
#include <QtQmlIntegration/qqmlintegration.h>



// Object registered on each page's QWebChannel as "kondorPasswords". The
// page-side script (scripts/passwords.js, application world) calls it; one
// bridge belongs to one tab. A private tab's bridge refuses every call, and
// private views never get the script.
class PasswordBridge : public QObject
{
    Q_OBJECT
    QML_ELEMENT

    Q_PROPERTY(Tab *tab READ tab WRITE setTab NOTIFY tabChanged)

public:
    explicit PasswordBridge(QObject *parent = nullptr);

    Tab *tab() const { return m_tab; }
    void setTab(Tab *tab);

    // A login form was submitted: may turn into a "save password" prompt.
    Q_INVOKABLE void formSubmitted(const QString &origin, const QString &username,
                                   const QString &password);
    // `[{ username, password }]` saved for the origin.
    Q_INVOKABLE QVariantList credentialsFor(const QString &origin);

    // Fills the login form of the tab's page with a saved credential (key icon).
    Q_INVOKABLE void fill(const QString &username);

signals:
    void tabChanged();
    // For the page script: saved credentials may have changed, fill again.
    void credentialsChanged();
    // For the page script: fill the form of this origin.
    void fillRequested(const QString &origin, const QString &username, const QString &password);

private:
    bool allowed() const;

    QPointer<Tab> m_tab;
};
