#pragma once

#include <QObject>
#include <QString>
#include <QUrl>
#include <QTemporaryDir>
#include <QtQmlIntegration/qqmlintegration.h>

class QQmlEngine;
class QJSEngine;

class FileHelper : public QObject
{
    Q_OBJECT
    QML_ELEMENT
    QML_SINGLETON

public:
    static FileHelper *instance();
    static FileHelper *create(QQmlEngine *engine, QJSEngine *jsEngine);

    Q_INVOKABLE QString sanitizeFileName(const QString &title) const;
    Q_INVOKABLE QUrl suggestedFileUrl(const QString &directory, const QString &title,
                                      const QString &extension) const;
    Q_INVOKABLE QString tempPdfPath();
    Q_INVOKABLE QString readerResource(const QString &name) const;
    Q_INVOKABLE bool openFile(const QString &path);

private:
    explicit FileHelper(QObject *parent = nullptr);

    QTemporaryDir m_tempDir;
    int m_counter = 0;
};
