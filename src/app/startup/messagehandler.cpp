#include "app/messagehandler.h"

#include <QByteArray>
#include <QString>
#include <QtLogging>

#include <cstdio>

namespace {
bool isExtensionCategory(const QMessageLogContext &context)
{
    return context.category && qstrcmp(context.category, "kondor.extensions") == 0;
}

bool isSilenced(QtMsgType type, const QMessageLogContext &context)
{
    const bool isChatty = type == QtDebugMsg || type == QtInfoMsg;
    return isChatty && !isExtensionCategory(context);
}

void printToStandardError(QtMsgType type, const QMessageLogContext &context, const QString &message)
{
    if (isSilenced(type, context))
        return;
    std::fprintf(stderr, "%s\n", message.toUtf8().constData());
    std::fflush(stderr);
}
}

void installMessageHandler()
{
    qInstallMessageHandler(printToStandardError);
}
