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
        visible: !root.isBusy && !info.hasPageIcon
        source: info.iconSource
        opacity: info.isSleeping ? 0.5 : 1
    }

    SiteIcon {
        anchors.fill: parent
        visible: !root.isBusy && info.hasPageIcon && pageIcon.status !== Image.Ready
        pageUrl: root.tab?.url ?? ""
        fallback: info.iconSource
        opacity: info.isSleeping ? 0.5 : 1
    }

    Image {
        id: pageIcon
        anchors.fill: parent
        visible: !root.isBusy && info.hasPageIcon && status === Image.Ready
        source: info.pageIconSource
        cache: false
        sourceSize.width: width
        sourceSize.height: height
        fillMode: Image.PreserveAspectFit
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

    Rectangle {
        visible: root.showsEmblem && info.isAgentTab
        width: 12
        height: 12
        radius: 6
        anchors { right: parent.right; bottom: parent.bottom; rightMargin: -4; bottomMargin: -4 }
        color: Kirigami.Theme.neutralTextColor

        Kirigami.Icon {
            anchors.centerIn: parent
            width: 8
            height: 8
            source: "automated-tasks"
            color: "white"
            isMask: true
        }
    }

    BusyIndicator {
        anchors.fill: parent
        visible: root.isBusy
        running: visible
    }
}
