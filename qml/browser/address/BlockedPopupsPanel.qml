import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

ToolbarPopup {
    id: root

    property TabPopups popups: null

    function withoutScheme(url) {
        const schemeEnd = url.indexOf("://")
        return schemeEnd < 0 ? url : url.slice(schemeEnd + 3)
    }

    width: 340
    padding: Kirigami.Units.largeSpacing

    contentItem: ColumnLayout {
        spacing: Kirigami.Units.smallSpacing

        Kirigami.Heading {
            level: 4
            text: qsTr("Blocked Pop-ups")
        }

        Repeater {
            model: root.popups ? root.popups.blockedUrls : []

            delegate: BlockedPopupRow {
                required property string modelData
                Layout.fillWidth: true
                url: modelData
                text: root.withoutScheme(modelData)
                onClicked: root.popups.openBlocked(modelData)
            }
        }

        Kirigami.Separator {
            Layout.fillWidth: true
            visible: allowSwitch.visible
        }

        PopupAllowSwitch {
            id: allowSwitch
            Layout.fillWidth: true
            popups: root.popups
        }
    }
}
