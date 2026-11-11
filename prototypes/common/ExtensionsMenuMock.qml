// The toolbar "Extensions" menu of #107, open under its button (left of the main menu button).
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Item {
    id: root
    anchors.fill: parent

    Menu {
        popupType: Popup.Item
        closePolicy: Popup.NoAutoClose
        x: root.width - width - 44
        y: -6
        width: 280
        visible: true

        MenuSeparator {
            contentItem: Kirigami.ListSectionHeader { text: "Video Speed Controller"; icon.name: "media-playback-start" }
        }
        MenuItem { text: "Faster"; icon.name: "media-seek-forward" }
        MenuItem { text: "Slower"; icon.name: "media-seek-backward" }
        MenuItem { text: "Show Speed Overlay"; checkable: true; checked: true }
        MenuItem { text: "Run on www.youtube.com"; checkable: true; checked: true }
        MenuSeparator {
            contentItem: Kirigami.ListSectionHeader { text: "Dark Mode"; icon.name: "weather-clear-night" }
        }
        MenuItem { text: "Dim Images"; checkable: true; checked: false }
        MenuItem { text: "Run on www.youtube.com"; checkable: true; checked: true }
        MenuSeparator {}
        MenuItem { text: "Manage Extensions…"; icon.name: "preferences-plugin" }
    }
}
