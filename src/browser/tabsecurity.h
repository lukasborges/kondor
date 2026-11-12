#pragma once

#include <QObject>
#include <QString>
#include <QUrl>
#include <QtQmlIntegration/qqmlintegration.h>

class QQuickWebEngineProfile;

struct CertificateError
{
    QUrl url;
    QString description;
    bool overridable = false;

    bool operator==(const CertificateError &other) const
    {
        return url == other.url && description == other.description
                && overridable == other.overridable;
    }
};

class TabSecurity : public QObject
{
    Q_OBJECT
    QML_ELEMENT
    QML_UNCREATABLE("Owned by Tab")

    Q_PROPERTY(QString state READ state NOTIFY stateChanged)
    Q_PROPERTY(bool certificateErrorPending READ certificateErrorPending NOTIFY certificateErrorChanged)
    Q_PROPERTY(QUrl certificateErrorUrl READ certificateErrorUrl NOTIFY certificateErrorChanged)
    Q_PROPERTY(QString certificateErrorDescription READ certificateErrorDescription NOTIFY certificateErrorChanged)
    Q_PROPERTY(bool certificateErrorOverridable READ certificateErrorOverridable NOTIFY certificateErrorChanged)

public:
    explicit TabSecurity(QQuickWebEngineProfile *profile, QObject *parent = nullptr);

    QString state() const { return m_state; }
    bool certificateErrorPending() const { return m_pending; }
    QUrl certificateErrorUrl() const { return m_error.url; }
    QString certificateErrorDescription() const { return m_error.description; }
    bool certificateErrorOverridable() const { return m_error.overridable; }

    void updateFor(const QUrl &url);
    void clearPendingCertificateError();
    Q_INVOKABLE void setPendingCertificateError(const QUrl &url, const QString &description,
                                                bool overridable);
    Q_INVOKABLE void acceptCertificateError();
    Q_INVOKABLE void rejectCertificateError();

signals:
    void stateChanged();
    void certificateErrorChanged();
    void acceptCertificateErrorRequested();
    void rejectCertificateErrorRequested();

private:
    QString computeState() const;
    bool hasCertificateOverride() const;
    void refreshState();
    void markCertificateOverridden();

    QQuickWebEngineProfile *m_profile = nullptr;
    QUrl m_url;
    QString m_state = QStringLiteral("local");
    bool m_pending = false;
    CertificateError m_error;
};
