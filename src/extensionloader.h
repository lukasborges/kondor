#pragma once

#include <QObject>
#include <QStringList>

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
