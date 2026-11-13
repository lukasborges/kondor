#pragma once

#include <QByteArray>
#include <QList>
#include <QMetaType>
#include <QUrl>

struct SingleInstanceMessage
{
    QList<QUrl> urls;
    bool privateMode = false;
    bool newWindow = false;
    QByteArray activationToken;

    QByteArray toJsonLine() const;
    static SingleInstanceMessage fromJsonLine(const QByteArray &line);
};

Q_DECLARE_METATYPE(SingleInstanceMessage)
