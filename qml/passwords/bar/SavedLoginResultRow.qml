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

    objectName: "savedLoginResultRow"
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

        SiteIcon {
            pageUrl: root.login.origin
            Layout.leftMargin: Kirigami.Units.smallSpacing / 2
            Layout.rightMargin: Kirigami.Units.smallSpacing / 2
        }

        ColumnLayout {
            spacing: 0
            Layout.fillWidth: true

            Label {
                text: root.login.host
                elide: Text.ElideRight
                Layout.fillWidth: true
            }

            Label {
                text: root.login.username
                elide: Text.ElideRight
                color: Kirigami.Theme.disabledTextColor
                font: Kirigami.Theme.smallFont
                Layout.fillWidth: true
            }
        }

        SavedLoginCopyButtons {
            id: copyButtons
            isRowHighlighted: root.highlighted
            login: root.login
            tab: root.tab
        }
    }
}
