// #211 / #212: the "Tabs" picker of Settings → General → Appearance. One thumbnail per style,
// like the KDE System Settings appearance pages (KCM grid delegates). Static.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Grid {
    id: picker

    property bool withVertical: false
    property string current: "floating"
    property string focused: ""

    readonly property var styles: [
        { id: "floating", name: "Floating" },
        { id: "below", name: "Below Address Bar" },
        { id: "vertical", name: "Side Bar" },
        { id: "classic", name: "Classic" }
    ].filter(s => withVertical || s.id !== "vertical")

    columns: 2
    spacing: Kirigami.Units.largeSpacing

    component Thumbnail: Rectangle {
        property string style
        readonly property bool vertical: style === "vertical"
        readonly property bool below: style === "below"
        width: Kirigami.Units.gridUnit * 8
        height: Kirigami.Units.gridUnit * 5
        radius: Kirigami.Units.cornerRadius
        color: page.color
        border.color: Qt.alpha(Kirigami.Theme.textColor, 0.2)
        clip: true

        Kirigami.Theme.colorSet: Kirigami.Theme.View
        Kirigami.Theme.inherit: false
        Rectangle { id: page; visible: false; color: Kirigami.Theme.backgroundColor }

        Column {
            anchors.fill: parent
            anchors.margins: 1
            Rectangle {
                visible: !parent.parent.vertical && !parent.parent.below
                width: parent.width
                height: 14
                color: headerColors.backgroundColor
                Row {
                    x: 4; y: 3
                    spacing: 2
                    Repeater {
                        model: 3
                        Rectangle {
                            required property int index
                            width: 26; height: 9
                            radius: style === "classic" ? 0 : 2
                            color: style === "classic" ? (index === 1 ? windowColors.backgroundColor : Qt.darker(headerColors.backgroundColor, 1.05))
                                 : (index === 1 ? Qt.alpha(Kirigami.Theme.highlightColor, 0.25) : "transparent")
                            border.color: index === 1 && style !== "classic" ? Kirigami.Theme.highlightColor : "transparent"
                            Rectangle {
                                visible: style === "classic" && index === 1
                                width: parent.width; height: 2
                                color: Kirigami.Theme.highlightColor
                            }
                        }
                    }
                }
            }
            Rectangle {
                width: parent.width
                height: 12
                color: windowColors.backgroundColor
                Rectangle { x: 18; y: 3; width: parent.width - 26; height: 6; radius: 2; color: page.color; border.color: Qt.alpha(Kirigami.Theme.textColor, 0.25) }
            }
            Rectangle {
                visible: parent.parent.below
                width: parent.width
                height: 13
                color: windowColors.backgroundColor
                Row {
                    x: 4; y: 2
                    spacing: 2
                    Repeater {
                        model: 3
                        Rectangle {
                            required property int index
                            width: 26; height: 9; radius: 2
                            color: index === 1 ? Qt.alpha(Kirigami.Theme.highlightColor, 0.25) : "transparent"
                            border.color: index === 1 ? Kirigami.Theme.highlightColor : "transparent"
                        }
                    }
                }
            }
            Row {
                visible: parent.parent.vertical
                Rectangle {
                    width: 36; height: Kirigami.Units.gridUnit * 5 - 14
                    color: windowColors.backgroundColor
                    Column {
                        x: 3; y: 3
                        spacing: 3
                        Repeater {
                            model: 5
                            Rectangle {
                                required property int index
                                width: 30; height: 6; radius: 1
                                color: index === 1 ? Kirigami.Theme.highlightColor : Qt.alpha(Kirigami.Theme.textColor, 0.15)
                            }
                        }
                    }
                }
            }
        }

        Item {
            id: headerColors
            Kirigami.Theme.colorSet: Kirigami.Theme.Header
            Kirigami.Theme.inherit: false
            readonly property color backgroundColor: Kirigami.Theme.backgroundColor
        }
        Item {
            id: windowColors
            Kirigami.Theme.colorSet: Kirigami.Theme.Window
            Kirigami.Theme.inherit: false
            readonly property color backgroundColor: Kirigami.Theme.backgroundColor
        }
    }

    Repeater {
        model: picker.styles
        delegate: ItemDelegate {
            required property var modelData
            readonly property bool selected: modelData.id === picker.current
            checkable: true
            checked: selected
            highlighted: selected
            focus: modelData.id === picker.focused
            Accessible.name: modelData.name
            Accessible.role: Accessible.RadioButton
            padding: Kirigami.Units.smallSpacing
            contentItem: ColumnLayout {
                spacing: Kirigami.Units.smallSpacing
                Thumbnail { style: modelData.id; Layout.alignment: Qt.AlignHCenter }
                Label {
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignHCenter
                    text: modelData.name
                    elide: Text.ElideRight
                }
            }
        }
    }
}
