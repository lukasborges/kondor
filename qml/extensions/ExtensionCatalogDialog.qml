pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

Dialog {
    id: root

    anchors.centerIn: parent
    width: Kirigami.Units.gridUnit * 40
    height: Kirigami.Units.gridUnit * 30
    modal: true
    dim: true
    closePolicy: Popup.CloseOnEscape
    title: qsTr("Get New Extensions")
    standardButtons: Dialog.Close

    onAboutToShow: {
        searchField.text = ""
        ExtensionCatalog.refresh()
    }

    function matches(name, description, author) {
        const text = searchField.text.trim().toLowerCase()
        return text === "" || (name + " " + description + " " + author).toLowerCase().includes(text)
    }

    contentItem: ColumnLayout {
        spacing: Kirigami.Units.largeSpacing

        TextField {
            id: searchField
            Layout.fillWidth: true
            placeholderText: qsTr("Search extensions…")
        }

        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: ExtensionCatalog.state === "error"
            type: Kirigami.MessageType.Error
            text: qsTr("The extensions catalog could not be loaded.")
            actions: [
                Kirigami.Action {
                    text: qsTr("Try Again")
                    icon.name: "view-refresh"
                    onTriggered: ExtensionCatalog.refresh()
                }
            ]
        }

        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: ExtensionCatalog.installError !== ""
            type: Kirigami.MessageType.Error
            text: ExtensionCatalog.installError
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

            BusyIndicator {
                anchors.centerIn: parent
                running: ExtensionCatalog.state === "loading" && catalogList.count === 0
                visible: running
            }

            ListView {
                id: catalogList
                anchors.fill: parent
                clip: true
                model: ExtensionCatalog

                delegate: ItemDelegate {
                    id: entry
                    required property string id
                    required property string name
                    required property string description
                    required property string version
                    required property string author
                    required property string iconSource
                    required property bool installed
                    required property bool updateAvailable

                    width: ListView.view.width
                    visible: root.matches(entry.name, entry.description, entry.author)
                    height: visible ? implicitHeight : 0

                    contentItem: RowLayout {
                        spacing: Kirigami.Units.largeSpacing

                        ExtensionIcon {
                            source: entry.iconSource
                            size: Kirigami.Units.iconSizes.large
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 0

                            RowLayout {
                                Label {
                                    text: entry.name
                                    font.bold: true
                                }
                                Label {
                                    text: qsTr("by %1").arg(entry.author)
                                    opacity: 0.7
                                    font: Kirigami.Theme.smallFont
                                }
                            }
                            Label {
                                Layout.fillWidth: true
                                text: entry.description
                                wrapMode: Text.WordWrap
                            }
                        }

                        Button {
                            text: entry.installed ? qsTr("Installed")
                                  : entry.updateAvailable ? qsTr("Update") : qsTr("Install")
                            icon.name: entry.installed ? "checkmark"
                                       : entry.updateAvailable ? "update-none" : "download"
                            enabled: !entry.installed && ExtensionCatalog.installingId === ""
                            onClicked: ExtensionCatalog.install(entry.id)
                        }
                    }
                }
            }

            Kirigami.PlaceholderMessage {
                anchors.centerIn: parent
                width: parent.width - Kirigami.Units.gridUnit * 4
                visible: ExtensionCatalog.state === "ready" && catalogList.count === 0
                text: qsTr("The catalog has no extensions yet")
            }
        }

        Label {
            text: "<a href=\"" + ExtensionCatalog.contributingUrl() + "\">"
                  + qsTr("Submit an extension…") + "</a>"
            textFormat: Text.StyledText
            color: Kirigami.Theme.linkColor
            onLinkActivated: function(link) { Qt.openUrlExternally(link) }
        }
    }
}
