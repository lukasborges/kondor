#pragma once

#include <QList>
#include <QObject>
#include <functional>
#include <QString>
#include <QUrl>
#include <QtQmlIntegration/qqmlintegration.h>
#include <QQuickWebEngineProfile>

#include "browser/certificateoverrides.h"

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

    Q_INVOKABLE QQuickWebEngineProfile *defaultProfile();
    Q_INVOKABLE QQuickWebEngineProfile *createPrivateProfile();
    Q_INVOKABLE QUrl resolveAddress(const QString &text) const;
    Q_INVOKABLE QUrl addressUrl(const QString &text) const;
    Q_INVOKABLE QUrl searchUrl(const QString &text) const;
    Q_INVOKABLE void clearCookiesAndCacheNow();

    void markCertificateOverridden(QQuickWebEngineProfile *profile, const QString &host);
    bool isCertificateOverridden(QQuickWebEngineProfile *profile, const QString &host) const;

    QString homePage() const;
    QList<QQuickWebEngineProfile *> profiles() const;

signals:
    void homePageChanged();
    void profileCreated(QQuickWebEngineProfile *profile);

private:
    explicit ProfileManager(QObject *parent = nullptr);
    void connectSettings();
    void applyDownloadDirectory();
    void applySpellCheck();
    void clearDataOnExit();
    void setupProfile(QQuickWebEngineProfile *profile);
    QQuickWebEngineProfile *createPersistentProfile();
    void forEachProfile(const std::function<void(QQuickWebEngineProfile *)> &action) const;

    QQuickWebEngineProfile *m_defaultProfile = nullptr;
    QList<QQuickWebEngineProfile *> m_privateProfiles;
    CertificateOverrides m_certificateOverrides;
};
