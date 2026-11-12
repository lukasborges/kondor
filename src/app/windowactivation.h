#pragma once

#include <QByteArray>

class QObject;

void raiseWindow(QObject *window, const QByteArray &activationToken);
