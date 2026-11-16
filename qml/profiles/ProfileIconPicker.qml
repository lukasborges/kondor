import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

RowLayout {
    id: root

    property string iconName: ""

    readonly property var labels: ({
        "im-user": qsTr("Person"),
        "go-home": qsTr("Home"),
        "view-pim-tasks": qsTr("Work"),
        "globe": qsTr("World"),
        "favorite": qsTr("Star"),
        "games-config-board": qsTr("Games"),
        "code-context": qsTr("Development"),
        "flag": qsTr("Flag")
    })

    spacing: Kirigami.Units.smallSpacing

    ButtonGroup { id: group }

    Repeater {
        model: UserProfiles.iconNames()
        delegate: ToolButton {
            id: choice
            required property string modelData
            icon.name: modelData
            display: AbstractButton.IconOnly
            checkable: true
            checked: modelData === root.iconName
            ButtonGroup.group: group
            ToolTip.visible: hovered
            ToolTip.text: root.labels[modelData]
            ToolTip.delay: 600
            Accessible.name: ToolTip.text
            onClicked: root.iconName = modelData
        }
    }
}
