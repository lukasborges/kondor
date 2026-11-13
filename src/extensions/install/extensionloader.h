#pragma once

#include <QHash>
#include <QObject>
#include <QStringList>
#include <QtWebEngineCore/qtwebenginecoreglobal.h>

#if QT_VERSION >= QT_VERSION_CHECK(6, 10, 0) && QT_CONFIG(webengine_extensions)
#  define KONDOR_HAVE_EXTENSIONS 1
#else
#  define KONDOR_HAVE_EXTENSIONS 0
#endif

class QQuickWebEngineProfile;
class QWebEngineExtensionInfo;
class QWebEngineExtensionManager;

class ExtensionLoader : public QObject
{
    Q_OBJECT

public:
    explicit ExtensionLoader(QObject *parent = nullptr);

    static bool isSupported();

    void load(QQuickWebEngineProfile *profile, const QStringList &directories);

signals:
    void loadFinished(const QString &directory, bool loaded);

private:
    void loadInto(QQuickWebEngineProfile *profile, const QStringList &directories);
#if KONDOR_HAVE_EXTENSIONS
    void handleLoadFinished(const QWebEngineExtensionInfo &info,
                            const QHash<QString, QString> &requested,
                            QWebEngineExtensionManager *manager);
#endif
};
