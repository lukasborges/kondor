import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

RowLayout {
    id: root

    property string title: ""

    signal backRequested()

    Layout.margins: Kirigami.Units.smallSpacing

    ToolButton {
        display: AbstractButton.IconOnly
        icon.name: Qt.application.layoutDirection === Qt.RightToLeft ? "go-next-symbolic" : "go-previous-symbolic"
        ToolTip.visible: hovered
        ToolTip.text: qsTr("Back")
        ToolTip.delay: 600
        Accessible.name: ToolTip.text
        onClicked: root.backRequested()
    }

    Kirigami.Heading {
        level: 4
        text: root.title
        elide: Text.ElideRight
        Layout.fillWidth: true
    }
}
