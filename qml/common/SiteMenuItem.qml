import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

MenuItem {
    id: root

    required property url pageUrl
    required property string label

    text: label

    contentItem: RowLayout {
        Item {
            Layout.preferredWidth: (root.ListView.view && root.ListView.view.hasCheckables) || root.checkable
                ? root.indicator.width : Kirigami.Units.smallSpacing
        }
        SiteIcon {
            pageUrl: root.pageUrl
            Layout.alignment: Qt.AlignVCenter
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
            Layout.preferredWidth: Math.min(implicitWidth, Kirigami.Units.gridUnit * 18)
        }
        Item {
            Layout.preferredWidth: Kirigami.Units.smallSpacing
        }
    }
}
