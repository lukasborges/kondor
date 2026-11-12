#pragma once

#include <QString>
#include <QVariantList>

namespace HistorySearch {

QVariantList suggest(const QString &text, int limit);
QVariantList recentToday(int limit);
QString hostCompletion(const QString &text);
QString likePattern(const QString &term);

}
