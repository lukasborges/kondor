import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

ColumnLayout {
    id: root
    spacing: Kirigami.Units.largeSpacing

    signal linkActivated(string url)

    Label {
        Layout.fillWidth: true
        wrapMode: Text.WordWrap
        textFormat: Text.RichText
        linkColor: Kirigami.Theme.linkColor
        text: qsTr("Please use %1 to report bugs.")
              .arg("<a href=\"https://github.com/lukasborges/kondor/issues\">https://github.com/lukasborges/kondor/issues</a>")
        onLinkActivated: function(link) {
            root.linkActivated(link)
        }
    }

    Repeater {
        model: [
            {
                name: "Lucas Borges",
                role: qsTr("Maintainer"),
                homepage: "https://github.com/lukasborges"
            }
        ]

        delegate: RowLayout {
            required property var modelData

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 0

                Label {
                    font.bold: true
                    text: modelData.name
                }
                Label {
                    text: modelData.role
                    color: Kirigami.Theme.disabledTextColor
                }
            }

            ToolButton {
                icon.name: "internet-services"
                display: AbstractButton.IconOnly
                ToolTip.visible: hovered
                ToolTip.text: qsTr("Visit Author's Homepage")
                ToolTip.delay: 600
                onClicked: root.linkActivated(modelData.homepage)
            }
        }
    }

    Item { Layout.fillHeight: true }
}
