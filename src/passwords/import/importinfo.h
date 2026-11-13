#pragma once

#include <QUrl>
#include <QVariantMap>

#include "passwords/csv/passwordimport.h"
#include "passwords/csv/passwordimportplan.h"

QVariantMap importFailure(const QUrl &file, const QString &error);

QString importErrorName(PasswordImport::Error error);

QVariantMap importResult(const QUrl &file, const PasswordImport::Result &parsed,
                         const ImportSummary &summary);
