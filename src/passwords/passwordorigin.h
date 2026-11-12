#pragma once

#include <QString>
#include <QUrl>

namespace PasswordOrigin {

QString originOf(const QUrl &url);
bool canSaveFor(const QString &origin);
QString originFromInput(const QString &text);
QString hostOfOrigin(const QString &origin);

}
