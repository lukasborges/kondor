#include "app/commandline/startupurl.h"

#include "browser/address/addressresolver.h"
#include "core/settings/settings.h"

#include <QDir>
#include <QFileInfo>

namespace {
StartupContext currentStartupContext()
{
    Settings *settings = Settings::instance();
    return {QDir::currentPath(), QUrl(settings->homePage()), settings->searchUrlTemplate()};
}

bool isExistingFile(const QString &input, const QString &workingDirectory)
{
    return QFileInfo::exists(QDir(workingDirectory).absoluteFilePath(input));
}
}

QUrl startupUrlForArgument(const QString &argument, const StartupContext &context)
{
    const QString input = argument.trimmed();
    if (input.isEmpty())
        return {};
    if (isExistingFile(input, context.workingDirectory))
        return QUrl::fromUserInput(input, context.workingDirectory, QUrl::AssumeLocalFile);
    return resolveAddress(input, context.homePage, context.searchTemplate);
}

QList<QUrl> startupUrlsForArguments(const QStringList &arguments)
{
    const StartupContext context = currentStartupContext();
    QList<QUrl> urls;
    for (const QString &argument : arguments) {
        const QUrl url = startupUrlForArgument(argument, context);
        if (!url.isEmpty())
            urls.append(url);
    }
    return urls;
}
