#pragma once

#include <QList>
#include <QString>
#include <QStringList>
#include <QUrl>

struct StartupContext
{
    QString workingDirectory;
    QUrl homePage;
    QString searchTemplate;
};

QUrl startupUrlForArgument(const QString &argument, const StartupContext &context);
QList<QUrl> startupUrlsForArguments(const QStringList &arguments);
