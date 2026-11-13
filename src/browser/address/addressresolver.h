#pragma once

#include <QString>
#include <QUrl>

QUrl addressUrl(const QString &text);
QUrl searchUrl(const QString &text, const QString &searchTemplate);
QUrl resolveAddress(const QString &text, const QUrl &homePage, const QString &searchTemplate);
