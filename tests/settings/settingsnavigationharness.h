#pragma once

#include "settingswindowharness.h"

inline QObject *childOf(QQuickWindow *window, const char *objectName)
{
    return window->findChild<QObject *>(QString::fromLatin1(objectName));
}

inline int visiblePageCount(QQuickWindow *window)
{
    QObject *list = childOf(window, "pageList");
    return list ? list->property("count").toInt() : -1;
}

inline QQuickItem *sidebarEntry(QQuickWindow *window, int index)
{
    QQuickItem *entry = nullptr;
    QMetaObject::invokeMethod(childOf(window, "pageList"), "itemAtIndex", Q_RETURN_ARG(QQuickItem *, entry),
                              Q_ARG(int, index));
    return entry;
}

inline QPoint entryCenter(QQuickItem *entry)
{
    return entry->mapToScene(QPointF(entry->width() / 2, entry->height() / 2)).toPoint();
}

inline void typeText(QQuickWindow *window, const QString &text)
{
    for (const QChar character : text)
        QTest::keyClick(window, character.toLatin1());
}

inline void searchFor(QQuickWindow *window, const QString &text)
{
    QTest::keyClick(window, Qt::Key_A, Qt::ControlModifier);
    QTest::keyClick(window, Qt::Key_Delete);
    typeText(window, text);
}

inline void verifySidebarHighlights(QQuickWindow *window, int page)
{
    for (int i = 0; i < 4; ++i) {
        QQuickItem *entry = sidebarEntry(window, i);
        QVERIFY(entry);
        QCOMPARE(entry->property("highlighted").toBool(), i == page);
    }
}

inline void verifyShownPage(QQuickWindow *window, int page, const QString &title)
{
    QCOMPARE(window->property("currentPage").toInt(), page);
    QObject *heading = childOf(window, "pageHeading");
    QVERIFY(heading);
    QCOMPARE(heading->property("text").toString(), title);
    QObject *stack = childOf(window, "pageStack");
    QVERIFY(stack);
    QCOMPARE(stack->property("currentIndex").toInt(), page);
    QObject *list = childOf(window, "pageList");
    QVERIFY(list);
    QCOMPARE(list->property("currentIndex").toInt(), page);
    verifySidebarHighlights(window, page);
}

inline void verifyOnlyPageIsListed(QQuickWindow *window, int page, const QString &title)
{
    QTRY_COMPARE(visiblePageCount(window), 1);
    QCOMPARE(window->property("currentPage").toInt(), page);
    QCOMPARE(childOf(window, "pageHeading")->property("text").toString(), title);
}

inline void clickSidebarEntryAndVerify(QQuickWindow *window, int page, const QString &title)
{
    QQuickItem *entry = nullptr;
    QTRY_VERIFY((entry = sidebarEntry(window, page)));
    QTest::mouseClick(window, Qt::LeftButton, Qt::NoModifier, entryCenter(entry));
    QTRY_COMPARE(window->property("currentPage").toInt(), page);
    verifyShownPage(window, page, title);
}

inline void verifyPrivacyIsTheOnlyEntry(QQuickWindow *window)
{
    verifyOnlyPageIsListed(window, 3, QStringLiteral("Privacy"));
    QCOMPARE(childOf(window, "pageStack")->property("currentIndex").toInt(), 3);
    QQuickItem *privacy = nullptr;
    QTRY_VERIFY((privacy = sidebarEntry(window, 0)));
    QCOMPARE(privacy->property("text").toString(), QStringLiteral("Privacy"));
    QVERIFY(privacy->property("highlighted").toBool());
    QVERIFY(!sidebarEntry(window, 1));
}

inline bool focusSearchField(QQuickWindow *window)
{
    auto *searchItem = qobject_cast<QQuickItem *>(findByClassName(window, QStringLiteral("SearchField")));
    if (searchItem)
        searchItem->forceActiveFocus();
    return searchItem;
}
