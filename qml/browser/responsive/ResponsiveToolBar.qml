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

    function ratioLabel(ratio) {
        return qsTr("%1×").arg(Qt.locale().toString(ratio, "g", 4))
    }

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
            onValueModified: root.responsive.commitSize(value, root.responsive.height)
        }
        Label { text: "×" }
        SpinBox {
            from: 200; to: 4000; editable: true
            value: root.responsive.height
            Accessible.name: qsTr("Height")
            onValueModified: root.responsive.commitSize(root.responsive.width, value)
        }
        ComboBox {
            model: root.responsive.ratioList
            currentIndex: model.indexOf(root.responsive.ratio)
            implicitContentWidthPolicy: ComboBox.WidestText
            displayText: root.ratioLabel(root.responsive.ratio)
            ToolTip.visible: hovered
            ToolTip.text: qsTr("Device pixel ratio")
            ToolTip.delay: 600
            Accessible.name: qsTr("Device pixel ratio")
            delegate: ItemDelegate {
                required property real modelData
                width: ListView.view ? ListView.view.width : implicitWidth
                text: root.ratioLabel(modelData)
                enabled: modelData <= root.responsive.maxRatio
                highlighted: modelData === root.responsive.ratio
            }
            onActivated: root.responsive.setRatio(model[currentIndex])
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
