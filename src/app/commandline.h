#pragma once

#include <QList>
#include <QStringList>
#include <QUrl>

class QCoreApplication;

struct CommandLine
{
    QList<QUrl> urls;
    bool isPrivate = false;
    bool newWindow = false;
    bool newInstance = false;
    QStringList extensionDirectories;
};

CommandLine parseCommandLine(const QCoreApplication &app);
