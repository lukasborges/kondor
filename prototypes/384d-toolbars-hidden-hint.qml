// #384 Right after the toolbars are hidden: a floating hint at the top of the page for 5 s, in the
// style of the page full screen hint (Complementary colors, outlined so it stands out on any page).
// "Show Toolbars" turns the setting off; the keyboard way is in its tooltip.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "common"

BrowserFrame {
    id: frame
    showHeader: false
    FakePage {}

    Rectangle {
        anchors.horizontalCenter: parent.horizontalCenter
        y: Kirigami.Units.gridUnit * 2
        width: hintRow.implicitWidth + Kirigami.Units.largeSpacing * 2
        height: hintRow.implicitHeight + Kirigami.Units.smallSpacing * 2
        radius: Kirigami.Units.cornerRadius
        Kirigami.Theme.colorSet: Kirigami.Theme.Complementary
        Kirigami.Theme.inherit: false
        color: Kirigami.Theme.backgroundColor
        border.width: 1
        border.color: Qt.rgba(Kirigami.Theme.textColor.r, Kirigami.Theme.textColor.g, Kirigami.Theme.textColor.b, 0.3)
        opacity: 0.95

        RowLayout {
            id: hintRow
            anchors.centerIn: parent
            spacing: Kirigami.Units.largeSpacing
            Label {
                Layout.leftMargin: Kirigami.Units.smallSpacing
                color: Kirigami.Theme.textColor
                text: "Toolbars hidden"
            }
            Button {
                text: "Show Toolbars"
                icon.name: "view-visible"
                ToolTip.visible: true
                ToolTip.delay: 600
                ToolTip.text: "Ctrl+Shift+F, or move the pointer to the top"
            }
        }
    }
}
