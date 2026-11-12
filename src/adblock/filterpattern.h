#pragma once

#include "adblock/filterrequest.h"
#include "adblock/filterrule.h"

#include <QSet>

bool matchesPattern(const FilterRule &rule, const QString &text, bool isUnanchoredSearch);
int matchSegmentAt(const QString &segment, const QString &text, int position);
QString tokenOf(const QString &pattern, bool anchorStart, bool anchorEnd);
QSet<QString> urlTokens(const QString &url);
QString registrableDomain(const QString &host);
bool hostMatches(const QString &host, const QString &domain);
