import QtQuick
import org.kde.kirigami as Kirigami
import Kondor

// A site favicon from Kondor's FaviconStore, with a Breeze fallback icon while
// the stored image is missing or still loading. Used for bookmarks (toolbar and
// manager) and the New Tab page tiles.
Item {
    id: root

    required property url pageUrl
    property string fallback: "globe"

    implicitWidth: Kirigami.Units.iconSizes.small
    implicitHeight: Kirigami.Units.iconSizes.small

    Image {
        id: image

        anchors.fill: parent
        // The revision suffix makes the image reload when a new favicon
        // arrives; the provider ignores the fragment.
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
