#pragma once

#include <QQmlComponent>
#include <QQmlContext>
#include <QQmlEngine>
#include <QQuickItem>
#include <QQuickWebEngineProfile>
#include <QQuickWindow>
#include <QtTest>

#include "extensionsharness.h"

inline QObject *createInWindow(QQmlEngine *engine, const QByteArray &source)
{
    engine->addImportPath(QStringLiteral(KONDOR_QML_IMPORT_DIR));
    QQmlComponent component(engine);
    component.setData(source, QUrl::fromLocalFile(QStringLiteral(KONDOR_QML_DIR "/Host.qml")));
    QObject *object = component.create();
    if (!object)
        qWarning() << component.errors();
    return object;
}

inline QObject *childObject(QObject *window, const char *name)
{
    return window->property(name).value<QObject *>();
}

inline QVariantList rebuiltEntries(QObject *menu)
{
    QMetaObject::invokeMethod(menu, "rebuild");
    return menu->property("entries").toList();
}

inline QString textOf(const QVariant &entry, const QString &key)
{
    return entry.toMap().value(key).toString();
}

inline bool isChecked(const QVariant &entry)
{
    return entry.toMap().value(QStringLiteral("checked")).toBool();
}

inline QQuickItem *itemWithText(QQuickItem *root, const QString &text)
{
    if (root->isVisible() && root->property("text").toString() == text)
        return root;
    for (QQuickItem *child : root->childItems())
        if (QQuickItem *found = itemWithText(child, text))
            return found;
    return nullptr;
}

inline void clickCenterOf(QQuickItem *item)
{
    const QPointF center = item->mapToScene(QPointF(item->width() / 2, item->height() / 2));
    QTest::mouseClick(item->window(), Qt::LeftButton, Qt::NoModifier, center.toPoint());
}

inline bool isDialogOpen(QObject *window, const QString &title)
{
    for (QObject *object : window->findChildren<QObject *>())
        if (object->property("title").toString() == title && object->property("opened").toBool())
            return true;
    return false;
}

inline QString settingValue(const QString &name)
{
    return ExtensionManager::instance()->settingValues(QStringLiteral("sample")).value(name).toString();
}

constexpr const char *menuWindowQml =
    "import QtQuick\nimport QtQuick.Controls\nimport Kondor\n"
    "ApplicationWindow {\n"
    "    property alias menu: menu\n"
    "    ExtensionsMenu { id: menu; tab: theTab }\n"
    "}\n";

constexpr const char *settingsDialogQml =
    "import QtQuick\nimport QtQuick.Controls\nimport Kondor\n"
    "ApplicationWindow {\n"
    "    property alias dialog: dialog\n"
    "    ExtensionSettingsDialog { id: dialog }\n"
    "}\n";

constexpr const char *installDialogQml =
    "import QtQuick\nimport QtQuick.Controls\nimport Kondor\n"
    "ApplicationWindow {\n"
    "    visible: true\n"
    "    property alias dialog: dialog\n"
    "    InstallExtensionDialog { id: dialog; parent: Overlay.overlay }\n"
    "}\n";

constexpr const char *extensionsPageQml =
    "import QtQuick\nimport QtQuick.Controls\nimport Kondor\n"
    "ApplicationWindow {\n"
    "    visible: true\n"
    "    width: 700; height: 400\n"
    "    ExtensionsPage { anchors.fill: parent }\n"
    "}\n";

constexpr const char *emptySavedPasswordsQml =
    "import QtQuick\nimport QtQuick.Controls\nimport Kondor\n"
    "ApplicationWindow {\n"
    "    id: window\n"
    "    visible: true\n"
    "    width: 700; height: 400\n"
    "    property bool isAddRequested: false\n"
    "    SavedPasswordsList {\n"
    "        anchors.fill: parent\n"
    "        walletDenied: false\n"
    "        filter: \"\"\n"
    "        revealed: RevealedPasswords {}\n"
    "        onAddRequested: window.isAddRequested = true\n"
    "    }\n"
    "}\n";
