// #22 Reader mode — clean article in KDE theme colors, checked toolbar button and floating controls.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "common"

BrowserFrame {
    address: "https://blogs.kde.org/2026/10/plasma-6-5"
    tabs: [{ title: "Plasma 6.5: What's New", icon: "internet-web-browser" }]
    addressLeft: [
        ToolButton { icon.name: "security-high"; display: AbstractButton.IconOnly; flat: true; implicitWidth: 28; implicitHeight: 28 }
    ]
    addressRight: [
        ToolButton { icon.name: "view-readermode"; display: AbstractButton.IconOnly; flat: true; checked: true; implicitWidth: 28; implicitHeight: 28 }
    ]
    Rectangle {
        anchors.fill: parent
        Kirigami.Theme.colorSet: Kirigami.Theme.View
        Kirigami.Theme.inherit: false
        color: Kirigami.Theme.backgroundColor

        ColumnLayout {
            anchors.horizontalCenter: parent.horizontalCenter
            y: 40
            width: 640
            spacing: 16
            Label { text: "BLOGS.KDE.ORG"; color: Kirigami.Theme.disabledTextColor; font.letterSpacing: 1.5; font.pointSize: Kirigami.Theme.smallFont.pointSize }
            Label { text: "Plasma 6.5: What's New"; font.pixelSize: 32; font.family: "Noto Serif"; font.bold: true; Layout.fillWidth: true; wrapMode: Text.WordWrap }
            Label { text: "By the KDE Promo Team · 7 min read"; color: Kirigami.Theme.disabledTextColor }
            Label {
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                font.family: "Noto Serif"; font.pixelSize: 18; lineHeight: 1.5
                text: "Plasma 6.5 brings window management improvements, a new quick settings panel and better HDR support. The community also spent this cycle fixing hundreds of small issues reported by users."
            }
            Label {
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                font.family: "Noto Serif"; font.pixelSize: 18; lineHeight: 1.5
                text: "Among the most requested features are automatic tiling, which arranges windows effortlessly, and the new welcome screen."
            }
        }

        // Reader mode floating controls (QML, not part of the HTML)
        Pane {
            anchors { right: parent.right; top: parent.top; margins: Kirigami.Units.largeSpacing }
            padding: Kirigami.Units.smallSpacing
            background: Rectangle {
                color: Kirigami.Theme.backgroundColor; radius: Kirigami.Units.cornerRadius
                border.color: Kirigami.ColorUtils.linearInterpolation(Kirigami.Theme.backgroundColor, Kirigami.Theme.textColor, 0.2)
            }
            RowLayout {
                spacing: 2
                ToolButton { icon.name: "format-font-size-less"; display: AbstractButton.IconOnly }
                Label { text: "18 px" }
                ToolButton { icon.name: "format-font-size-more"; display: AbstractButton.IconOnly }
                ToolButton { text: "Serif"; icon.name: "format-text-symbol"; checkable: true; checked: true }
                ToolButton { text: "Exit Reader Mode"; icon.name: "window-close" }
            }
        }
    }
}
