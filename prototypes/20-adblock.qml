// #20 Ad and tracker blocking — button with counter in the address bar and per-site popup.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "common"

BrowserFrame {
    id: frame
    address: "https://news.example.com/tech/kde-plasma-6"
    tabs: [{ title: "Plasma 6 ships with Wayland by default", icon: "internet-web-browser" }]
    addressLeft: [
        ToolButton { icon.name: "security-high"; display: AbstractButton.IconOnly; flat: true; implicitWidth: 28; implicitHeight: 28 }
    ]
    addressRight: [
        ToolButton {
            icon.name: "view-filter"
            display: AbstractButton.IconOnly
            flat: true
            checked: true
            implicitWidth: 28; implicitHeight: 28
            Rectangle {
                anchors { right: parent.right; top: parent.top; rightMargin: 1; topMargin: 1 }
                width: badge.implicitWidth + 6; height: 13; radius: 6.5
                color: Kirigami.Theme.negativeTextColor
                Label { id: badge; anchors.centerIn: parent; text: "27"; color: "white"; font.pixelSize: 9; font.bold: true }
            }
        }
    ]
    FakePage { heading: "Plasma 6 ships with Wayland by default" }

    Popup {
        popupType: Popup.Item
        x: frame.width - width - 50
        y: -4
        width: 340
        padding: Kirigami.Units.largeSpacing
        Component.onCompleted: open()
        contentItem: ColumnLayout {
            spacing: Kirigami.Units.largeSpacing
            RowLayout {
                spacing: Kirigami.Units.largeSpacing
                Kirigami.Icon { source: "view-filter"; Layout.preferredWidth: 32; Layout.preferredHeight: 32 }
                ColumnLayout {
                    spacing: 0
                    Kirigami.Heading { level: 4; text: "27 items blocked" }
                    Label { text: "news.example.com"; color: Kirigami.Theme.disabledTextColor }
                }
            }
            Label { text: "19 ads · 8 trackers"; color: Kirigami.Theme.disabledTextColor }
            Kirigami.Separator { Layout.fillWidth: true }
            Switch { text: "Blocking enabled on this site"; checked: true }
            RowLayout {
                Layout.fillWidth: true
                Label { text: "Lists updated today, 09:12"; font: Kirigami.Theme.smallFont; color: Kirigami.Theme.disabledTextColor; Layout.fillWidth: true }
                Button { text: "Update"; icon.name: "view-refresh"; flat: true }
            }
        }
    }
}
