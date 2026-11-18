import QtQuick
import org.kde.kirigami as Kirigami
import Kondor

Item {
    id: adornment

    required property Tab tab
    required property TabModel tabModel
    required property var targetWindow
    required property real leadWidth

    signal labelDropped(real sceneX)

    anchors.fill: parent

    TabGroupBar {
        anchors.leftMargin: adornment.leadWidth + Kirigami.Units.smallSpacing
        group: adornment.tab.group
    }

    Loader {
        active: adornment.leadWidth > 0 && adornment.tab.group !== null
        x: 0
        y: 2
        z: 3
        width: adornment.leadWidth - 2
        height: adornment.height - 4
        sourceComponent: TabGroupLabel {
            group: adornment.tab.group
            tabModel: adornment.tabModel
            targetWindow: adornment.targetWindow
            onDropped: sceneX => adornment.labelDropped(sceneX)
        }
    }
}
