#pragma once

#include <QString>
#include <QUrl>

// Turns typed text into a URL: address, host shortcut or search. Kept free of
// application singletons so it can be tested in isolation.
QUrl resolveAddress(const QString &text, const QUrl &homePage, const QString &searchTemplate);
