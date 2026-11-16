import QtQuick
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

RowLayout {
    id: root

    required property var login
    required property var tab
    property bool isRowHighlighted: false

    readonly property bool isAnyHovered: copyUsernameButton.hovered || copyPasswordButton.hovered

    spacing: Kirigami.Units.smallSpacing

    CopyFeedbackButton {
        id: copyUsernameButton
        isOnHighlight: root.isRowHighlighted
        iconName: "edit-copy"
        tooltipText: qsTr("Copy Username")
        copiedTooltipText: qsTr("Copied.")
        announcement: qsTr("Username copied")
        //: %1 is the user name
        accessibleName: qsTr("Copy Username for %1").arg(root.login.username)
        onCopyRequested: root.tab.passwords.copyUsername(root.login.username)
    }

    CopyFeedbackButton {
        id: copyPasswordButton
        objectName: "copyPasswordButton"
        isOnHighlight: root.isRowHighlighted
        iconName: "password-copy"
        tooltipText: qsTr("Copy Password")
        copiedTooltipText: qsTr("Copied. Cleared in 30 seconds.")
        announcement: qsTr("Password copied, cleared in 30 seconds")
        //: %1 is the user name
        accessibleName: qsTr("Copy Password for %1").arg(root.login.username)
        onCopyRequested: root.tab.passwords.copyPassword(root.login.origin, root.login.username)
    }
}
