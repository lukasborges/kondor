#pragma once

#include <QString>

struct InstallResult {
    bool isInstalled = false;
    bool needsReview = false;
    QString error;

    bool isRefused() const { return !error.isEmpty(); }
};
