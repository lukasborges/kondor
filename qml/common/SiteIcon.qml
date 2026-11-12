import QtQuick
import org.kde.kirigami as Kirigami
import Kondor

Item {
    id: root

    required property url pageUrl
    property string fallback: "globe"

    implicitWidth: Kirigami.Units.iconSizes.small
    implicitHeight: Kirigami.Units.iconSizes.small

    Image {
        id: image

        anchors.fill: parent
        source: "image://kondor-favicon/" + root.pageUrl.toString()
                + "#" + FaviconStore.revision
        cache: false
        sourceSize.width: width
        sourceSize.height: height
        fillMode: Image.PreserveAspectFit
    }

    Kirigami.Icon {
        anchors.fill: parent
        source: root.fallback
        visible: image.status !== Image.Ready
    }
}
