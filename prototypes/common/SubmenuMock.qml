// A static submenu drawn like a Breeze Menu. Prototypes use it next to an open
// Menu: opening a second Menu would close the first one.
import QtQuick
import QtQuick.Controls
import org.kde.kirigami as Kirigami

Popup {
    id: control
    default property alias items: column.data
    property real menuWidth: 280

    popupType: Popup.Item
    closePolicy: Popup.NoAutoClose
    padding: 4
    width: menuWidth
    height: column.implicitHeight + topPadding + bottomPadding
    Kirigami.Theme.colorSet: Kirigami.Theme.View
    Kirigami.Theme.inherit: false

    contentItem: Column {
        id: column
        onChildrenChanged: {
            for (let i = 0; i < children.length; ++i)
                children[i].width = Qt.binding(function() { return column.width })
        }
    }

    background: Kirigami.ShadowedRectangle {
        radius: Kirigami.Units.cornerRadius
        color: Kirigami.Theme.backgroundColor
        border.color: Kirigami.ColorUtils.linearInterpolation(Kirigami.Theme.backgroundColor, Kirigami.Theme.textColor, Kirigami.Theme.frameContrast)
        border.width: 1
        shadow.xOffset: 0
        shadow.yOffset: 2
        shadow.color: Qt.rgba(0, 0, 0, 0.3)
        shadow.size: 8
    }
}
