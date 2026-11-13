#pragma once

#include "extensionsuiharness.h"

class PanelFixture
{
protected:
    void resetPanel();
    void openPanel(const QString &extensionId = QString());
    QQuickItem *rowAt(int index) const;
    QQuickItem *panelItem(const char *name) const;
    QString currentId() const;
    void toggleRunOnSite();

    QTemporaryDir m_work;
    QQmlEngine m_engine;
    std::unique_ptr<Tab> m_tab;
    QScopedPointer<QObject> m_window;
    QObject *m_panel = nullptr;
};

inline void PanelFixture::resetPanel()
{
    m_window.reset();
    m_tab.reset();
    m_engine.rootContext()->setContextProperty(QStringLiteral("theTab"), nullptr);
    removeEveryExtension();
}

inline void PanelFixture::openPanel(const QString &extensionId)
{
    if (ExtensionManager::instance()->count() == 0)
        QVERIFY(installSample(m_work.path()));
    if (!m_tab) {
        m_tab.reset(new Tab(nullptr));
        m_tab->setUrl(QUrl(QStringLiteral("https://www.example.com/page")));
        m_tab->extensionItems()->setChecked(QStringLiteral("sample"), QStringLiteral("toggle"), true);
    }
    m_engine.rootContext()->setContextProperty(QStringLiteral("theTab"), m_tab.get());
    m_window.reset(createInWindow(&m_engine, panelWindowQml));
    QVERIFY(m_window);
    m_panel = childObject(m_window.data(), "panel");
    if (extensionId.isEmpty())
        QMetaObject::invokeMethod(m_panel, "open");
    else
        QMetaObject::invokeMethod(m_panel, "openAt", Q_ARG(QVariant, extensionId));
    QTRY_VERIFY(m_panel->property("opened").toBool());
}

inline QQuickItem *PanelFixture::panelItem(const char *name) const
{
    return findByName(m_window.data(), name);
}

inline QQuickItem *PanelFixture::rowAt(int index) const
{
    QQuickItem *row = nullptr;
    QMetaObject::invokeMethod(panelItem("panelExtensionList"), "itemAtIndex",
                              Q_RETURN_ARG(QQuickItem *, row), Q_ARG(int, index));
    return row;
}

inline QString PanelFixture::currentId() const
{
    return m_panel->property("currentId").toString();
}

inline void PanelFixture::toggleRunOnSite()
{
    clickCenterOf(panelItem("siteSwitch"));
}
