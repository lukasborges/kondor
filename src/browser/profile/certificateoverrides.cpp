#include "browser/certificateoverrides.h"

void CertificateOverrides::mark(QQuickWebEngineProfile *profile, const QString &host)
{
    if (!profile || host.isEmpty())
        return;
    m_hostsByProfile[profile].insert(host.toLower());
}

bool CertificateOverrides::isOverridden(QQuickWebEngineProfile *profile, const QString &host) const
{
    if (!profile || host.isEmpty())
        return false;
    return m_hostsByProfile.value(profile).contains(host.toLower());
}

void CertificateOverrides::forget(QQuickWebEngineProfile *profile)
{
    m_hostsByProfile.remove(profile);
}
