#include "app/startupurl.h"

#include "browser/addressresolver.h"

#include <QDir>
#include <QFileInfo>

QUrl startupUrlForArgument(const QString &argument, const QString &workingDirectory,
                           const QUrl &homePage, const QString &searchTemplate)
{
    const QString input = argument.trimmed();
    if (input.isEmpty())
        return {};

    // A file that exists, absolute or relative to the directory kondor was
    // started from, is a local file even without a scheme or a known extension.
    if (QFileInfo::exists(QDir(workingDirectory).absoluteFilePath(input)))
        return QUrl::fromUserInput(input, workingDirectory, QUrl::AssumeLocalFile);

    // Everything else goes through the same rules as the address bar.
    return resolveAddress(input, homePage, searchTemplate);
}
