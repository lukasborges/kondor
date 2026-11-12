#pragma once

#include <QJSEngine>
#include <QQmlComponent>
#include <QQmlEngine>
#include <QQuickImageProvider>
#include <QQuickItem>
#include <QQuickWindow>
#include <QTest>

#include <functional>

#include "bookmarks/bookmarkmanager.h"
#include "browser/faviconstore.h"
#include "browser/profilemanager.h"
#include "browser/tabmodel.h"

class EmptyImageProvider : public QQuickImageProvider
{
public:
    EmptyImageProvider()
        : QQuickImageProvider(QQuickImageProvider::Image)
    {
    }

    QImage requestImage(const QString &, QSize *size, const QSize &) override
    {
        QImage image(1, 1, QImage::Format_ARGB32);
        image.fill(Qt::transparent);
        if (size)
            *size = image.size();
        return image;
    }
};

template<typename T>
void registerSingleton(const char *name)
{
    qmlRegisterSingletonType<T>("Kondor", 1, 0, name,
                                [](QQmlEngine *, QJSEngine *) -> QObject * { return T::instance(); });
}

inline void registerKondorTypes(QQmlEngine &engine)
{
    qmlRegisterType<TabModel>("Kondor", 1, 0, "TabModel");
    registerSingleton<BookmarkManager>("BookmarkManager");
    registerSingleton<FaviconStore>("FaviconStore");
    registerSingleton<ProfileManager>("ProfileManager");
    engine.addImageProvider(QStringLiteral("kondor-favicon"), new EmptyImageProvider);
}

inline QQuickWindow *createBookmarksWindow(QQmlEngine &engine, TabModel *tabs, qint64 folderId)
{
    engine.addImportPath(QStringLiteral(KONDOR_QML_IMPORT_DIR));
    QQmlComponent component(&engine, QUrl::fromLocalFile(QStringLiteral(KONDOR_QML_DIR
                                                                       "/bookmarks/BookmarksWindow.qml")));
    QObject *object = component.createWithInitialProperties({
        {QStringLiteral("tabModel"), QVariant::fromValue(tabs)},
        {QStringLiteral("selectedFolderId"), QVariant::fromValue(folderId)},
    });
    if (!object)
        qWarning() << component.errors();
    auto *window = qobject_cast<QQuickWindow *>(object);
    if (object && !window)
        delete object;
    if (window)
        window->resize(820, 540);
    return window;
}

inline QObject *childNamed(QQuickWindow *window, const char *objectName)
{
    return window->findChild<QObject *>(QString::fromLatin1(objectName));
}

inline QQuickItem *rowAt(QQuickWindow *window, const char *listName, int index)
{
    QQuickItem *row = nullptr;
    QMetaObject::invokeMethod(childNamed(window, listName), "itemAtIndex",
                              Q_RETURN_ARG(QQuickItem *, row), Q_ARG(int, index));
    return row;
}

inline QPoint rowCenter(QQuickItem *row)
{
    return row->mapToScene(QPointF(row->width() / 2, row->height() / 2)).toPoint();
}

inline int folderRowOf(qint64 folderId)
{
    const QVariantList folders = BookmarkManager::instance()->folders();
    for (int i = 0; i < folders.size(); ++i) {
        if (folders.at(i).toMap().value(QStringLiteral("id")).toLongLong() == folderId)
            return i;
    }
    return -1;
}

inline void dragWithButtonDown(QQuickWindow *window, const QPoint &from, const QPoint &to,
                               const std::function<void()> &duringDrag = {})
{
    QTest::mousePress(window, Qt::LeftButton, Qt::NoModifier, from);
    const int steps = 12;
    for (int i = 1; i <= steps; ++i)
        QTest::mouseMove(window, from + (to - from) * i / steps);
    if (duringDrag)
        duringDrag();
    QTest::mouseRelease(window, Qt::LeftButton, Qt::NoModifier, to);
    QTest::qWait(100);
}

inline QStringList menuTitles(QObject *menu)
{
    QStringList titles;
    for (int i = 0; i < menu->property("count").toInt(); ++i) {
        QQuickItem *item = nullptr;
        QMetaObject::invokeMethod(menu, "itemAt", Q_RETURN_ARG(QQuickItem *, item), Q_ARG(int, i));
        titles << item->property("text").toString();
    }
    return titles;
}
