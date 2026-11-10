import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

// "About Kondor Browser" window, modelled on KDE's KAboutApplicationDialog:
// icon, name and version in the header, About / Components / Authors tabs and
// a Close button.
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
    // The main window, raised after a link opens a tab there.
    property var mainWindow

    onClosing: function(close) {
        // Do not destroy: just hide, so the window reopens on the same tab.
        close.accepted = false
        root.visible = false
    }

    function showWindow() {
        root.visible = true
        root.raise()
        root.requestActivate()
    }

    // Links always open in a normal tab, never in a private one.
    function openUrl(url) {
        root.tabModel.addTab(false, url)
        if (root.mainWindow) {
            root.mainWindow.raise()
            root.mainWindow.requestActivate()
        }
    }

    Shortcut {
        sequences: [StandardKey.Cancel]
        onActivated: root.close()
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Kirigami.Units.largeSpacing
        spacing: Kirigami.Units.largeSpacing

        // ── Header ───────────────────────────────────────────────────────
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

        // ── Tabs ─────────────────────────────────────────────────────────
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

                    // ── About ────────────────────────────────────────────
                    ColumnLayout {
                        spacing: Kirigami.Units.largeSpacing

                        Label {
                            text: qsTr("Web Browser")
                        }
                        Label {
                            text: qsTr("© 2026 The Kondor Developers")
                        }
                        Label {
                            Layout.fillWidth: true
                            textFormat: Text.RichText
                            linkColor: Kirigami.Theme.linkColor
                            text: "<a href=\"https://github.com/lukasborges/kondor\">https://github.com/lukasborges/kondor</a>"
                            onLinkActivated: function(link) {
                                root.openUrl(link)
                            }
                        }
                        Label {
                            Layout.fillWidth: true
                            textFormat: Text.RichText
                            linkColor: Kirigami.Theme.linkColor
                            text: "<a href=\"#license\">" + qsTr("License: GNU General Public License Version 3") + "</a>"
                            onLinkActivated: function(link) {
                                if (link === "#license")
                                    licenseWindow.show()
                            }
                        }

                        Item { Layout.fillHeight: true }
                    }

                    // ── Components ───────────────────────────────────────
                    ScrollView {
                        id: componentsPage
                        contentWidth: availableWidth
                        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

                        ColumnLayout {
                            width: componentsPage.availableWidth
                            spacing: Kirigami.Units.largeSpacing

                            Repeater {
                                model: [
                                    {
                                        name: "Qt",
                                        version: AboutInfo.qtRuntimeVersion,
                                        description: qsTr("Using %1 (built against %2)")
                                                     .arg(AboutInfo.qtRuntimeVersion)
                                                     .arg(AboutInfo.qtBuildVersion),
                                        link: "https://www.qt.io/"
                                    },
                                    {
                                        name: "Qt WebEngine",
                                        version: AboutInfo.webEngineVersion,
                                        description: qsTr("Chromium %1").arg(AboutInfo.chromiumVersion),
                                        link: "https://doc.qt.io/qt-6/qtwebengine-index.html"
                                    },
                                    {
                                        name: "Kirigami",
                                        version: "",
                                        description: qsTr("KDE user interface framework, used for the Breeze look"),
                                        link: "https://develop.kde.org/frameworks/kirigami/"
                                    },
                                    {
                                        name: qsTr("Windowing System"),
                                        version: "",
                                        description: AboutInfo.windowingSystem,
                                        link: ""
                                    },
                                    {
                                        name: qsTr("Operating System"),
                                        version: "",
                                        description: AboutInfo.operatingSystem,
                                        link: ""
                                    }
                                ]

                                delegate: ColumnLayout {
                                    required property var modelData
                                    spacing: 0

                                    Label {
                                        font.bold: true
                                        text: modelData.version.length > 0
                                              ? "%1 %2".arg(modelData.name).arg(modelData.version)
                                              : modelData.name
                                    }
                                    Label {
                                        Layout.fillWidth: true
                                        wrapMode: Text.WordWrap
                                        text: modelData.description
                                    }
                                    Label {
                                        Layout.fillWidth: true
                                        visible: modelData.link.length > 0
                                        textFormat: Text.RichText
                                        linkColor: Kirigami.Theme.linkColor
                                        text: "<a href=\"" + modelData.link + "\">" + modelData.link + "</a>"
                                        onLinkActivated: function(link) {
                                            root.openUrl(link)
                                        }
                                    }
                                }
                            }
                        }
                    }

                    // ── Authors ──────────────────────────────────────────
                    ColumnLayout {
                        spacing: Kirigami.Units.largeSpacing

                        Label {
                            Layout.fillWidth: true
                            wrapMode: Text.WordWrap
                            textFormat: Text.RichText
                            linkColor: Kirigami.Theme.linkColor
                            text: qsTr("Please use %1 to report bugs.")
                                  .arg("<a href=\"https://github.com/lukasborges/kondor/issues\">https://github.com/lukasborges/kondor/issues</a>")
                            onLinkActivated: function(link) {
                                root.openUrl(link)
                            }
                        }

                        Repeater {
                            model: [
                                {
                                    name: "Lucas Borges",
                                    role: qsTr("Maintainer"),
                                    homepage: "https://github.com/lukasborges"
                                }
                            ]

                            delegate: RowLayout {
                                required property var modelData

                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 0

                                    Label {
                                        font.bold: true
                                        text: modelData.name
                                    }
                                    Label {
                                        text: modelData.role
                                        color: Kirigami.Theme.disabledTextColor
                                    }
                                }

                                ToolButton {
                                    icon.name: "internet-services"
                                    display: AbstractButton.IconOnly
                                    ToolTip.visible: hovered
                                    ToolTip.text: qsTr("Visit Author's Homepage")
                                    ToolTip.delay: 600
                                    onClicked: root.openUrl(modelData.homepage)
                                }
                            }
                        }

                        Item { Layout.fillHeight: true }
                    }
                }
            }
        }

        // ── Buttons ──────────────────────────────────────────────────────
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

    // ── License window ───────────────────────────────────────────────────
    Window {
        id: licenseWindow
        width: 600
        height: 500
        title: qsTr("License Agreement")
        transientParent: root

        Shortcut {
            sequences: [StandardKey.Cancel]
            onActivated: licenseWindow.close()
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: Kirigami.Units.largeSpacing
            spacing: Kirigami.Units.largeSpacing

            ScrollView {
                Layout.fillWidth: true
                Layout.fillHeight: true

                TextArea {
                    text: AboutInfo.licenseText
                    readOnly: true
                    selectByMouse: true
                    wrapMode: TextArea.NoWrap
                    font.family: "monospace"
                }
            }

            DialogButtonBox {
                Layout.fillWidth: true
                padding: 0

                Button {
                    text: qsTr("Close")
                    icon.name: "dialog-close"
                    DialogButtonBox.buttonRole: DialogButtonBox.RejectRole
                    onClicked: licenseWindow.close()
                }
            }
        }
    }
}
