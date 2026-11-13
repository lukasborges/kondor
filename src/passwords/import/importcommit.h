#pragma once

#include <QMap>
#include <QObject>
#include <QStringList>

#include <functional>

#include "passwords/import/pendingimport.h"

class ImportCommit : public QObject
{
    Q_OBJECT

public:
    using Writer = std::function<bool(const QString &, const QMap<QString, QString> &)>;

    ImportCommit(PendingImport pending, Writer write, QObject *parent = nullptr);

    void start();
    int total() const { return m_origins.size(); }
    int done() const { return m_done; }

signals:
    void progressed();
    void finished(int written);

private:
    void writeNextOrigin();
    int mergeOrigin(const QString &origin);
    void scheduleNext();

    QMap<QString, QList<PasswordImport::Login>> m_byOrigin;
    QStringList m_origins;
    SavedLogins m_saved;
    bool m_replaceConflicts;
    Writer m_write;
    int m_done = 0;
    int m_written = 0;
};
