#pragma once

#include "adblock/filters/filterengine.h"

#include <QString>
#include <QUrl>

struct FilterRequest {
    QString url;
    QString rest;
    QString host;
    QString firstPartyHost;
    bool thirdParty = false;
    int kind = 0;
};

FilterRequest makeFilterRequest(const QUrl &url, const QString &firstPartyHost,
                                FilterEngine::ResourceKind kind);
