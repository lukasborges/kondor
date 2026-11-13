#pragma once

#include <QHash>
#include <QSet>
#include <QString>

class QQuickWebEngineProfile;

class CertificateOverrides
{
public:
    void mark(QQuickWebEngineProfile *profile, const QString &host);
    bool isOverridden(QQuickWebEngineProfile *profile, const QString &host) const;
    void forget(QQuickWebEngineProfile *profile);

private:
    QHash<QQuickWebEngineProfile *, QSet<QString>> m_hostsByProfile;
};
