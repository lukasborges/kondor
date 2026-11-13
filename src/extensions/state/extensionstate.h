#pragma once

#include <QSettings>
#include <QString>
#include <QStringList>
#include <QVariant>

class ExtensionState
{
public:
    ExtensionState();

    bool isEnabled(const QString &id) const;
    void setEnabled(const QString &id, bool isEnabled);
    bool isPrivateAllowed(const QString &id) const;
    void setPrivateAllowed(const QString &id, bool isAllowed);
    QString source(const QString &id) const;
    void setSource(const QString &id, const QString &source);
    QStringList disabledSites(const QString &id) const;
    void setDisabledSites(const QString &id, const QStringList &sites);
    bool hasSetting(const QString &id, const QString &key) const;
    QVariant setting(const QString &id, const QString &key) const;
    void setSetting(const QString &id, const QString &key, const QVariant &value);
    void removeExtension(const QString &id);
    void sync();

private:
    static QString keyOf(const QString &id, const QString &name);

    mutable QSettings m_settings;
};
