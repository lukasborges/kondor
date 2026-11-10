import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

// Full-page notice shown over the WebEngineView when this tab's renderer
// process died. Reload starts a fresh process for the same page.
Item {
    id: root

    required property Tab tab
    required property TabModel tabModel

    Rectangle {
        anchors.fill: parent
        Kirigami.Theme.colorSet: Kirigami.Theme.View
        Kirigami.Theme.inherit: false
        color: Kirigami.Theme.backgroundColor

        ColumnLayout {
            anchors.centerIn: parent
            width: Math.min(parent.width - 2 * Kirigami.Units.gridUnit, 480)
            spacing: Kirigami.Units.largeSpacing * 2

            Kirigami.Icon {
                source: "dialog-error"
                Layout.preferredWidth: 64
                Layout.preferredHeight: 64
                Layout.alignment: Qt.AlignHCenter
            }

            Kirigami.Heading {
                level: 2
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
                text: qsTr("This tab crashed")
            }

            Label {
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                horizontalAlignment: Text.AlignHCenter
                visible: text.length > 0
                text: root.tab.crashReason
            }

            Label {
                Layout.alignment: Qt.AlignHCenter
                color: Kirigami.Theme.disabledTextColor
                font: Kirigami.Theme.smallFont
                text: qsTr("Exit code: %1").arg(root.tab.crashExitCode)
            }

            RowLayout {
                Layout.alignment: Qt.AlignHCenter
                spacing: Kirigami.Units.largeSpacing

                Button {
                    text: qsTr("Close Tab")
                    icon.name: "tab-close"
                    onClicked: root.tabModel.closeTabObject(root.tab)
                }

                Button {
                    text: qsTr("Reload")
                    icon.name: "view-refresh"
                    highlighted: true
                    // The Breeze style only activates a Button on Space, so
                    // Return and Enter are handled explicitly: they reload right
                    // away, like the default button.
                    focus: visible
                    Keys.onReturnPressed: clicked()
                    Keys.onEnterPressed: clicked()
                    onClicked: root.tab.reload()
                }
            }
        }
    }
}
