import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

Window {
    id: root
    width: 600
    height: 500
    title: qsTr("License Agreement")

    Shortcut {
        sequences: [StandardKey.Cancel]
        onActivated: root.close()
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Kirigami.Units.largeSpacing
        spacing: Kirigami.Units.largeSpacing

        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true

            TextArea {
                text: AboutInfo.licenseText
                readOnly: true
                selectByMouse: true
                wrapMode: TextArea.NoWrap
                font.family: "monospace"
            }
        }

        DialogButtonBox {
            Layout.fillWidth: true
            padding: 0

            Button {
                text: qsTr("Close")
                icon.name: "dialog-close"
                DialogButtonBox.buttonRole: DialogButtonBox.RejectRole
                onClicked: root.close()
            }
        }
    }
}
