import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

ApplicationWindow {
    id: root
    width: 520
    height: 380
    minimumWidth: 440
    minimumHeight: 320
    //: %1 is the application name
    title: qsTr("About %1").arg(Qt.application.displayName)
    visible: false

    required property TabModel tabModel
    property var mainWindow

    onClosing: function(close) {
        close.accepted = false
        root.visible = false
    }

    function showWindow() {
        root.visible = true
        root.raise()
        root.requestActivate()
    }

    function openUrl(url) {
        root.tabModel.addTab(false, url)
        raiseMainWindow()
    }

    function raiseMainWindow() {
        if (!root.mainWindow)
            return
        root.mainWindow.raise()
        root.mainWindow.requestActivate()
    }

    Shortcut {
        sequences: [StandardKey.Cancel]
        onActivated: root.close()
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Kirigami.Units.largeSpacing
        spacing: Kirigami.Units.largeSpacing

        RowLayout {
            spacing: Kirigami.Units.largeSpacing

            Kirigami.Icon {
                source: "kondor"
                fallback: "internet-web-browser"
                Layout.preferredWidth: Kirigami.Units.iconSizes.large
                Layout.preferredHeight: Kirigami.Units.iconSizes.large
            }

            ColumnLayout {
                spacing: 0
                Kirigami.Heading {
                    level: 2
                    text: Qt.application.displayName
                }
                Label {
                    text: qsTr("Version %1").arg(AboutInfo.version)
                }
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            TabBar {
                id: aboutTabBar
                Layout.fillWidth: true
                currentIndex: 0

                TabButton {
                    text: qsTr("About")
                    width: implicitWidth
                }
                TabButton {
                    text: qsTr("Components")
                    width: implicitWidth
                }
                TabButton {
                    text: qsTr("Authors")
                    width: implicitWidth
                }
            }

            Frame {
                Layout.fillWidth: true
                Layout.fillHeight: true

                StackLayout {
                    anchors.fill: parent
                    currentIndex: aboutTabBar.currentIndex

                    AboutTab {
                        onLinkActivated: function(url) { root.openUrl(url) }
                        onLicenseRequested: licenseWindow.show()
                    }
                    ComponentsTab {
                        onLinkActivated: function(url) { root.openUrl(url) }
                    }
                    AuthorsTab {
                        onLinkActivated: function(url) { root.openUrl(url) }
                    }
                }
            }
        }

        DialogButtonBox {
            Layout.fillWidth: true
            padding: 0

            Button {
                text: qsTr("Close")
                icon.name: "dialog-close"
                DialogButtonBox.buttonRole: DialogButtonBox.RejectRole
                onClicked: root.close()
            }
        }
    }

    LicenseWindow {
        id: licenseWindow
        transientParent: root
    }
}
