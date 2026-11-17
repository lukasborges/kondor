import QtQuick
import org.kde.kirigami as Kirigami
import Kondor

FullScreenHint {
    id: root

    required property bool isWindowFullScreen

    y: Kirigami.Units.gridUnit * 2
    iconName: ""
    //: Shown for a few seconds after the toolbars get hidden
    text: qsTr("Toolbars hidden")
    actionText: qsTr("Show Toolbars")
    actionIconName: "view-visible"
    actionToolTip: isWindowFullScreen
        ? qsTr("F11, or move the pointer to the top")
        : qsTr("Ctrl+Shift+F, or move the pointer to the top")
    duration: 5000
    shownOpacity: 0.95
    isOutlined: true

    Connections {
        target: Settings
        function onHideToolbarsChanged() {
            if (Settings.hideToolbars)
                root.announce(qsTr("Toolbars hidden. Move the pointer to the top edge or press Ctrl+L to show them."))
        }
    }
}
