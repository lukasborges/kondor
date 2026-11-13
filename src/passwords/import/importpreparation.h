#pragma once

#include <QFutureWatcher>
#include <QObject>
#include <QUrl>
#include <QVariantMap>

#include <functional>
#include <optional>

#include "passwords/import/pendingimport.h"

struct ParsedImport
{
    QString error;
    PasswordImport::Result parsed;
};

class ImportPreparation : public QObject
{
    Q_OBJECT

public:
    using SavedLoginsSource = std::function<std::optional<SavedLogins>()>;

    explicit ImportPreparation(SavedLoginsSource savedLogins, QObject *parent = nullptr);

    void start(const QUrl &file);
    void cancel();
    bool isRunning() const { return m_watcher.isRunning(); }
    PendingImport takePending();

signals:
    void prepared(const QVariantMap &info);
    void runningChanged();

private:
    void finish();
    QVariantMap describe(const ParsedImport &source);

    SavedLoginsSource m_savedLogins;
    QFutureWatcher<ParsedImport> m_watcher;
    QUrl m_file;
    PendingImport m_pending;
};
