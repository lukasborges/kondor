import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

// Floating controls of reader mode, shown over the top-right corner of the
// page: font size, font family and a way out.
Pane {
    id: root

    signal exitRequested()

    padding: Kirigami.Units.smallSpacing
    background: Rectangle {
        color: Kirigami.Theme.backgroundColor
        radius: Kirigami.Units.cornerRadius
        border.color: Kirigami.ColorUtils.linearInterpolation(
            Kirigami.Theme.backgroundColor, Kirigami.Theme.textColor, 0.2)
    }

    RowLayout {
        spacing: 2

        ToolButton {
            icon.name: "format-font-size-less"
            display: AbstractButton.IconOnly
            enabled: Settings.readerFontSize > 12
            ToolTip.visible: hovered
            ToolTip.text: qsTr("Decrease Font Size")
            ToolTip.delay: 600
            onClicked: Settings.readerFontSize -= 2
        }
        Label {
            //: Font size in pixels, %1 is the number
            text: qsTr("%1 px").arg(Settings.readerFontSize)
        }
        ToolButton {
            icon.name: "format-font-size-more"
            display: AbstractButton.IconOnly
            enabled: Settings.readerFontSize < 32
            ToolTip.visible: hovered
            ToolTip.text: qsTr("Increase Font Size")
            ToolTip.delay: 600
            onClicked: Settings.readerFontSize += 2
        }
        ToolButton {
            text: Settings.readerSerif ? qsTr("Serif") : qsTr("Sans Serif")
            icon.name: "format-text-symbol"
            checkable: true
            checked: Settings.readerSerif
            ToolTip.visible: hovered
            ToolTip.text: qsTr("Switch Font Family")
            ToolTip.delay: 600
            onClicked: Settings.readerSerif = !Settings.readerSerif
        }
        ToolButton {
            text: qsTr("Exit Reader Mode")
            icon.name: "window-close"
            onClicked: root.exitRequested()
        }
    }
}
