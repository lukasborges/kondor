import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import QtCore
import org.kde.kirigami as Kirigami
import Kondor

// Settings → Passwords: the "Saved Passwords" and "Never Saved" tabs. The list
// holds only sites and usernames; a password is read from KWallet when Show or
// Copy is clicked and is masked again when the window closes. Delete and
// Remove act at once (like "Clear Cookies and Cache Now"); only the "offer"
// checkbox is a pending option, owned by the Configure window.
StackLayout {
    id: root

    // Pending value of the "Offer to save passwords" option and the tab chosen
    // in the Configure window's tab bar.
    property bool offerToSave: true
    property int tab: 0
    signal offerToSaveToggled(bool checked)

    currentIndex: root.tab

    readonly property bool walletDenied: PasswordStore.state === "unavailable"
    // True while the page is on screen in a shown window.
    readonly property bool active: root.visible && Window.window !== null && Window.window.visible
    // Passwords revealed by Show, by "origin\nusername". Dropped when the window closes.
    property var revealed: ({})
    // State of the message about the last import (cleared when the window closes).
    property bool importDone: false
    property bool importFailed: false
    property bool importTrashed: false
    property bool importTrashFailed: false
    property int importedCount: 0
    property string importedName: ""
    property url importedFile

    function keyOf(origin, username) {
        return origin + "\n" + username
    }

    function isRevealed(origin, username) {
        return root.revealed[root.keyOf(origin, username)] !== undefined
    }

    function toggleReveal(origin, username) {
        const copy = Object.assign({}, root.revealed)
        const key = root.keyOf(origin, username)
        if (copy[key] !== undefined)
            delete copy[key]
        else
            copy[key] = PasswordStore.password(origin, username)
        root.revealed = copy
    }

    function rebuild() {
        const filter = filterField.text.trim().toLowerCase()
        const list = PasswordStore.entries.filter(function(entry) {
            return filter === "" || entry.host.toLowerCase().includes(filter)
                || entry.username.toLowerCase().includes(filter)
        })
        list.sort(function(a, b) {
            return a.host.localeCompare(b.host) || a.origin.localeCompare(b.origin)
                || a.username.localeCompare(b.username)
        })
        savedModel.clear()
        for (const entry of list)
            savedModel.append({ site: entry.host, origin: entry.origin, username: entry.username })
        // Nothing is selected until a login is added by hand.
        savedList.currentIndex = -1
    }

    onActiveChanged: {
        if (root.active) {
            PasswordStore.ensureOpen()
            root.rebuild()
        } else {
            root.revealed = ({})
            addDialog.close()
            addDialog.clear()
            importDialog.close()
            PasswordStore.cancelImport()
            root.importDone = false
        }
    }

    Connections {
        target: PasswordStore
        function onChanged() {
            root.rebuild()
            // A deleted login must not keep a revealed password around.
            root.revealed = ({})
        }
    }

    ListModel { id: savedModel }

    AddPasswordDialog {
        id: addDialog
        parent: Overlay.overlay
        onSaved: function(origin, username) {
            filterField.text = ""
            root.rebuild()
            for (let i = 0; i < savedModel.count; ++i) {
                const row = savedModel.get(i)
                if (row.origin === origin && row.username === username) {
                    savedList.currentIndex = i
                    savedList.positionViewAtIndex(i, ListView.Contain)
                    break
                }
            }
        }
    }

    FileDialog {
        id: importFileDialog
        title: qsTr("Import Passwords")
        fileMode: FileDialog.OpenFile
        currentFolder: StandardPaths.writableLocation(StandardPaths.DownloadLocation)
        nameFilters: [qsTr("CSV files (*.csv)"), qsTr("All files (*)")]
        onAccepted: {
            root.importDone = false
            importDialog.openFor(PasswordStore.prepareImport(selectedFile))
            root.importedFile = selectedFile
        }
    }

    ImportPasswordsDialog {
        id: importDialog
        parent: Overlay.overlay
        onImported: function(count, fileName) {
            root.importedCount = count
            root.importedName = fileName
            root.importFailed = count < 0
            root.importTrashed = false
            root.importTrashFailed = false
            root.importDone = true
        }
    }

    MessageDialog {
        id: deleteDialog
        property string origin: ""
        property string username: ""
        title: qsTr("Delete Saved Password")
        text: qsTr("Delete the saved password for %1 on %2?")
                  .arg(deleteDialog.username).arg(deleteDialog.origin.replace(/^https?:\/\//, ""))
        buttons: MessageDialog.Yes | MessageDialog.No
        onButtonClicked: function(button) {
            if (button === MessageDialog.Yes)
                PasswordStore.remove(deleteDialog.origin, deleteDialog.username)
        }
    }

    // ── Saved Passwords ─────────────────────────────────────────────────
    ColumnLayout {
        spacing: Kirigami.Units.largeSpacing

        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: root.walletDenied
            type: Kirigami.MessageType.Warning
            text: qsTr("KWallet is disabled or access to it was denied, so passwords cannot be saved or filled.")
            actions: [
                Kirigami.Action {
                    text: qsTr("Try Again")
                    icon.name: "view-refresh"
                    onTriggered: PasswordStore.retry()
                }
            ]
        }

        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: root.importDone
            type: root.importFailed ? Kirigami.MessageType.Error : Kirigami.MessageType.Positive
            showCloseButton: true
            text: root.importFailed
                  ? qsTr("Some passwords could not be saved to KWallet.")
                  : root.importTrashed
                    ? qsTr("“%1” was moved to the trash.").arg(root.importedName)
                    : qsTr("Imported %n password(s) from “%1”. The file holds your passwords unencrypted: delete it when you no longer need it.", "", root.importedCount).arg(root.importedName)
            actions: [
                Kirigami.Action {
                    visible: !root.importFailed && !root.importTrashed && !root.importTrashFailed
                    text: qsTr("Move File to Trash")
                    icon.name: "user-trash"
                    onTriggered: {
                        if (PasswordStore.moveImportFileToTrash(root.importedFile))
                            root.importTrashed = true
                        else
                            root.importTrashFailed = true
                    }
                }
            ]
            // The close button sets `visible` directly, which drops the binding.
            onVisibleChanged: if (!visible) {
                root.importDone = false
                visible = Qt.binding(function() { return root.importDone })
            }
        }

        CheckBox {
            id: offerCheck
            enabled: !root.walletDenied
            text: qsTr("Offer to save passwords")
            onToggled: root.offerToSaveToggled(checked)
        }

        Binding {
            target: offerCheck
            property: "checked"
            value: root.offerToSave
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: Kirigami.Units.smallSpacing

            TextField {
                id: filterField
                Layout.fillWidth: true
                enabled: !root.walletDenied
                placeholderText: qsTr("Filter by site or username…")
                onTextChanged: root.rebuild()
            }

            Button {
                text: qsTr("Add Password…")
                icon.name: "list-add"
                enabled: !root.walletDenied
                onClicked: addDialog.open()
            }

            Button {
                text: qsTr("Import…")
                icon.name: "document-import"
                enabled: !root.walletDenied
                ToolTip.visible: hovered
                ToolTip.text: qsTr("Import passwords from a CSV file")
                ToolTip.delay: 600
                onClicked: importFileDialog.open()
            }
        }

        Frame {
            Layout.fillWidth: true
            Layout.fillHeight: true
            padding: 0
            enabled: !root.walletDenied
            Kirigami.Theme.colorSet: Kirigami.Theme.View
            Kirigami.Theme.inherit: false
            background: Rectangle {
                color: Kirigami.Theme.backgroundColor
                border.color: Kirigami.ColorUtils.linearInterpolation(
                                  Kirigami.Theme.backgroundColor, Kirigami.Theme.textColor, 0.2)
            }

            Kirigami.PlaceholderMessage {
                anchors.centerIn: parent
                width: parent.width - Kirigami.Units.gridUnit * 4
                visible: !root.walletDenied && savedModel.count === 0
                icon.name: filterField.text.trim() !== "" ? "edit-none" : "dialog-password"
                text: filterField.text.trim() !== ""
                      ? qsTr("No saved passwords match “%1”").arg(filterField.text.trim())
                      : qsTr("No saved passwords")
                explanation: filterField.text.trim() !== ""
                             ? ""
                             : qsTr("Kondor offers to save a password when you log in to a site. You can also add one here, or import the CSV file exported by another browser or password manager.")
                helpfulAction: filterField.text.trim() !== "" ? null : addAction

                Kirigami.Action {
                    id: addAction
                    text: qsTr("Add Password…")
                    icon.name: "list-add"
                    onTriggered: addDialog.open()
                }
            }

            ListView {
                id: savedList
                anchors.fill: parent
                clip: true
                visible: !root.walletDenied
                highlightFollowsCurrentItem: false
                model: savedModel
                section.property: "site"
                section.delegate: Kirigami.ListSectionHeader {
                    required property string section
                    width: ListView.view.width
                    text: section
                }

                delegate: ItemDelegate {
                    id: row
                    highlighted: ListView.isCurrentItem
                    required property string origin
                    required property string username
                    readonly property bool shown: root.isRevealed(origin, username)
                    width: ListView.view.width

                    contentItem: RowLayout {
                        spacing: Kirigami.Units.largeSpacing

                        Label {
                            text: row.username
                            Layout.preferredWidth: Kirigami.Units.gridUnit * 10
                            elide: Text.ElideRight
                        }

                        Label {
                            Layout.fillWidth: true
                            text: row.shown ? root.revealed[root.keyOf(row.origin, row.username)]
                                            : "••••••••••"
                            font.family: row.shown ? "monospace" : Kirigami.Theme.defaultFont.family
                            elide: Text.ElideRight
                        }

                        ToolButton {
                            icon.name: row.shown ? "view-hidden" : "view-visible"
                            display: AbstractButton.IconOnly
                            text: row.shown ? qsTr("Hide Password") : qsTr("Show Password")
                            ToolTip.visible: hovered
                            ToolTip.text: text
                            ToolTip.delay: 600
                            onClicked: root.toggleReveal(row.origin, row.username)
                        }

                        ToolButton {
                            icon.name: "edit-copy"
                            display: AbstractButton.IconOnly
                            text: qsTr("Copy Password")
                            ToolTip.visible: hovered
                            ToolTip.text: text
                            ToolTip.delay: 600
                            onClicked: PasswordStore.copyPassword(row.origin, row.username)
                        }

                        ToolButton {
                            icon.name: "edit-delete"
                            display: AbstractButton.IconOnly
                            text: qsTr("Delete")
                            ToolTip.visible: hovered
                            ToolTip.text: text
                            ToolTip.delay: 600
                            onClicked: {
                                deleteDialog.origin = row.origin
                                deleteDialog.username = row.username
                                deleteDialog.open()
                            }
                        }
                    }
                }
            }
        }
    }

    // ── Never Saved ─────────────────────────────────────────────────────
    ColumnLayout {
        spacing: Kirigami.Units.largeSpacing

        Label {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            text: qsTr("Kondor never offers to save passwords on these sites.")
        }

        Frame {
            Layout.fillWidth: true
            Layout.fillHeight: true
            padding: 0
            Kirigami.Theme.colorSet: Kirigami.Theme.View
            Kirigami.Theme.inherit: false
            background: Rectangle {
                color: Kirigami.Theme.backgroundColor
                border.color: Kirigami.ColorUtils.linearInterpolation(
                                  Kirigami.Theme.backgroundColor, Kirigami.Theme.textColor, 0.2)
            }

            ListView {
                anchors.fill: parent
                clip: true
                model: Settings.passwordNeverSaveSites

                delegate: ItemDelegate {
                    required property string modelData
                    width: ListView.view.width

                    contentItem: RowLayout {
                        Label {
                            text: modelData.replace(/^https?:\/\//, "")
                            Layout.fillWidth: true
                            elide: Text.ElideRight
                        }

                        Button {
                            text: qsTr("Remove")
                            icon.name: "list-remove"
                            flat: true
                            onClicked: Settings.passwordNeverSaveSites =
                                Settings.passwordNeverSaveSites.filter(function(site) {
                                    return site !== modelData
                                })
                        }
                    }
                }
            }
        }
    }
}
