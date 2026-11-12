import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

ColumnLayout {
    id: root

    required property var sites

    signal siteRemoved(string site)

    visible: root.sites.length > 0
    spacing: Kirigami.Units.smallSpacing

    Label {
        text: qsTr("Turned off on:")
    }

    Repeater {
        model: root.sites

        delegate: RowLayout {
            id: siteRow
            required property string modelData
            Layout.fillWidth: true
            Layout.leftMargin: Kirigami.Units.largeSpacing

            Label {
                Layout.fillWidth: true
                text: siteRow.modelData
                elide: Text.ElideMiddle
            }
            ToolButton {
                icon.name: "list-remove"
                text: qsTr("Remove")
                display: AbstractButton.TextBesideIcon
                onClicked: root.siteRemoved(siteRow.modelData)
            }
        }
    }
}
