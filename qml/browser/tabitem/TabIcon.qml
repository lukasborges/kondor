import QtQuick
import QtQuick.Controls
import org.kde.kirigami as Kirigami
import Kondor

Item {
    id: root

    required property Tab tab

    readonly property bool isBusy: !!tab && tab.loading && !tab.crashed

    implicitWidth: 16
    implicitHeight: 16

    TabInfo {
        id: info
        tab: root.tab
    }

    Kirigami.Icon {
        anchors.fill: parent
        visible: !root.isBusy
        source: info.iconSource
    }

    BusyIndicator {
        anchors.fill: parent
        visible: root.isBusy
        running: visible
    }
}
