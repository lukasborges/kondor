#pragma once

#include "adblock/filterrequest.h"
#include "adblock/filterrule.h"

bool applyFilterOptions(const QString &options, FilterRule &rule);
bool optionsMatch(const FilterRule &rule, const FilterRequest &request);
