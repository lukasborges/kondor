// #376 "Custom…" in "Identify as:" asks for the user agent text; OK saves it for this site.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "common"

BrowserFrame {
    id: frame
    address: "https://intranet.example.com/"
    tabs: [{ title: "Intranet", icon: "internet-web-browser" }]
    FakePage {}

    Dialog {
        popupType: Popup.Item
        anchors.centerIn: parent
        width: 620
        modal: true
        title: "Custom Browser Identity"
        standardButtons: Dialog.Ok | Dialog.Cancel
        Component.onCompleted: open()
        contentItem: Kirigami.FormLayout {
            Label {
                Kirigami.FormData.label: "Site:"
                text: "intranet.example.com"
            }
            TextArea {
                Kirigami.FormData.label: "User agent:"
                Layout.preferredWidth: Kirigami.Units.gridUnit * 24
                wrapMode: TextEdit.WrapAnywhere
                text: "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
            }
        }
    }
}
