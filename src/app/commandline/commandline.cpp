#include "app/commandline/commandline.h"

#include "app/commandline/startupurl.h"

#include <QCommandLineOption>
#include <QCommandLineParser>

namespace {
void addFlag(QCommandLineParser &parser, const QString &name, const QString &description)
{
    parser.addOption(QCommandLineOption(name, description));
}

void addExtensionOption(QCommandLineParser &parser)
{
    parser.addOption(QCommandLineOption(
        QStringLiteral("load-extension"),
        QStringLiteral("Load an unpacked extension (developer option). Repeatable; "
                       "not forwarded to a running instance, use with --new-instance"),
        QStringLiteral("dir")));
}

void addFlags(QCommandLineParser &parser)
{
    addFlag(parser, QStringLiteral("private"), QStringLiteral("open URLs in a private tab"));
    addFlag(parser, QStringLiteral("new-window"),
            QStringLiteral("open the URLs in a new window of the running instance"));
    addFlag(parser, QStringLiteral("new-instance"),
            QStringLiteral("start a separate process instead of reusing the running one"));
}

void describe(QCommandLineParser &parser)
{
    parser.setApplicationDescription(QStringLiteral("Kondor web browser"));
    parser.addHelpOption();
    parser.addVersionOption();
    addFlags(parser);
    addExtensionOption(parser);
    parser.addPositionalArgument(QStringLiteral("urls"),
                                 QStringLiteral("URLs or files to open"),
                                 QStringLiteral("[urls...]"));
}

CommandLine read(const QCommandLineParser &parser)
{
    CommandLine commandLine;
    commandLine.urls = startupUrlsForArguments(parser.positionalArguments());
    commandLine.isPrivate = parser.isSet(QStringLiteral("private"));
    commandLine.newWindow = parser.isSet(QStringLiteral("new-window"));
    commandLine.newInstance = parser.isSet(QStringLiteral("new-instance"));
    commandLine.extensionDirectories = parser.values(QStringLiteral("load-extension"));
    return commandLine;
}
}

CommandLine parseCommandLine(const QCoreApplication &app)
{
    QCommandLineParser parser;
    describe(parser);
    parser.process(app);
    return read(parser);
}
