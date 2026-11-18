import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

ItemDelegate {
    id: row

    required property var entry
    readonly property bool isActive: highlighted || hovered

    signal closeRequested

    opacity: entry.isSleeping ? 0.6 : 1

    contentItem: RowLayout {
        spacing: Kirigami.Units.largeSpacing

        SiteIcon {
            pageUrl: row.entry.pageUrl
        }

        ColumnLayout {
            spacing: 0
            Layout.fillWidth: true

            Label {
                text: row.entry.titleHtml
                textFormat: Text.StyledText
                elide: Text.ElideRight
                color: row.highlighted ? Kirigami.Theme.highlightedTextColor : Kirigami.Theme.textColor
                Layout.fillWidth: true
            }

            Label {
                text: row.entry.addressHtml
                textFormat: Text.StyledText
                elide: Text.ElideMiddle
                font: Kirigami.Theme.smallFont
                color: row.highlighted ? Kirigami.Theme.highlightedTextColor : Kirigami.Theme.disabledTextColor
                Layout.fillWidth: true
            }
        }

        Kirigami.Icon {
            visible: row.entry.isCurrent
            source: "checkmark"
            Layout.preferredWidth: Kirigami.Units.iconSizes.small
            Layout.preferredHeight: Kirigami.Units.iconSizes.small
        }

        ToolButton {
            visible: row.isActive
            display: AbstractButton.IconOnly
            icon.name: "window-close-symbolic"
            ToolTip.visible: hovered
            ToolTip.text: qsTr("Close Tab")
            ToolTip.delay: 600
            Accessible.name: ToolTip.text
            onClicked: row.closeRequested()
        }
    }
}
