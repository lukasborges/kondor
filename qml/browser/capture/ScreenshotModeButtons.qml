import QtQuick
import QtQuick.Controls

Row {
    id: root

    property bool isFullPage: false

    signal modeChosen(bool fullPage)

    spacing: 0

    Button {
        text: qsTr("Visible Area")
        icon.name: "select-rectangular"
        checkable: true
        checked: !root.isFullPage
        autoExclusive: true
        onClicked: root.modeChosen(false)
    }

    Button {
        text: qsTr("Full Page")
        icon.name: "zoom-fit-page"
        checkable: true
        checked: root.isFullPage
        autoExclusive: true
        onClicked: root.modeChosen(true)
    }
}
