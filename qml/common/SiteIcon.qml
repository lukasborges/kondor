import QtQuick
import org.kde.kirigami as Kirigami
import Kondor

Item {
    id: root

    required property url pageUrl
    property string fallback: "globe"

    readonly property bool hasStoredIcon: FaviconStore.revision >= 0 && FaviconStore.hasIcon(root.pageUrl)

    implicitWidth: Kirigami.Units.iconSizes.small
    implicitHeight: Kirigami.Units.iconSizes.small

    Image {
        id: image

        anchors.fill: parent
        source: root.hasStoredIcon
                ? "image://kondor-favicon/" + root.pageUrl.toString() + "#" + FaviconStore.revision
                : ""
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
