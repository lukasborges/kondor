#pragma once

#include <QList>
#include <QString>
#include <QUrl>

struct SessionTab
{
    QUrl url;
    QString title;
};

struct SessionWindow
{
    QList<SessionTab> tabs;
    int currentIndex = 0;
};
