import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

Popup {
    id: root

    required property var browserWindow

    width: 360
    padding: Kirigami.Units.largeSpacing
    modal: false
    focus: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

    function openPrivacySettings() {
        root.close()
        root.browserWindow.openSettingsPage("privacy")
    }

    contentItem: ColumnLayout {
        spacing: Kirigami.Units.largeSpacing

        RowLayout {
            Layout.fillWidth: true
            spacing: Kirigami.Units.largeSpacing

            Kirigami.Icon {
                source: "automated-tasks"
                color: Kirigami.Theme.neutralTextColor
                Layout.preferredWidth: Kirigami.Units.iconSizes.medium
                Layout.preferredHeight: Kirigami.Units.iconSizes.medium
            }

            ColumnLayout {
                spacing: 0
                Layout.fillWidth: true

                Kirigami.Heading {
                    level: 4
                    text: qsTr("Remote Control Is On")
                    Layout.fillWidth: true
                    elide: Text.ElideRight
                }

                Label {
                    text: RemoteControl.address
                    color: Kirigami.Theme.disabledTextColor
                    Layout.fillWidth: true
                    elide: Text.ElideRight
                }
            }

            CopyFeedbackButton {
                iconName: "edit-copy"
                tooltipText: qsTr("Copy Address")
                copiedTooltipText: qsTr("Copied")
                announcement: qsTr("Address copied")
                accessibleName: qsTr("Copy Address")
                onCopyRequested: RemoteControl.copyAddress()
            }
        }

        Label {
            text: qsTr("Automation tools on this computer can read and control the pages of normal windows. Private browsing is unavailable.")
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }

        Kirigami.Separator { Layout.fillWidth: true }

        Button {
            text: qsTr("Configure…")
            icon.name: "configure"
            flat: true
            Layout.alignment: Qt.AlignRight
            onClicked: root.openPrivacySettings()
        }
    }
}
