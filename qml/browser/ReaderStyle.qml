import QtQuick
import QtWebEngine
import org.kde.kirigami as Kirigami
import Kondor

Item {
    id: root

    required property Tab tab
    required property WebEngineView webView
    required property bool loadPending

    visible: false

    Item {
        id: colors
        Kirigami.Theme.colorSet: Kirigami.Theme.View
        Kirigami.Theme.inherit: false
        readonly property color backgroundColor: Kirigami.Theme.backgroundColor
        readonly property color textColor: Kirigami.Theme.textColor
        readonly property color linkColor: Kirigami.Theme.linkColor
        readonly property color disabledTextColor: Kirigami.Theme.disabledTextColor
    }

    function fontFamily() {
        return Settings.readerSerif
            ? "'Noto Serif', 'DejaVu Serif', Georgia, serif"
            : "'Noto Sans', 'DejaVu Sans', system-ui, sans-serif"
    }

    function readerVars() {
        return "--reader-bg: " + colors.backgroundColor
            + "; --reader-text: " + colors.textColor
            + "; --reader-link: " + colors.linkColor
            + "; --reader-muted: " + colors.disabledTextColor
            + "; --reader-font: " + fontFamily()
            + "; --reader-size: " + Settings.readerFontSize + "px;"
    }

    function applyReaderStyle() {
        if (!tab.readerActive || loadPending)
            return
        const css = JSON.stringify(":root { " + readerVars() + " }")
        webView.runJavaScript(
            "document.getElementById('reader-vars').textContent = " + css + ";",
            WebEngineScript.ApplicationWorld)
    }

    Connections {
        target: Settings
        function onReaderFontSizeChanged() { root.applyReaderStyle() }
        function onReaderSerifChanged() { root.applyReaderStyle() }
    }

    Connections {
        target: colors
        function onBackgroundColorChanged() { root.applyReaderStyle() }
        function onTextColorChanged() { root.applyReaderStyle() }
        function onLinkColorChanged() { root.applyReaderStyle() }
    }
}
