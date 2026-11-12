import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

Rectangle {
    id: root

    property alias text: hintLabel.text

    y: Kirigami.Units.gridUnit
    width: hintRow.implicitWidth + Kirigami.Units.largeSpacing * 4
    height: hintRow.implicitHeight + Kirigami.Units.largeSpacing * 2
    radius: Kirigami.Units.cornerRadius
    Kirigami.Theme.colorSet: Kirigami.Theme.Complementary
    Kirigami.Theme.inherit: false
    color: Kirigami.Theme.backgroundColor
    opacity: 0
    visible: opacity > 0

    function show() {
        opacity = 0.92
        hideTimer.restart()
    }

    function hide() {
        hideTimer.stop()
        opacity = 0
    }

    Behavior on opacity {
        NumberAnimation { duration: Kirigami.Units.shortDuration }
    }

    Timer {
        id: hideTimer
        interval: 3000
        onTriggered: root.opacity = 0
    }

    RowLayout {
        id: hintRow
        anchors.centerIn: parent
        spacing: Kirigami.Units.largeSpacing

        Kirigami.Icon {
            source: "view-fullscreen"
            Layout.preferredWidth: Kirigami.Units.iconSizes.smallMedium
            Layout.preferredHeight: Kirigami.Units.iconSizes.smallMedium
        }

        Label {
            id: hintLabel
            color: Kirigami.Theme.textColor
        }
    }
}
