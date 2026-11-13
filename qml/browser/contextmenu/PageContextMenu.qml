import QtQuick
import QtQuick.Controls
import QtWebEngine
import Kondor

Menu {
    id: menu

    property var request: null
    property WebEngineView webView: null
    property Tab tab: null
    property TabModel tabModel: null
    property bool endsWithSeparator: true

    popupType: Popup.Item

    function popupAt(point) {
        rebuild()
        popup(webView, point.x, point.y)
    }

    function rebuild() {
        clear()
        endsWithSeparator = true
        entries.blocksFor(request).forEach(addBlock)
    }

    function clear() {
        while (count > 0)
            removeFirst()
    }

    function removeFirst() {
        const first = itemAt(0)
        if (first.subMenu)
            removeMenu(first.subMenu)
        else
            removeItem(first)
    }

    function addBlock(block) {
        addSeparatorOnce()
        block.forEach(addBlockEntry)
    }

    function addBlockEntry(entry) {
        if (entry === null) {
            addSeparatorOnce()
            return
        }
        addEntry(entry)
        endsWithSeparator = false
    }

    function addSeparatorOnce() {
        if (endsWithSeparator)
            return
        addItem(separatorComponent.createObject(null))
        endsWithSeparator = true
    }

    function addEntry(entry) {
        if (entry.spellCheckLanguages === true) {
            addMenu(spellCheckLanguagesComponent.createObject(null))
            return
        }
        const item = itemComponent.createObject(null, itemProperties(entry))
        if (entry.bold === true)
            item.font.bold = true
        addItem(item)
    }

    function itemProperties(entry) {
        return {
            "text": entry.text,
            "iconName": entry.icon ?? "",
            "actionId": entry.action,
            "actionData": entry.data ?? "",
            "enabled": entry.enabled !== false,
            "checkable": entry.checkable === true,
            "checked": entry.checked === true
        }
    }

    PageMenuEntries {
        id: entries
        webView: menu.webView
    }

    PageMenuActions {
        id: actions
        request: menu.request
        webView: menu.webView
        tab: menu.tab
        tabModel: menu.tabModel
    }

    Component {
        id: itemComponent

        MenuItem {
            property string actionId
            property string actionData
            property string iconName

            icon.name: iconName
            onTriggered: actions.perform(actionId, actionData)
        }
    }

    Component {
        id: spellCheckLanguagesComponent

        SpellCheckLanguagesMenu {}
    }

    Component {
        id: separatorComponent

        MenuSeparator {}
    }
}
