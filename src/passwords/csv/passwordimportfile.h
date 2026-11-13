#pragma once

#include <QByteArray>
#include <QString>
#include <QUrl>

struct ImportFile
{
    QByteArray data;
    QString error;
};

ImportFile readImportFile(const QUrl &file);
