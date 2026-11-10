// Shared mock for the #53 "About Kondor Browser" window, modelled on KDE's
// KAboutApplicationDialog (e.g. About Dolphin): header with icon, name and
// version; About / Components / Authors tabs; a Close button.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Rectangle {
    id: root
    property int tab: 0
    width: 520
    height: 380
    color: Kirigami.Theme.backgroundColor

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Kirigami.Units.largeSpacing
        spacing: Kirigami.Units.largeSpacing

        // ── Header ───────────────────────────────────────────────────────
        RowLayout {
            spacing: Kirigami.Units.largeSpacing
            Kirigami.Icon {
                source: "kondor"
                Layout.preferredWidth: Kirigami.Units.iconSizes.large
                Layout.preferredHeight: Kirigami.Units.iconSizes.large
            }
            ColumnLayout {
                spacing: 0
                Kirigami.Heading { level: 2; text: "Kondor Browser" }
                Label { text: "Version 0.1.5" }
            }
        }

        // ── Tabs ─────────────────────────────────────────────────────────
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            TabBar {
                id: bar
                currentIndex: root.tab
                TabButton { text: "About"; width: implicitWidth }
                TabButton { text: "Components"; width: implicitWidth }
                TabButton { text: "Authors"; width: implicitWidth }
            }

            Frame {
                Layout.fillWidth: true
                Layout.fillHeight: true

                StackLayout {
                    anchors.fill: parent
                    currentIndex: bar.currentIndex

                    // About
                    ColumnLayout {
                        spacing: Kirigami.Units.largeSpacing
                        Label { text: "Web Browser" }
                        Label { text: "© 2026 The Kondor Developers" }
                        Label {
                            text: "<a href=\"https://github.com/lukasborges/kondor\">https://github.com/lukasborges/kondor</a>"
                            color: Kirigami.Theme.linkColor
                        }
                        Label {
                            text: "<a href=\"#license\">License: GNU General Public License Version 3</a>"
                        }
                        Item { Layout.fillHeight: true }
                    }

                    // Components
                    ScrollView {
                        ColumnLayout {
                            width: parent.width
                            spacing: Kirigami.Units.largeSpacing
                            Repeater {
                                model: [
                                    { name: "Qt", version: "6.11.2", desc: "Using 6.11.2 (built against 6.11.2)", link: "https://www.qt.io/" },
                                    { name: "Qt WebEngine", version: "6.11.2", desc: "Chromium 134.0.6998.208", link: "https://doc.qt.io/qt-6/qtwebengine-index.html" },
                                    { name: "Kirigami", version: "", desc: "KDE user interface framework, used for the Breeze look", link: "https://develop.kde.org/frameworks/kirigami/" },
                                    { name: "Windowing System", version: "", desc: "Wayland", link: "" },
                                    { name: "Operating System", version: "", desc: "Fedora Linux 45 (KDE Plasma Desktop Edition)", link: "" }
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
                                    Label { text: modelData.desc }
                                    Label {
                                        visible: modelData.link.length > 0
                                        text: "<a href=\"%1\">%1</a>".arg(modelData.link)
                                    }
                                }
                            }
                        }
                    }

                    // Authors
                    ColumnLayout {
                        spacing: Kirigami.Units.largeSpacing
                        Label {
                            Layout.fillWidth: true
                            wrapMode: Text.WordWrap
                            text: "Please use <a href=\"https://github.com/lukasborges/kondor/issues\">https://github.com/lukasborges/kondor/issues</a> to report bugs."
                        }
                        RowLayout {
                            ColumnLayout {
                                spacing: 0
                                Layout.fillWidth: true
                                Label { text: "Lucas Borges"; font.bold: true }
                                Label { text: "Maintainer"; color: Kirigami.Theme.disabledTextColor }
                            }
                            ToolButton {
                                icon.name: "internet-services"
                                display: AbstractButton.IconOnly
                                text: "Visit Author's Homepage"
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
            Button { text: "Close"; icon.name: "dialog-close"; DialogButtonBox.buttonRole: DialogButtonBox.RejectRole }
        }
    }
}
