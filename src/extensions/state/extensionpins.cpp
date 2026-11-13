#include "extensions/state/extensionpins.h"

#include "core/settings/settings.h"

namespace ExtensionPins {

namespace {

QString idOf(const QVariant &entry)
{
    return entry.toMap().value(QStringLiteral("id")).toString();
}

QVariant entryWithId(const QVariantList &entries, const QString &id)
{
    for (const QVariant &entry : entries)
        if (idOf(entry) == id)
            return entry;
    return QVariant();
}

QStringList changedPins(QStringList pins, const QString &id, bool isPinned)
{
    if (isPinned && !pins.contains(id))
        pins.append(id);
    if (!isPinned)
        pins.removeAll(id);
    return pins;
}

}

bool isPinned(const QString &id)
{
    return Settings::instance()->pinnedExtensions().contains(id);
}

void setPinned(const QString &id, bool isPinned)
{
    Settings *settings = Settings::instance();
    settings->setPinnedExtensions(changedPins(settings->pinnedExtensions(), id, isPinned));
}

QVariantList onlyPinned(const QVariantList &entries)
{
    QVariantList pinned;
    for (const QString &id : Settings::instance()->pinnedExtensions()) {
        const QVariant entry = entryWithId(entries, id);
        if (entry.isValid())
            pinned.append(entry);
    }
    return pinned;
}

}
