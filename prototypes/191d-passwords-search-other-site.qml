// #191 Filling a login saved for another site asks first, so a look-alike page cannot get it with one click.
import QtQuick
import QtQuick.Controls
import org.kde.kirigami as Kirigami
import "common"

BrowserFrame {
    id: frame
    height: 640
    address: "https://accounts.example.org/signin/identifier"
    tabs: [{ title: "Sign in · Example Accounts", icon: "internet-web-browser" }]
    addressLeft: [
        ToolButton { icon.name: "security-high"; display: AbstractButton.IconOnly; flat: true; implicitWidth: 28; implicitHeight: 28 }
    ]
    addressRight: [
        ToolButton { icon.name: "dialog-password"; display: AbstractButton.IconOnly; flat: true; checked: false; implicitWidth: 28; implicitHeight: 28 }
    ]
    SignInPageMock {}

    Dialog {
        popupType: Popup.Item
        anchors.centerIn: parent
        width: Kirigami.Units.gridUnit * 22
        modal: true
        dim: true
        title: "Fill Password from Another Site"
        Component.onCompleted: open()
        contentItem: Label {
            text: "This password was saved for <b>id.example.org</b>. Fill it on <b>accounts.example.org</b>?"
            wrapMode: Text.WordWrap
        }
        footer: DialogButtonBox {
            Button { text: "Fill"; icon.name: "dialog-password"; DialogButtonBox.buttonRole: DialogButtonBox.AcceptRole }
            Button { text: "Cancel"; icon.name: "dialog-cancel"; focus: true; DialogButtonBox.buttonRole: DialogButtonBox.RejectRole }
        }
    }
}
