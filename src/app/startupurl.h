#pragma once

#include <QString>
#include <QUrl>

// Converts one command-line argument into the URL a tab should open. Existing
// files (absolute or relative to workingDirectory) become file URLs; everything
// else follows the address bar rules: an explicit URL or host opens directly,
// free text becomes a search.
QUrl startupUrlForArgument(const QString &argument, const QString &workingDirectory,
                           const QUrl &homePage, const QString &searchTemplate);
