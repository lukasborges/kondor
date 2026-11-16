import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

ItemDelegate {
    id: root

    required property var login
    required property var tab

    signal activated()
    signal stepRequested(int step)

    objectName: "savedAccountRow"
    highlighted: ListView.isCurrentItem
    padding: Kirigami.Units.smallSpacing
    ToolTip.visible: hovered && !copyButtons.isAnyHovered
    ToolTip.text: qsTr("Fill")
    ToolTip.delay: 600
    //: %1 is the user name
    Accessible.name: qsTr("Fill %1").arg(login.username)
    onClicked: activated()
    Keys.onReturnPressed: activated()
    Keys.onEnterPressed: activated()
    Keys.onDownPressed: stepRequested(1)
    Keys.onUpPressed: stepRequested(-1)

    contentItem: RowLayout {
        spacing: Kirigami.Units.smallSpacing

        Kirigami.Icon {
            source: "user-identity"
            Layout.preferredWidth: Kirigami.Units.iconSizes.smallMedium
            Layout.preferredHeight: Kirigami.Units.iconSizes.smallMedium
        }

        Label {
            text: root.login.username
            elide: Text.ElideRight
            Layout.fillWidth: true
        }

        SavedLoginCopyButtons {
            id: copyButtons
            isRowHighlighted: root.highlighted
            login: root.login
            tab: root.tab
        }
    }
}
