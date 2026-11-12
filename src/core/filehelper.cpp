#include "filehelper.h"

#include <QFile>
#include <QStringList>

#include <QDesktopServices>
#include <QDir>
#include <QUrl>

FileHelper::FileHelper(QObject *parent)
    : QObject(parent)
    , m_tempDir(QDir::tempPath() + QStringLiteral("/kondor-print-XXXXXX"))
{
}

FileHelper *FileHelper::instance()
{
    static FileHelper *self = new FileHelper();
    return self;
}

FileHelper *FileHelper::create(QQmlEngine *, QJSEngine *)
{
    return instance();
}

QString FileHelper::sanitizeFileName(const QString &title) const
{
    QString name = title.trimmed();
    for (QChar &c : name) {
        if (QStringLiteral("/\\:*?\"<>|").contains(c) || c.unicode() < 0x20)
            c = QLatin1Char('_');
    }
    name = name.left(100).trimmed();
    return name.isEmpty() ? QStringLiteral("page") : name;
}

QUrl FileHelper::suggestedFileUrl(const QString &directory, const QString &title,
                                  const QString &extension) const
{
    return QUrl::fromLocalFile(QDir(directory).filePath(sanitizeFileName(title) + extension));
}

QString FileHelper::tempPdfPath()
{
    if (!m_tempDir.isValid())
        return QString();
    return m_tempDir.filePath(QStringLiteral("print-%1.pdf").arg(++m_counter));
}

QString FileHelper::readerResource(const QString &name) const
{
    static const QStringList allowed{QStringLiteral("Readability.js"),
                                     QStringLiteral("Readability-readerable.js"),
                                     QStringLiteral("template.html")};
    if (!allowed.contains(name))
        return QString();
    QFile file(QStringLiteral(":/reader/") + name);
    if (!file.open(QIODevice::ReadOnly))
        return QString();
    return QString::fromUtf8(file.readAll());
}

bool FileHelper::openFile(const QString &path)
{
    return QDesktopServices::openUrl(QUrl::fromLocalFile(path));
}
