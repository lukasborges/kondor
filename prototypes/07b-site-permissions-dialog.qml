// #7 Site permissions — "Site Permissions" dialog (grouped by site, with revoke).
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

        Kirigami.Heading { level: 3; text: "Site Permissions" }
        Label {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            color: Kirigami.Theme.disabledTextColor
            text: "Decisions remembered for sites visited in normal tabs. Private tabs never keep permissions."
        }
        TextField { Layout.fillWidth: true; placeholderText: "Filter by site…" }

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
                    ListElement { site: "meet.jit.si"; perm: "Camera"; ic: "camera-web"; granted: true }
                    ListElement { site: "meet.jit.si"; perm: "Microphone"; ic: "audio-input-microphone"; granted: true }
                    ListElement { site: "maps.example.com"; perm: "Location"; ic: "mark-location"; granted: true }
                    ListElement { site: "news.example.com"; perm: "Notifications"; ic: "preferences-desktop-notification"; granted: false }
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
                            text: granted ? "Allowed" : "Blocked"
                            color: granted ? Kirigami.Theme.positiveTextColor : Kirigami.Theme.negativeTextColor
                        }
                        Button { text: "Revoke"; icon.name: "edit-undo"; flat: true }
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
