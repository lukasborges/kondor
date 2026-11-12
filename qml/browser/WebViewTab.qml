import QtQuick
import QtQuick.Controls
import QtWebEngine
import org.kde.kirigami as Kirigami
import Kondor

Item {
    id: root

    required property Tab tab
    required property TabModel tabModel

    property point contextMenuPosition: Qt.point(0, 0)

    function setDevToolsOpen(open) {
        if (open === root.tab.devToolsOpen)
            return
        pageView.devToolsView = open ? devTools : null
        root.tab.setDevToolsOpen(open)
    }

    function showContextMenu(request) {
        contextMenuPosition = Qt.point(request.position.x, request.position.y)
        contextMenu.request = request
        contextMenu.popupAt(contextMenuPosition)
    }

    function popupMenuAtLastPosition() {
        contextMenu.request = null
        const center = Qt.point(pageView.width / 2, pageView.height / 2)
        const isUnset = contextMenuPosition.x === 0 && contextMenuPosition.y === 0
        contextMenu.popupAt(isUnset ? center : contextMenuPosition)
    }

    function leaveFullScreenAndMenu() {
        contextMenu.close()
        if (root.tab && root.tab.isFullScreen)
            root.tab.exitFullScreen()
    }

    PageZoom {
        id: pageZoom
        tab: root.tab
        webView: pageView
    }

    ReaderStyle {
        id: readerStyle
        tab: root.tab
        webView: pageView
        loadPending: readerMode.readerLoadPending
    }

    ReaderMode {
        id: readerMode
        tab: root.tab
        webView: pageView
        style: readerStyle
    }

    PageOutput {
        id: pageOutput
        tab: root.tab
        webView: pageView
    }

    CertificateErrorHandler {
        id: certificateHandler
        tab: root.tab
        tabModel: root.tabModel
        webView: pageView
    }

    PageScriptBridges {
        id: scriptBridges
        tab: root.tab
        webView: pageView
    }

    TabCommands {
        tab: root.tab
        tabModel: root.tabModel
        webView: pageView
        reader: readerMode
        certificates: certificateHandler
    }

    SplitView {
        anchors.fill: parent
        orientation: Qt.Vertical

        PageView {
            id: pageView
            SplitView.fillHeight: true
            tab: root.tab
            tabModel: root.tabModel
            zoom: pageZoom
            reader: readerMode
            output: pageOutput
            certificates: certificateHandler
            webChannel: scriptBridges.channel
            onPageContextMenuRequested: function(request) { root.showContextMenu(request) }
        }

        WebEngineView {
            id: devTools
            visible: root.tab.devToolsOpen
            SplitView.preferredHeight: root.height * 0.4
            SplitView.minimumHeight: 100
            profile: root.tab.profile
            onWindowCloseRequested: root.setDevToolsOpen(false)
        }
    }

    PageContextMenu {
        id: contextMenu
        webView: pageView
        tab: root.tab
        tabModel: root.tabModel
    }

    Shortcut {
        sequences: ["Menu", "Shift+F10"]
        enabled: root.visible && pageView.activeFocus
        onActivated: root.popupMenuAtLastPosition()
    }

    NewTabPage {
        anchors.fill: parent
        visible: root.tab.newTabPage
        tab: root.tab
        tabModel: root.tabModel
    }

    CertificateErrorPage {
        anchors.fill: parent
        visible: root.tab.security.certificateErrorPending
        tab: root.tab
    }

    ReaderControls {
        anchors { right: parent.right; top: parent.top; margins: Kirigami.Units.largeSpacing }
        visible: root.tab.readerActive
        onExitRequested: readerMode.exitReader()
    }

    CrashedPage {
        anchors.fill: parent
        visible: root.tab.crashed
        tab: root.tab
        tabModel: root.tabModel
    }

    Connections {
        target: root.tab
        function onToggleDevToolsRequested() { root.setDevToolsOpen(!root.tab.devToolsOpen) }
        function onInspectElementRequested() {
            root.setDevToolsOpen(true)
            pageView.triggerWebAction(WebEngineView.InspectElement)
        }
    }

    onVisibleChanged: {
        if (!visible)
            leaveFullScreenAndMenu()
    }

    Component.onCompleted: {
        if (root.tab.url.toString() !== "")
            pageView.url = root.tab.url
    }
}
