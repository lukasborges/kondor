import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

Rectangle {
    id: root

    property alias text: hintLabel.text
    property string iconName: "view-fullscreen"
    property string actionText
    property string actionIconName
    property string actionToolTip
    property int duration: 3000
    property real shownOpacity: 0.92
    property bool isOutlined: false

    signal actionTriggered

    function show() {
        opacity = shownOpacity
        hideTimer.restart()
    }

    function hide() {
        hideTimer.stop()
        opacity = 0
    }

    function announce(message) {
        Accessible.announce(message)
    }

    y: Kirigami.Units.gridUnit
    width: hintRow.implicitWidth + Kirigami.Units.largeSpacing * 4
    height: hintRow.implicitHeight + Kirigami.Units.largeSpacing * 2
    radius: Kirigami.Units.cornerRadius
    Kirigami.Theme.colorSet: Kirigami.Theme.Complementary
    Kirigami.Theme.inherit: false
    color: Kirigami.Theme.backgroundColor
    border.width: isOutlined ? 1 : 0
    border.color: Qt.alpha(Kirigami.Theme.textColor, 0.3)
    opacity: 0
    visible: opacity > 0

    Behavior on opacity {
        NumberAnimation { duration: Kirigami.Units.shortDuration }
    }

    Timer {
        id: hideTimer
        interval: root.duration
        onTriggered: root.opacity = 0
    }

    HoverHandler {
        onHoveredChanged: {
            if (hovered)
                hideTimer.stop()
            else if (root.opacity > 0)
                hideTimer.restart()
        }
    }

    RowLayout {
        id: hintRow
        anchors.centerIn: parent
        spacing: Kirigami.Units.largeSpacing

        Kirigami.Icon {
            visible: root.iconName.length > 0
            source: root.iconName
            Layout.preferredWidth: Kirigami.Units.iconSizes.smallMedium
            Layout.preferredHeight: Kirigami.Units.iconSizes.smallMedium
        }

        Label {
            id: hintLabel
            color: Kirigami.Theme.textColor
        }

        Button {
            visible: root.actionText.length > 0
            text: root.actionText
            icon.name: root.actionIconName
            focusPolicy: Qt.NoFocus
            ToolTip.visible: hovered
            ToolTip.delay: 600
            ToolTip.text: root.actionToolTip
            onClicked: root.actionTriggered()
        }
    }
}
