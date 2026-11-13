pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import QtCore
import org.kde.kirigami as Kirigami
import Kondor

ColumnLayout {
    id: root

    property bool autoUpdate: true
    signal autoUpdateToggled(bool checked)

    spacing: Kirigami.Units.largeSpacing

    function confirmRemoval(id, name) {
        removeDialog.extensionId = id
        removeDialog.extensionName = name
        removeDialog.open()
    }

    function openCatalog() {
        catalogDialog.open()
    }

    RowLayout {
        Layout.fillWidth: true
        spacing: Kirigami.Units.smallSpacing

        TextField {
            id: filterField
            Layout.fillWidth: true
            placeholderText: qsTr("Filter extensions…")
        }
        Button {
            text: qsTr("Get New Extensions…")
            icon.name: "get-hot-new-stuff"
            onClicked: root.openCatalog()
        }
        Button {
            text: qsTr("Install from File…")
            icon.name: "document-import"
            onClicked: installFileDialog.open()
        }
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
            id: extensionList
            objectName: "extensionList"
            anchors.fill: parent
            clip: true
            model: ExtensionManager

            delegate: ExtensionDelegate {
                filterText: filterField.text
                onConfigureRequested: function(id) { configureDialog.openFor(id) }
                onRemoveRequested: function(id, name) { root.confirmRemoval(id, name) }
            }

            Kirigami.PlaceholderMessage {
                anchors.centerIn: parent
                width: parent.width - Kirigami.Units.gridUnit * 4
                visible: extensionList.count === 0
                icon.name: "preferences-plugin"
                text: qsTr("No extensions installed")
                explanation: qsTr("Extensions add features to Kondor. Get them from the Kondor extensions catalog, or install a .kondorext file.")
                helpfulAction: Kirigami.Action {
                    text: qsTr("Get New Extensions…")
                    icon.name: "get-hot-new-stuff"
                    onTriggered: root.openCatalog()
                }
            }
        }
    }

    CheckBox {
        text: qsTr("Update extensions automatically")
        checked: root.autoUpdate
        onToggled: root.autoUpdateToggled(checked)
    }

    FileDialog {
        id: installFileDialog
        title: qsTr("Install Extension")
        fileMode: FileDialog.OpenFile
        currentFolder: StandardPaths.writableLocation(StandardPaths.DownloadLocation)
        nameFilters: [qsTr("Kondor extensions and user scripts (*.kondorext *.user.js)"),
                      qsTr("Kondor extensions (*.kondorext)"), qsTr("All files (*)")]
        onAccepted: ExtensionManager.inspectFile(selectedFile.toString())
    }

    ConfirmDialog {
        id: removeDialog
        property string extensionId: ""
        property string extensionName: ""
        title: qsTr("Remove Extension")
        message: qsTr("Remove the extension “%1” and its data?").arg(removeDialog.extensionName)
        acceptText: qsTr("Remove")
        acceptIcon: "edit-delete"
        onAccepted: ExtensionManager.remove(removeDialog.extensionId)
    }

    ExtensionCatalogDialog {
        id: catalogDialog
        parent: Overlay.overlay
    }

    InstallExtensionDialog {
        id: installDialog
        parent: Overlay.overlay
    }

    ExtensionSettingsDialog {
        id: configureDialog
        parent: Overlay.overlay
    }
}
