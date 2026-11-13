import QtQuick
import QtQuick.Controls
import org.kde.kirigami as Kirigami
import Kondor

Menu {
    id: root

    required property Tab tab
    signal manageRequested()

    property var entries: []
    readonly property string host: root.tab ? root.tab.url.toString().replace(/^https?:\/\/([^/:?#]+).*$/, "$1") : ""

    function rebuild() {
        root.entries = root.tab ? root.collectEntries() : []
    }

    function collectEntries() {
        const list = []
        for (const extension of ExtensionManager.actionExtensions(root.tab.isPrivate))
            list.push(...root.entriesOf(extension))
        return list
    }

    function entriesOf(extension) {
        const list = [{ kind: "header", title: extension.name, icon: extension.iconSource }]
        list.push(...extension.items.map(function(item) { return root.itemEntry(extension, item) }))
        if (extension.siteToggle && ExtensionManager.originOf(root.tab.url) !== "")
            list.push(root.siteEntry(extension))
        return list
    }

    function itemEntry(extension, item) {
        return {
            kind: "item", extension: extension.id, id: item.id, title: item.title,
            checkable: item.checkable, icon: item.icon,
            checked: root.tab.extensionItems.isChecked(extension.id, item.id)
        }
    }

    function siteEntry(extension) {
        return {
            kind: "site", extension: extension.id, extensionName: extension.name,
            title: qsTr("Run on %1").arg(root.host),
            accessibleName: qsTr("Run %1 on %2").arg(extension.name).arg(root.host),
            checked: ExtensionManager.siteEnabled(extension.id, root.tab.url)
        }
    }

    function triggerItem(data) {
        root.tab.extensionItems.trigger(data.extension, data.id, data.checkable === true)
    }

    function toggleSite(data, checked) {
        ExtensionManager.setSiteEnabled(data.extension, root.tab.url, checked)
        root.tab.siteReload.recordToggle(data.extension, data.extensionName, checked)
    }

    function trigger(data, checked) {
        if (data.kind === "item")
            root.triggerItem(data)
        else if (data.kind === "site")
            root.toggleSite(data, checked)
    }

    onAboutToShow: root.rebuild()

    Repeater {
        model: root.entries

        delegate: MenuItem {
            id: entry
            required property var modelData
            text: entry.modelData.title
            checkable: entry.modelData.kind === "site" || entry.modelData.checkable === true
            checked: entry.modelData.checked === true
            enabled: entry.modelData.kind !== "header"
            font.bold: entry.modelData.kind === "header"
            icon.name: entry.modelData.kind === "header" || entry.modelData.icon
                       ? (entry.modelData.icon ?? "") : ""
            opacity: 1.0
            Accessible.name: entry.modelData.accessibleName ?? entry.text
            onTriggered: root.trigger(entry.modelData, entry.checked)
        }
    }

    MenuSeparator {}

    MenuItem {
        text: qsTr("Manage Extensions…")
        icon.name: "preferences-plugin"
        onTriggered: root.manageRequested()
    }
}
