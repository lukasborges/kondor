import QtQuick
import org.kde.kirigami as Kirigami
import Kondor

// Icon of an extension: a Breeze icon name, a file inside the package, or an
// image of the catalog. Falls back to the plugin icon while an image loads or
// when it fails.
Item {
    id: root

    property string source: ""
    property int size: Kirigami.Units.iconSizes.medium

    implicitWidth: root.size
    implicitHeight: root.size

    readonly property bool isImage: root.source.indexOf("://") >= 0

    Kirigami.Icon {
        anchors.fill: parent
        visible: !root.isImage || image.status !== Image.Ready
        source: root.isImage || root.source === "" ? "preferences-plugin" : root.source
    }

    Image {
        id: image
        anchors.fill: parent
        visible: status === Image.Ready
        source: root.isImage ? root.source : ""
        sourceSize: Qt.size(root.size * 2, root.size * 2)
        fillMode: Image.PreserveAspectFit
        asynchronous: true
    }
}
