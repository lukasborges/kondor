#pragma once

#include "adblock/filters/filterengine.h"

#include <QDateTime>
#include <QList>
#include <QString>
#include <QStringList>

#include <memory>

struct FilterListSource {
    QString url;
    QString fileName;
};

const QList<FilterListSource> &filterListSources();
QString filterCacheDirectory();
QString filterCachePath(const FilterListSource &list);
QStringList cachedFilterListFiles();
bool isCacheStale(const QDateTime &lastUpdate);
std::shared_ptr<const FilterEngine> parseFilterLists(const QStringList &files);
