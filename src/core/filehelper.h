#pragma once

#include <QObject>
#include <QString>
#include <QUrl>
#include <QTemporaryDir>
#include <QtQmlIntegration/qqmlintegration.h>

class QQmlEngine;
class QJSEngine;

// QML singleton `FileHelper`: small file utilities for printing and saving
// pages (suggested file names, temporary PDFs, opening a file).
class FileHelper : public QObject
{
    Q_OBJECT
    QML_ELEMENT
    QML_SINGLETON

public:
    static FileHelper *instance();
    static FileHelper *create(QQmlEngine *engine, QJSEngine *jsEngine);

    // A page title turned into a safe file name stem: `/\:*?"<>|` become `_`,
    // at most 100 characters, "page" when nothing is left.
    Q_INVOKABLE QString sanitizeFileName(const QString &title) const;
    // The file URL (built with QUrl::fromLocalFile, so `#`, `%` and spaces
    // survive) for `directory`/<sanitized title><extension>.
    Q_INVOKABLE QUrl suggestedFileUrl(const QString &directory, const QString &title,
                                      const QString &extension) const;
    // A fresh path for a temporary PDF; the folder is removed when Kondor quits.
    Q_INVOKABLE QString tempPdfPath();
    // Text of a file bundled under qrc:/reader/ (Readability and the template).
    Q_INVOKABLE QString readerResource(const QString &name) const;
    // Opens a local file with the default application.
    Q_INVOKABLE bool openFile(const QString &path);

private:
    explicit FileHelper(QObject *parent = nullptr);

    QTemporaryDir m_tempDir;
    int m_counter = 0;
};
