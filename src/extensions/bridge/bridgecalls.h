#pragma once

#include <QString>

#include "browser/tabs/tab.h"
#include "extensions/bridge/extensioncall.h"

struct BridgeContext {
    Tab *tab;
    ExtensionCall call;
};

QString handleBridgeCall(const BridgeContext &context);
