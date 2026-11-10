#pragma once

#include <QHash>
#include <QList>
#include <QObject>
#include <QSet>
#include <QString>
#include <QUrl>
#include <QtQmlIntegration/qqmlintegration.h>
#include <QQuickWebEngineProfile>

class QQmlEngine;
class QJSEngine;

class ProfileManager : public QObject
{
    Q_OBJECT
    QML_ELEMENT
    QML_SINGLETON

    Q_PROPERTY(QString homePage READ homePage NOTIFY homePageChanged)

public:
    static ProfileManager *instance();
    static ProfileManager *create(QQmlEngine *engine, QJSEngine *jsEngine);

    // Persistent profile (cookies, cache, history) used by normal tabs.
    Q_INVOKABLE QQuickWebEngineProfile *defaultProfile();
    // Fresh off-the-record profile used by private tabs.
    Q_INVOKABLE QQuickWebEngineProfile *createPrivateProfile();

    // Turns typed text into a URL: address, host shortcut or search.
    Q_INVOKABLE QUrl resolveAddress(const QString &text) const;
    // URL when the text looks like an address, empty otherwise.
    Q_INVOKABLE QUrl addressUrl(const QString &text) const;
    // Search URL for the text with the configured engine.
    Q_INVOKABLE QUrl searchUrl(const QString &text) const;

    // Privacy page: "Clear Cookies and Cache Now".
    Q_INVOKABLE void clearCookiesAndCacheNow();

    // Hosts whose certificate error the user accepted. Qt WebEngine remembers
    // the override per profile for its whole lifetime and stops reporting the
    // error, so the tab's security state has to come from this set. It lives
    // in memory only: a private profile's hosts die with the profile.
    void markCertificateOverridden(QQuickWebEngineProfile *profile, const QString &host);
    bool isCertificateOverridden(QQuickWebEngineProfile *profile, const QString &host) const;

    QString homePage() const;

signals:
    void homePageChanged();

private:
    explicit ProfileManager(QObject *parent = nullptr);
    void setupProfile(QQuickWebEngineProfile *profile);
    void applySpellCheckSettings(QQuickWebEngineProfile *profile);
    void applyThirdPartyCookieFilter(QQuickWebEngineProfile *profile);

    QQuickWebEngineProfile *m_defaultProfile = nullptr;
    // Private profiles that are still alive, so download folder changes reach them.
    QList<QQuickWebEngineProfile *> m_privateProfiles;
    // Lower-case hosts with an accepted certificate error, per profile.
    QHash<QQuickWebEngineProfile *, QSet<QString>> m_overriddenCertificateHosts;
};
