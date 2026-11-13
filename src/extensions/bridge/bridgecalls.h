#pragma once

#include <QString>

#include "browser/tab.h"
#include "extensions/extensioncall.h"

struct BridgeContext {
    Tab *tab;
    ExtensionCall call;
};

QString handleBridgeCall(const BridgeContext &context);
