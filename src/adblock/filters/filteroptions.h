#pragma once

#include "adblock/filters/filterrequest.h"
#include "adblock/filters/filterrule.h"

bool applyFilterOptions(const QString &options, FilterRule &rule);
bool optionsMatch(const FilterRule &rule, const FilterRequest &request);
