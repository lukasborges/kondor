import QtQuick
import QtQuick.Controls
import org.kde.kirigami as Kirigami
import Kondor

// The toolbar "Extensions" menu: one section per enabled extension with a
// toolbar action (its items, with a per-tab checked state, and "Run on <site>"),
// then "Manage Extensions…". The sections are rebuilt every time it opens.
Menu {
    id: root

    required property Tab tab
    signal manageRequested()

    // Flat description of the current content: `{ kind, ... }` entries.
    property var entries: []
    readonly property string host: root.tab ? root.tab.url.toString().replace(/^https?:\/\/([^/:?#]+).*$/, "$1") : ""

    function rebuild() {
        const list = []
        if (!root.tab) {
            root.entries = list
            return
        }
        const extensions = ExtensionManager.actionExtensions(root.tab.isPrivate)
        for (const extension of extensions) {
            list.push({ kind: "header", title: extension.name, icon: extension.iconSource })
            for (const item of extension.items) {
                list.push({
                    kind: "item", extension: extension.id, id: item.id, title: item.title,
                    checkable: item.checkable, icon: item.icon,
                    checked: root.tab.extensionItems.isChecked(extension.id, item.id)
                })
            }
            if (extension.siteToggle && ExtensionManager.originOf(root.tab.url) !== "") {
                list.push({
                    kind: "site", extension: extension.id,
                    title: qsTr("Run on %1").arg(root.host),
                    checked: ExtensionManager.siteEnabled(extension.id, root.tab.url)
                })
            }
        }
        root.entries = list
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
            // Headers are always drawn at full strength.
            opacity: 1.0
            onTriggered: {
                if (entry.modelData.kind === "item") {
                    root.tab.extensionItems.trigger(entry.modelData.extension, entry.modelData.id,
                                                  entry.modelData.checkable === true)
                } else if (entry.modelData.kind === "site") {
                    ExtensionManager.setSiteEnabled(entry.modelData.extension, root.tab.url,
                                                    entry.checked)
                    root.tab.reload()
                }
            }
        }
    }

    MenuSeparator {}

    MenuItem {
        text: qsTr("Manage Extensions…")
        icon.name: "preferences-plugin"
        onTriggered: root.manageRequested()
    }
}
