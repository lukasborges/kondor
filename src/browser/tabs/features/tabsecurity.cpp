#include "browser/tabs/features/tabsecurity.h"

#include "browser/tabs/assignandnotify.h"
#include "browser/profile/profilemanager.h"

TabSecurity::TabSecurity(QQuickWebEngineProfile *profile, QObject *parent)
    : QObject(parent)
    , m_profile(profile)
{
}

void TabSecurity::updateFor(const QUrl &url)
{
    m_url = url;
    refreshState();
}

void TabSecurity::refreshState()
{
    assignAndNotify(m_state, computeState(), [this] { emit stateChanged(); });
}

QString TabSecurity::computeState() const
{
    const QString scheme = m_url.scheme().toLower();
    if (m_pending)
        return QStringLiteral("error");
    if (scheme == QLatin1String("https"))
        return hasCertificateOverride() ? QStringLiteral("error") : QStringLiteral("secure");
    if (scheme == QLatin1String("http"))
        return QStringLiteral("insecure");
    return QStringLiteral("local");
}

bool TabSecurity::hasCertificateOverride() const
{
    return ProfileManager::instance()->isCertificateOverridden(m_profile, m_url.host());
}

void TabSecurity::setPendingCertificateError(const QUrl &url, const QString &description,
                                             bool overridable)
{
    const CertificateError error{url, description, overridable};
    if (m_pending && m_error == error)
        return;
    m_pending = true;
    m_error = error;
    refreshState();
    emit certificateErrorChanged();
}

void TabSecurity::clearPendingCertificateError()
{
    if (!m_pending)
        return;
    m_pending = false;
    m_error = CertificateError();
    refreshState();
    emit certificateErrorChanged();
}

void TabSecurity::markCertificateOverridden()
{
    const QString errorHost = m_error.url.host();
    ProfileManager::instance()->markCertificateOverridden(
            m_profile, errorHost.isEmpty() ? m_url.host() : errorHost);
}

void TabSecurity::acceptCertificateError()
{
    if (!m_pending)
        return;
    markCertificateOverridden();
    clearPendingCertificateError();
    emit acceptCertificateErrorRequested();
}

void TabSecurity::rejectCertificateError()
{
    if (!m_pending)
        return;
    clearPendingCertificateError();
    emit rejectCertificateErrorRequested();
}
