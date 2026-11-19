import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

ToolBar {
    id: root

    required property Tab tab

    readonly property TabResponsive responsive: tab.responsive
    readonly property var devices: [{ key: "responsive", name: qsTr("Responsive") }].concat(responsive.deviceList)

    position: ToolBar.Header

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: Kirigami.Units.smallSpacing
        anchors.rightMargin: Kirigami.Units.smallSpacing
        spacing: Kirigami.Units.smallSpacing

        ComboBox {
            model: root.devices
            textRole: "name"
            valueRole: "key"
            currentIndex: indexOfValue(root.responsive.device)
            implicitContentWidthPolicy: ComboBox.WidestText
            Accessible.name: qsTr("Device")
            onActivated: root.responsive.selectDevice(currentValue)
        }
        SpinBox {
            from: 200; to: 4000; editable: true
            value: root.responsive.width
            Accessible.name: qsTr("Width")
            onValueModified: root.responsive.setSize(value, root.responsive.height)
            onEditingFinished: root.responsive.rememberSize()
        }
        Label { text: "×" }
        SpinBox {
            from: 200; to: 4000; editable: true
            value: root.responsive.height
            Accessible.name: qsTr("Height")
            onValueModified: root.responsive.setSize(root.responsive.width, value)
            onEditingFinished: root.responsive.rememberSize()
        }
        ToolButton {
            icon.name: "object-rotate-right"
            display: AbstractButton.IconOnly
            ToolTip.visible: hovered
            ToolTip.text: qsTr("Rotate")
            ToolTip.delay: 600
            Accessible.name: qsTr("Rotate")
            onClicked: root.responsive.rotate()
        }
        ToolButton {
            icon.name: "zoom-fit-best"
            display: AbstractButton.IconOnly
            checkable: true
            checked: root.responsive.zoomToFit
            ToolTip.visible: hovered
            ToolTip.text: qsTr("Zoom to Fit")
            ToolTip.delay: 600
            Accessible.name: qsTr("Zoom to Fit")
            onToggled: root.responsive.setZoomToFit(checked)
        }
        Item { Layout.fillWidth: true }
        ToolButton {
            icon.name: "window-close"
            display: AbstractButton.IconOnly
            ToolTip.visible: hovered
            ToolTip.text: qsTr("Close Responsive Mode (Ctrl+Shift+M)")
            ToolTip.delay: 600
            Accessible.name: qsTr("Close Responsive Mode")
            onClicked: root.responsive.setActive(false)
        }
    }
}
