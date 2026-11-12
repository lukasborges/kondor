#pragma once

#include <QObject>
#include <QStringList>
#include <QtWebEngineCore/qtwebenginecoreglobal.h>

// Extension support needs the Qt 6.10 API; the `webengine_extensions` feature
// alone is already on in 6.8/6.9, where the classes do not exist.
#if QT_VERSION >= QT_VERSION_CHECK(6, 10, 0) && QT_CONFIG(webengine_extensions)
#  define KONDOR_HAVE_EXTENSIONS 1
#else
#  define KONDOR_HAVE_EXTENSIONS 0
#endif

class QQuickWebEngineProfile;

// Developer-only loader for unpacked Chrome extensions (`--load-extension`).
// Uses Qt WebEngine's QWebEngineExtensionManager (Qt 6.10+, only when the
// build has the `webengine_extensions` feature); everywhere else it is a no-op.
// Nothing is installed: extensions live only until Kondor quits.
class ExtensionLoader : public QObject
{
    Q_OBJECT

public:
    explicit ExtensionLoader(QObject *parent = nullptr);

    // True when this Qt WebEngine build can load extensions.
    static bool isSupported();

    // Loads every directory into `profile` and logs one line per result on the
    // "kondor.extensions" category. `profile` must be a normal (persistent)
    // profile: private profiles never get extensions and are refused.
    // Without support, logs a notice and returns.
    void load(QQuickWebEngineProfile *profile, const QStringList &directories);

signals:
    // Emitted once per directory, after the log line was written.
    void loadFinished(const QString &directory, bool loaded);
};
