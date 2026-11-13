#pragma once

#include <QByteArray>
#include <QList>
#include <QStringList>

QList<QStringList> readCsvRows(const QByteArray &data);
