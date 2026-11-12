#pragma once

#include "browser/sessionwindow.h"

#include <QByteArray>
#include <QList>

namespace SessionFormat {

QByteArray toJson(const QList<SessionWindow> &windows);
QList<SessionWindow> fromJson(const QByteArray &json);

}
