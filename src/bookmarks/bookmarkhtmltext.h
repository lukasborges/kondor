#pragma once

#include <QString>

namespace BookmarkHtmlText {

QString decodeEntities(QString text);
QString cleanTitle(QString text);
QString attributeValue(const QString &tag, const QString &name);

}
