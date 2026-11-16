import QtQuick
import QtQuick.Controls
import org.kde.kirigami as Kirigami
import Kondor

Item {
    id: root

    required property Tab tab

    property bool showsEmblem: false

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
        opacity: info.isSleeping ? 0.5 : 1
    }

    Kirigami.Icon {
        visible: root.showsEmblem && info.hasSoundState
        width: 10
        height: 10
        anchors { right: parent.right; bottom: parent.bottom; rightMargin: -3; bottomMargin: -3 }
        source: info.isMuted ? "audio-volume-muted-symbolic" : "audio-volume-high-symbolic"
        opacity: info.isSleeping ? 0.5 : 1
    }

    BusyIndicator {
        anchors.fill: parent
        visible: root.isBusy
        running: visible
    }
}
