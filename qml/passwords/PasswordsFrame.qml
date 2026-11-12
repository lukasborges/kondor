import QtQuick
import QtQuick.Controls
import org.kde.kirigami as Kirigami

Frame {
    padding: 0
    Kirigami.Theme.colorSet: Kirigami.Theme.View
    Kirigami.Theme.inherit: false
    background: Rectangle {
        color: Kirigami.Theme.backgroundColor
        border.color: Kirigami.ColorUtils.linearInterpolation(
                          Kirigami.Theme.backgroundColor, Kirigami.Theme.textColor, 0.2)
    }
}
