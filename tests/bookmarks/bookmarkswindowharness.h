#pragma once

#include <QJSEngine>
#include <QQmlComponent>
#include <QQmlEngine>
#include <QQuickImageProvider>
#include <QQuickItem>
#include <QQuickWindow>
#include <QTest>

#include <functional>

#include "common/qmltesthelpers.h"
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

inline void registerKondorTypes(QQmlEngine &engine)
{
    static const bool typesRegistered = [] {
        qmlRegisterType<TabModel>("Kondor", 1, 0, "TabModel");
        registerSingleton<BookmarkManager>("BookmarkManager");
        registerSingleton<FaviconStore>("FaviconStore");
        registerSingleton<ProfileManager>("ProfileManager");
        return true;
    }();
    Q_UNUSED(typesRegistered)
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

class BookmarksWindowFixture
{
public:
    BookmarksWindowFixture(QQmlEngine &engine, qint64 folderId)
        : m_window(createBookmarksWindow(engine, &m_model, folderId))
    {
    }

    QQuickWindow *window() const { return m_window.data(); }

    bool show()
    {
        m_window->show();
        return QTest::qWaitForWindowExposed(m_window.data());
    }

private:
    TabModel m_model;
    QScopedPointer<QQuickWindow> m_window;
};

inline QQuickItem *waitForRow(QQuickWindow *window, const char *listName, int index)
{
    QQuickItem *row = nullptr;
    const bool found = QTest::qWaitFor([&] { return (row = rowAt(window, listName, index)) != nullptr; }, 5000);
    return found ? row : nullptr;
}

inline qint64 addBookmarkTo(qint64 folderId, const QString &title, const QString &url)
{
    return BookmarkManager::instance()->addBookmark(QUrl(url), title, folderId);
}

inline qint64 parentIdOf(qint64 id)
{
    return BookmarkManager::instance()->bookmark(id).value(QStringLiteral("parentId")).toLongLong();
}

inline bool previewShows(QQuickWindow *window, const QString &title)
{
    const bool shown = childNamed(window, "dragProxy")->property("visible").toBool();
    QObject *label = childNamed(window, "dragPreviewTitle");
    return shown && label && label->property("text").toString() == title;
}

inline bool previewHidden(QQuickWindow *window)
{
    return !childNamed(window, "dragProxy")->property("visible").toBool();
}

struct DragPath
{
    QPoint from;
    QPoint to;
};

inline bool dragShowingPreview(QQuickWindow *window, const DragPath &path, const QString &title)
{
    bool previewShown = false;
    dragWithButtonDown(window, path.from, path.to, [&]() { previewShown = previewShows(window, title); });
    return previewShown;
}

inline QPoint justInsideTopEdge(QQuickItem *row)
{
    const QPoint edge = row->mapToScene(QPointF(row->width() / 2, 2)).toPoint();
    return QPoint(edge.x(), edge.y() + 1);
}

int runTestBookmarksWindowDrag(int argc, char *argv[]);
