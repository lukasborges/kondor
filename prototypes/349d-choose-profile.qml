// #349 Multiple profiles — "Choose a Profile" window shown at startup when the
// startup choice is "Ask Every Time": a click (or Enter) on a row opens that profile.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Rectangle {
    width: 380
    height: 340
    color: Kirigami.Theme.backgroundColor

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Kirigami.Units.largeSpacing
        spacing: Kirigami.Units.largeSpacing

        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Kirigami.Theme.colorSet: Kirigami.Theme.View
            Kirigami.Theme.inherit: false
            background: Rectangle {
                color: Kirigami.Theme.backgroundColor
                border.color: Kirigami.ColorUtils.linearInterpolation(Kirigami.Theme.backgroundColor, Kirigami.Theme.textColor, Kirigami.Theme.frameContrast)
            }
            ListView {
                focus: true
                currentIndex: 0
                model: [
                    { name: "Personal", icon: "im-user" },
                    { name: "Work", icon: "view-pim-tasks" },
                    { name: "Shopping", icon: "globe" }
                ]
                delegate: ItemDelegate {
                    required property var modelData
                    width: ListView.view.width
                    highlighted: ListView.isCurrentItem
                    text: modelData.name
                    icon.name: modelData.icon
                    icon.width: Kirigami.Units.iconSizes.smallMedium
                    icon.height: Kirigami.Units.iconSizes.smallMedium
                }
            }
        }

        DialogButtonBox {
            Layout.fillWidth: true
            padding: 0
            Button {
                text: "Quit"
                icon.name: "application-exit"
                DialogButtonBox.buttonRole: DialogButtonBox.RejectRole
            }
        }
    }
}
