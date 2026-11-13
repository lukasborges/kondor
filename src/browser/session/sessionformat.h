#pragma once

#include "browser/session/sessionwindow.h"

#include <QByteArray>
#include <QList>

namespace SessionFormat {

QByteArray toJson(const QList<SessionWindow> &windows);
QList<SessionWindow> fromJson(const QByteArray &json);

}
