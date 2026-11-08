// #7 Site permissions — diálogo "Permissões de sites" (lista por site, com revogar).
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Rectangle {
    width: 640
    height: 460
    color: Kirigami.Theme.backgroundColor

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Kirigami.Units.largeSpacing
        spacing: Kirigami.Units.largeSpacing

        Kirigami.Heading { level: 3; text: "Permissões de sites" }
        Label {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            color: Kirigami.Theme.disabledTextColor
            text: "Decisões lembradas para sites visitados em abas normais. Abas privadas nunca guardam permissões."
        }
        TextField { Layout.fillWidth: true; placeholderText: "Filtrar por site…" }

        Frame {
            Layout.fillWidth: true
            Layout.fillHeight: true
            padding: 0
            Kirigami.Theme.colorSet: Kirigami.Theme.View
            background: Rectangle { color: Kirigami.Theme.backgroundColor; border.color: Kirigami.ColorUtils.linearInterpolation(Kirigami.Theme.backgroundColor, Kirigami.Theme.textColor, 0.2) }
            ListView {
                anchors.fill: parent
                clip: true
                section.property: "site"
                section.delegate: Kirigami.ListSectionHeader { required property string section; width: ListView.view.width; text: section }
                model: ListModel {
                    ListElement { site: "meet.jit.si"; perm: "Câmera"; ic: "camera-web"; granted: true }
                    ListElement { site: "meet.jit.si"; perm: "Microfone"; ic: "audio-input-microphone"; granted: true }
                    ListElement { site: "maps.example.com"; perm: "Localização"; ic: "mark-location"; granted: true }
                    ListElement { site: "news.example.com"; perm: "Notificações"; ic: "preferences-desktop-notification"; granted: false }
                }
                delegate: ItemDelegate {
                    required property string perm
                    required property string ic
                    required property bool granted
                    width: ListView.view.width
                    contentItem: RowLayout {
                        spacing: Kirigami.Units.largeSpacing
                        Kirigami.Icon { source: ic; Layout.preferredWidth: 22; Layout.preferredHeight: 22 }
                        Label { text: perm; Layout.fillWidth: true }
                        Label {
                            text: granted ? "Permitido" : "Bloqueado"
                            color: granted ? Kirigami.Theme.positiveTextColor : Kirigami.Theme.negativeTextColor
                        }
                        Button { text: "Revogar"; icon.name: "edit-undo"; flat: true }
                    }
                }
            }
        }

        DialogButtonBox {
            Layout.fillWidth: true
            standardButtons: DialogButtonBox.Close
            padding: 0
        }
    }
}
