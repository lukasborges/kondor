#pragma once

#include <QString>
#include <QStringList>

#include <optional>

struct FilterRule {
    enum ThirdParty { Any, OnlyThirdParty, OnlyFirstParty };

    QString pattern;
    QString host;
    bool anchorStart = false;
    bool anchorEnd = false;
    bool exception = false;
    int typeMask = 0;
    ThirdParty thirdParty = Any;
    QStringList domainsInclude;
    QStringList domainsExclude;
};

std::optional<FilterRule> parseFilterRule(const QString &line);
