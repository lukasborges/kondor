#include "filehelper.h"

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

QString FileHelper::tempPdfPath()
{
    if (!m_tempDir.isValid())
        return QString();
    return m_tempDir.filePath(QStringLiteral("print-%1.pdf").arg(++m_counter));
}

bool FileHelper::openFile(const QString &path)
{
    return QDesktopServices::openUrl(QUrl::fromLocalFile(path));
}
