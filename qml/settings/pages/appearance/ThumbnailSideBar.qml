import QtQuick
import org.kde.kirigami as Kirigami

Rectangle {
    width: 36

    Column {
        x: 3
        y: 3
        spacing: 3

        Repeater {
            model: 5

            Rectangle {
                required property int index

                width: 30
                height: 6
                radius: 1
                color: index === 1 ? Kirigami.Theme.highlightColor : Qt.alpha(Kirigami.Theme.textColor, 0.15)
            }
        }
    }
}
