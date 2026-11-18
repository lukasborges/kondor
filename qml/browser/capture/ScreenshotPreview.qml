import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

ColumnLayout {
    id: root

    property var grabResult: null
    property bool isCapturing: false
    readonly property int roundingTolerance: 1
    readonly property bool isCut: image.sourceSize.height >= Screenshot.maximumHeight - roundingTolerance
    readonly property string sizeText: {
        const size = image.sourceSize
        const text = qsTr("%1 × %2").arg(size.width).arg(size.height)
        return isCut ? qsTr("%1 (cut at 16384 px)").arg(text) : text
    }

    spacing: Kirigami.Units.largeSpacing

    Rectangle {
        Layout.fillWidth: true
        Layout.preferredHeight: width * 0.55
        color: Kirigami.Theme.backgroundColor
        border.color: Kirigami.ColorUtils.linearInterpolation(
            Kirigami.Theme.backgroundColor, Kirigami.Theme.textColor, Kirigami.Theme.frameContrast)
        clip: true

        Image {
            id: image
            anchors.fill: parent
            anchors.margins: 1
            fillMode: Image.PreserveAspectFit
            source: root.grabResult ? root.grabResult.url : ""
            visible: !root.isCapturing
        }

        BusyIndicator {
            anchors.centerIn: parent
            running: root.isCapturing
        }
    }

    Label {
        Layout.alignment: Qt.AlignHCenter
        text: root.isCapturing || !root.grabResult ? "" : root.sizeText
        color: Kirigami.Theme.disabledTextColor
    }
}
