#pragma once

#include <QString>
#include <QUrl>

// URL for the trimmed text when it looks like an address (explicit scheme,
// about:, data: or a host such as example.com, localhost:8080 or an IP);
// an empty QUrl otherwise.
QUrl addressUrl(const QString &text);

// Search URL for the text, with %1 in the template replaced by the encoded
// query. Always returns a search URL, even for text that looks like a host.
QUrl searchUrl(const QString &text, const QString &searchTemplate);

// Turns typed text into a URL: address, host shortcut or search. Kept free of
// application singletons so it can be tested in isolation.
QUrl resolveAddress(const QString &text, const QUrl &homePage, const QString &searchTemplate);
