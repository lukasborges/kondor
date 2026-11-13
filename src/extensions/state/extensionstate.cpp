#include "extensions/state/extensionstate.h"

ExtensionState::ExtensionState()
    : m_settings(QStringLiteral("KDE"), QStringLiteral("Kondor"))
{
}

QString ExtensionState::keyOf(const QString &id, const QString &name)
{
    return QStringLiteral("Extensions/%1/%2").arg(id, name);
}

bool ExtensionState::isEnabled(const QString &id) const
{
    return m_settings.value(keyOf(id, QStringLiteral("Enabled")), true).toBool();
}

void ExtensionState::setEnabled(const QString &id, bool isEnabled)
{
    m_settings.setValue(keyOf(id, QStringLiteral("Enabled")), isEnabled);
}

bool ExtensionState::isPrivateAllowed(const QString &id) const
{
    return m_settings.value(keyOf(id, QStringLiteral("PrivateAllowed")), false).toBool();
}

void ExtensionState::setPrivateAllowed(const QString &id, bool isAllowed)
{
    m_settings.setValue(keyOf(id, QStringLiteral("PrivateAllowed")), isAllowed);
}

QString ExtensionState::source(const QString &id) const
{
    return m_settings.value(keyOf(id, QStringLiteral("Source")), QStringLiteral("file")).toString();
}

void ExtensionState::setSource(const QString &id, const QString &source)
{
    m_settings.setValue(keyOf(id, QStringLiteral("Source")), source);
}

QStringList ExtensionState::disabledSites(const QString &id) const
{
    return m_settings.value(keyOf(id, QStringLiteral("DisabledSites"))).toStringList();
}

void ExtensionState::setDisabledSites(const QString &id, const QStringList &sites)
{
    const QString key = keyOf(id, QStringLiteral("DisabledSites"));
    if (sites.isEmpty())
        m_settings.remove(key);
    else
        m_settings.setValue(key, sites);
}

bool ExtensionState::hasSetting(const QString &id, const QString &key) const
{
    return m_settings.contains(keyOf(id, QStringLiteral("Settings/") + key));
}

QVariant ExtensionState::setting(const QString &id, const QString &key) const
{
    return m_settings.value(keyOf(id, QStringLiteral("Settings/") + key));
}

void ExtensionState::setSetting(const QString &id, const QString &key, const QVariant &value)
{
    m_settings.setValue(keyOf(id, QStringLiteral("Settings/") + key), value);
}

void ExtensionState::removeExtension(const QString &id)
{
    m_settings.remove(QStringLiteral("Extensions/%1").arg(id));
}

void ExtensionState::sync()
{
    m_settings.sync();
}
