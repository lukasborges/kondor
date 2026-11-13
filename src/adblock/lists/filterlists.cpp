#include "adblock/lists/filterlists.h"

#include <QFile>
#include <QFileInfo>
#include <QStandardPaths>

#include <algorithm>

namespace {
constexpr int kMaxCacheAgeDays = 4;

bool isMissingFromCache(const FilterListSource &list)
{
    return !QFileInfo::exists(filterCachePath(list));
}
}

const QList<FilterListSource> &filterListSources()
{
    static const QList<FilterListSource> all = {
        {QStringLiteral("https://easylist.to/easylist/easylist.txt"), QStringLiteral("easylist.txt")},
        {QStringLiteral("https://easylist.to/easylist/easyprivacy.txt"),
         QStringLiteral("easyprivacy.txt")},
    };
    return all;
}

QString filterCacheDirectory()
{
    return QStandardPaths::writableLocation(QStandardPaths::AppDataLocation)
            + QStringLiteral("/adblock");
}

QString filterCachePath(const FilterListSource &list)
{
    return filterCacheDirectory() + QLatin1Char('/') + list.fileName;
}

QStringList cachedFilterListFiles()
{
    QStringList files;
    for (const FilterListSource &list : filterListSources())
        files.append(filterCachePath(list));
    return files;
}

bool isCacheStale(const QDateTime &lastUpdate)
{
    if (!lastUpdate.isValid() || lastUpdate.daysTo(QDateTime::currentDateTime()) >= kMaxCacheAgeDays)
        return true;
    const QList<FilterListSource> &lists = filterListSources();
    return std::any_of(lists.begin(), lists.end(), isMissingFromCache);
}

std::shared_ptr<const FilterEngine> parseFilterLists(const QStringList &files)
{
    auto engine = std::make_shared<FilterEngine>();
    for (const QString &path : files) {
        QFile file(path);
        if (file.open(QIODevice::ReadOnly))
            engine->addList(file.readAll());
    }
    return engine;
}
