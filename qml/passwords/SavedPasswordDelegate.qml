import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

ItemDelegate {
    id: root

    required property string origin
    required property string username
    required property RevealedPasswords revealed
    signal deleteRequested(string origin, string username)

    readonly property bool shown: root.revealed.isRevealed(root.origin, root.username)

    highlighted: ListView.isCurrentItem
    width: ListView.view.width

    contentItem: RowLayout {
        spacing: Kirigami.Units.largeSpacing

        Label {
            text: root.username
            Layout.preferredWidth: Kirigami.Units.gridUnit * 10
            elide: Text.ElideRight
        }

        Label {
            Layout.fillWidth: true
            text: root.shown ? root.revealed.passwordOf(root.origin, root.username) : "••••••••••"
            font.family: root.shown ? "monospace" : Kirigami.Theme.defaultFont.family
            elide: Text.ElideRight
        }

        RowToolButton {
            icon.name: root.shown ? "view-hidden" : "view-visible"
            text: root.shown ? qsTr("Hide Password") : qsTr("Show Password")
            onClicked: root.revealed.toggleReveal(root.origin, root.username)
        }

        RowToolButton {
            icon.name: "edit-copy"
            text: qsTr("Copy Password")
            onClicked: PasswordStore.copyPassword(root.origin, root.username)
        }

        RowToolButton {
            icon.name: "edit-delete"
            text: qsTr("Delete")
            onClicked: root.deleteRequested(root.origin, root.username)
        }
    }
}
