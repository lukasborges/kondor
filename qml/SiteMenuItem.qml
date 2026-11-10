import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

// A menu row for a web page: the site favicon (SiteIcon) followed by the
// elided title. Used by the History and Bookmarks menus.
MenuItem {
    id: root

    required property url pageUrl
    required property string label

    // `text` keeps the menu width and keyboard type-ahead working.
    text: label

    contentItem: RowLayout {
        spacing: Kirigami.Units.smallSpacing
        SiteIcon {
            pageUrl: root.pageUrl
            Layout.preferredWidth: Kirigami.Units.iconSizes.small
            Layout.preferredHeight: Kirigami.Units.iconSizes.small
        }
        Label {
            text: root.label
            elide: Text.ElideRight
            color: !root.enabled ? Kirigami.Theme.disabledTextColor
                : root.pressed ? Kirigami.Theme.highlightedTextColor
                : Kirigami.Theme.textColor
            Layout.fillWidth: true
            Layout.maximumWidth: Kirigami.Units.gridUnit * 18
        }
    }
}
