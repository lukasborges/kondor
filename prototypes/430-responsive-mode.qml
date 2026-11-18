// #430 Responsive design mode (Ctrl+Shift+M): a toolbar under the navigation toolbar picks a
// device or a free size; the page is laid out at that size, centered on a neutral background,
// with handles to resize it. Choosing a phone or tablet uses its mobile user agent in this tab.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "common"

BrowserFrame {
    id: frame
    height: 760
    address: "https://kde.org/"
    belowHeader: [
        ToolBar {
            Layout.fillWidth: true
            position: ToolBar.Header
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: Kirigami.Units.smallSpacing
                anchors.rightMargin: Kirigami.Units.smallSpacing
                spacing: Kirigami.Units.smallSpacing
                ComboBox {
                    model: ["Responsive", "iPhone 15", "Pixel 8", "Galaxy S24", "iPad Air", "iPad Pro 12.9″"]
                    currentIndex: 1
                    implicitContentWidthPolicy: ComboBox.WidestText
                    Accessible.name: "Device"
                }
                SpinBox {
                    from: 200; to: 4000; value: 393; editable: true
                    Accessible.name: "Width"
                }
                Label { text: "×" }
                SpinBox {
                    from: 200; to: 4000; value: 852; editable: true
                    Accessible.name: "Height"
                }
                ToolButton {
                    icon.name: "object-rotate-right"
                    display: AbstractButton.IconOnly
                    ToolTip.text: "Rotate"
                    ToolTip.delay: 600
                    Accessible.name: "Rotate"
                }
                ToolButton {
                    icon.name: "zoom-fit-best"
                    display: AbstractButton.IconOnly
                    checkable: true
                    checked: true
                    ToolTip.text: "Zoom to Fit"
                    ToolTip.delay: 600
                    Accessible.name: "Zoom to Fit"
                }
                Item { Layout.fillWidth: true }
                ToolButton {
                    icon.name: "window-close"
                    display: AbstractButton.IconOnly
                    ToolTip.text: "Close Responsive Mode (Ctrl+Shift+M)"
                    ToolTip.delay: 600
                    Accessible.name: "Close Responsive Mode"
                }
            }
        }
    ]

    Rectangle {
        id: stage
        anchors.fill: parent
        color: Kirigami.ColorUtils.linearInterpolation(Kirigami.Theme.backgroundColor, Kirigami.Theme.textColor, 0.08)

        Rectangle {
            id: viewport
            anchors.horizontalCenter: parent.horizontalCenter
            y: Kirigami.Units.largeSpacing * 2
            width: 393 * 0.62
            height: 852 * 0.62
            color: "white"
            border.color: Kirigami.ColorUtils.linearInterpolation(Kirigami.Theme.backgroundColor, Kirigami.Theme.textColor, Kirigami.Theme.frameContrast)
            clip: true
            Item {
                width: 393
                height: 852
                scale: 0.62
                transformOrigin: Item.TopLeft
                Rectangle {
                    id: mobileHeader
                    width: parent.width; height: 56
                    color: "#232629"
                    Kirigami.Icon { source: "kde"; x: 16; anchors.verticalCenter: parent.verticalCenter; width: 28; height: 28 }
                    Kirigami.Icon { source: "application-menu"; color: "white"; isMask: true; anchors.right: parent.right; anchors.rightMargin: 16; anchors.verticalCenter: parent.verticalCenter; width: 24; height: 24 }
                }
                Column {
                    anchors.top: mobileHeader.bottom
                    anchors.topMargin: 24
                    x: 20
                    width: parent.width - 40
                    spacing: 16
                    Text { width: parent.width; wrapMode: Text.WordWrap; text: "KDE Community"; font.pixelSize: 32; font.bold: true; color: "#232629" }
                    Text { width: parent.width; wrapMode: Text.WordWrap; font.pixelSize: 17; lineHeight: 1.4; color: "#232629"
                        text: "Plasma is the desktop environment made by the KDE community. It is light, fast and fully configurable, from panels to keyboard shortcuts." }
                    Rectangle {
                        width: parent.width; height: 200; radius: 8
                        gradient: Gradient { orientation: Gradient.Horizontal; GradientStop { position: 0; color: "#3daee9" } GradientStop { position: 1; color: "#1d76b3" } }
                        Kirigami.Icon { anchors.centerIn: parent; source: "plasma"; width: 72; height: 72 }
                    }
                    Text { width: parent.width; wrapMode: Text.WordWrap; font.pixelSize: 17; lineHeight: 1.4; color: "#232629"
                        text: "Apps like Dolphin, Konsole, Kate and Okular follow the same Human Interface Guidelines." }
                }
            }
        }
        Rectangle {
            anchors.left: viewport.right
            anchors.leftMargin: 3
            anchors.verticalCenter: viewport.verticalCenter
            width: 4; height: Kirigami.Units.gridUnit * 2; radius: 2
            color: Kirigami.Theme.disabledTextColor
        }
        Rectangle {
            anchors.top: viewport.bottom
            anchors.topMargin: 3
            anchors.horizontalCenter: viewport.horizontalCenter
            width: Kirigami.Units.gridUnit * 2; height: 4; radius: 2
            color: Kirigami.Theme.disabledTextColor
        }
        Label {
            anchors.top: viewport.bottom
            anchors.topMargin: Kirigami.Units.largeSpacing
            anchors.horizontalCenter: viewport.horizontalCenter
            text: "62 %"
            color: Kirigami.Theme.disabledTextColor
        }
    }
}
