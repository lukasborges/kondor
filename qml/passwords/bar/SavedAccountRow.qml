import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

ItemDelegate {
    id: root

    required property string username
    required property var tab

    signal fillRequested()
    signal stepRequested(int step)

    function fill() {
        tab.passwords.fill(username)
        fillRequested()
    }

    objectName: "savedAccountRow"
    Layout.fillWidth: true
    padding: Kirigami.Units.smallSpacing
    ToolTip.visible: hovered && !copyUsernameButton.hovered && !copyPasswordButton.hovered
    ToolTip.text: qsTr("Fill")
    ToolTip.delay: 600
    //: %1 is the user name
    Accessible.name: qsTr("Fill %1").arg(username)
    onClicked: fill()
    Keys.onReturnPressed: fill()
    Keys.onEnterPressed: fill()
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
            text: root.username
            elide: Text.ElideRight
            Layout.fillWidth: true
        }

        CopyFeedbackButton {
            id: copyUsernameButton
            iconName: "edit-copy"
            tooltipText: qsTr("Copy Username")
            copiedTooltipText: qsTr("Copied.")
            announcement: qsTr("Username copied")
            //: %1 is the user name
            accessibleName: qsTr("Copy Username for %1").arg(root.username)
            onCopyRequested: root.tab.passwords.copyUsername(root.username)
        }

        CopyFeedbackButton {
            id: copyPasswordButton
            objectName: "copyPasswordButton"
            iconName: "password-copy"
            tooltipText: qsTr("Copy Password")
            copiedTooltipText: qsTr("Copied. Cleared in 30 seconds.")
            announcement: qsTr("Password copied, cleared in 30 seconds")
            //: %1 is the user name
            accessibleName: qsTr("Copy Password for %1").arg(root.username)
            onCopyRequested: root.tab.passwords.copyPassword(root.username)
        }
    }
}
