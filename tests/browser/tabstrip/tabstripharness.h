#pragma once

#include <QQmlComponent>
#include <QQmlEngine>
#include <QQuickItem>
#include <QQuickWindow>
#include <QTest>

#include "browser/profilemanager.h"
#include "browser/tab.h"
#include "browser/tabmodel.h"
#include "common/qmltesthelpers.h"
#include "core/settings.h"

int runTabStripWidths(int argc, char *argv[]);
int runTabStripClosing(int argc, char *argv[]);
int runTabDrag(int argc, char *argv[]);
int runTabDragScroll(int argc, char *argv[]);
int runTabDragRelease(int argc, char *argv[]);
int runTabStripAccessibility(int argc, char *argv[]);

constexpr int kStripRowY = 18;

struct DragSession
{
    QQuickItem *dragged;
    QPoint press;
    qreal startLeft;
    QList<Tab *> before;
};

class TabStripFixture : public QObject
{
protected:
    void registerTabStripTypes()
    {
        qmlRegisterType<TabModel>("Kondor", 1, 0, "TabModel");
        qmlRegisterUncreatableType<Tab>("Kondor", 1, 0, "Tab",
                                        QStringLiteral("Created by TabModel"));
        registerSingleton<ProfileManager>("ProfileManager");
        registerSingleton<Settings>("Settings");
    }

    void setUpStrip()
    {
        m_tabs = new TabModel;
        m_window = new QQuickWindow;
        m_window->resize(1100, 60);
        m_strip = createStrip();
        m_stubWindow = createStubWindow();
        attachStrip();
    }

    void tearDownStrip()
    {
        delete m_strip;
        delete m_stubWindow;
        delete m_window;
        delete m_tabs;
        m_strip = nullptr;
        m_stubWindow = nullptr;
        m_window = nullptr;
        m_tabs = nullptr;
    }

    void restartStrip()
    {
        tearDownStrip();
        setUpStrip();
    }

    void addTabs(int count)
    {
        for (int i = 0; i < count; ++i)
            m_tabs->addTab();
        QTest::qWait(50);
    }

    void resizeStrip(int width)
    {
        m_strip->setSize(QSizeF(width, 36));
        QTest::qWait(50);
    }

    qreal leftOf(int index) const { return leftOfItem(itemAt(index)); }
    qreal leftOfItem(QQuickItem *item) const { return item->mapToItem(m_strip, QPointF(0, 0)).x(); }
    Tab *tabAt(int i) const
    {
        return m_tabs->data(m_tabs->index(i), TabModel::TabRole).value<Tab *>();
    }
    QList<Tab *> order() const
    {
        QList<Tab *> list;
        for (int i = 0; i < m_tabs->count(); ++i)
            list << tabAt(i);
        return list;
    }
    qreal tabWidth() const { return m_strip->property("tabWidth").toReal(); }
    QQuickItem *itemAt(int index) const
    {
        QQuickItem *item = nullptr;
        QMetaObject::invokeMethod(tabBar(), "itemAt", Q_RETURN_ARG(QQuickItem *, item),
                                  Q_ARG(int, index));
        return item;
    }
    QQuickItem *button(const char *name) const
    {
        return m_strip->property(name).value<QQuickItem *>();
    }
    qreal scrolled() const { return m_strip->property("scrolled").toReal(); }
    QQuickItem *tabBar() const { return m_strip->property("tabBar").value<QQuickItem *>(); }
    QQuickItem *view() const { return tabBar()->property("contentItem").value<QQuickItem *>(); }

    void scrollTo(qreal position)
    {
        QMetaObject::invokeMethod(m_strip, "scrollTo", Q_ARG(QVariant, position));
    }

    void closeWithMouse(Tab *tab)
    {
        QMetaObject::invokeMethod(m_strip, "closeWithMouse",
                                  Q_ARG(QVariant, QVariant::fromValue(tab)));
    }

    DragSession pressOnTab(int index, int offset)
    {
        const qreal left = leftOf(index);
        DragSession session{itemAt(index), QPoint(int(left) + offset, kStripRowY), left, order()};
        QTest::mousePress(m_window, Qt::LeftButton, {}, session.press);
        return session;
    }

    void dragBy(const DragSession &session, int dx)
    {
        const int step = dx < 0 ? -5 : 5;
        for (int d = step; qAbs(d) < qAbs(dx); d += step)
            QTest::mouseMove(m_window, session.press + QPoint(d, 0));
        QTest::mouseMove(m_window, session.press + QPoint(dx, 0));
        QTest::qWait(60);
    }

    void releaseDrag(const DragSession &session, int dx)
    {
        QTest::mouseRelease(m_window, Qt::LeftButton, {}, session.press + QPoint(dx, 0));
    }

    void waitForSlotAnimation(const DragSession &session)
    {
        QTRY_COMPARE(session.dragged->property("dragShift").toReal(), 0.0);
    }

    void verifyDraggedLeftIs(const DragSession &session, qreal expected)
    {
        QVERIFY(qAbs(leftOfItem(session.dragged) - expected) <= 1.0);
    }

    QQmlEngine m_engine;
    QQuickWindow *m_window = nullptr;
    QQuickItem *m_strip = nullptr;
    QObject *m_stubWindow = nullptr;
    TabModel *m_tabs = nullptr;

private:
    QQuickItem *createStrip()
    {
        m_engine.addImportPath(QStringLiteral(KONDOR_QML_IMPORT_DIR));
        QQmlComponent component(&m_engine, QUrl::fromLocalFile(QStringLiteral(
            KONDOR_QML_DIR "/browser/TabStrip.qml")));
        QObject *object = component.createWithInitialProperties(
            { { QStringLiteral("tabModel"), QVariant::fromValue(m_tabs) } });
        if (!object)
            qWarning() << component.errors();
        return qobject_cast<QQuickItem *>(object);
    }

    QObject *createStubWindow()
    {
        QQmlComponent stub(&m_engine);
        stub.setData("import QtQml\nQtObject { property var model\n"
                     "function closeTabFor(t) { model.closeTabObject(t) } }",
                     QUrl());
        return stub.create();
    }

    void attachStrip()
    {
        QVERIFY(m_stubWindow);
        m_stubWindow->setProperty("model", QVariant::fromValue(m_tabs));
        m_strip->setProperty("targetWindow", QVariant::fromValue(m_stubWindow));
        QVERIFY(m_strip);
        m_strip->setParentItem(m_window->contentItem());
        m_strip->setPosition(QPointF(0, 0));
        resizeStrip(1100);
        m_window->show();
        QTest::mouseMove(m_window, QPoint(500, 58));
    }
};
