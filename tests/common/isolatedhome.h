#pragma once

#include <QByteArray>
#include <QTemporaryDir>

inline bool useIsolatedHome(const QTemporaryDir &home)
{
    if (!home.isValid())
        return false;
    const QByteArray path = home.path().toUtf8();
    qputenv("XDG_DATA_HOME", path);
    qputenv("XDG_CONFIG_HOME", path);
    qputenv("XDG_CACHE_HOME", path);
    return true;
}
