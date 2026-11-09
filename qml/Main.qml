import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

ApplicationWindow {
    id: window
    width: 1280
    height: 820
    minimumWidth: 640
    minimumHeight: 480
    visible: true
    title: {
        const t = tabs.currentTab
        return (t && t.title.length) ? t.title + " — Kondor" : qsTr("Kondor")
    }

    TabModel {
        id: tabs
    }

    // Set once the user confirms quitting with downloads still running, so the
    // confirmation is not asked again on the retried close.
    property bool quitConfirmed: false

    onClosing: function(close) {
        if (DownloadManager.hasActiveDownloads && !window.quitConfirmed) {
            close.accepted = false
            quitDialog.open()
        }
    }

    MessageDialog {
        id: quitDialog
        title: qsTr("Quit Kondor")
        text: qsTr("Downloads are still in progress. Quit anyway?")
        buttons: MessageDialog.Yes | MessageDialog.No
        onAccepted: {
            window.quitConfirmed = true
            window.close()
        }
    }

    function closeTabAt(idx) {
        if (tabs.count <= 1) {
            window.close()
            return
        }
        tabs.closeTab(idx)
    }

    function closeTabFor(t) {
        if (tabs.count <= 1) {
            window.close()
            return
        }
        tabs.closeTabObject(t)
    }

    // FileDialog hands a file:// URL to QML; downloads need a local path.
    function localPath(url) {
        let path = url.toString()
        if (path.startsWith("file://"))
            path = path.slice(7)
        return decodeURIComponent(path)
    }

    function openHistory() {
        if (!historyWindow)
            historyWindow = historyWindowComponent.createObject(window)
        historyWindow.showWindow()
    }

    function openSettings() {
        if (!settingsWindow)
            settingsWindow = settingsWindowComponent.createObject(window)
        settingsWindow.showWindow()
    }

    Component.onCompleted: {
        if (tabs.count === 0)
            tabs.addTab(false)
    }

    header: ColumnLayout {
        spacing: 0

        // ── Barra de abas (nativa do estilo KDE) ─────────────────────────
        Rectangle {
            Layout.fillWidth: true
            implicitHeight: tabBar.implicitHeight
            Kirigami.Theme.colorSet: Kirigami.Theme.Header
            Kirigami.Theme.inherit: false
            color: Kirigami.Theme.backgroundColor

            RowLayout {
                anchors.fill: parent
                spacing: 0

                TabBar {
                    id: tabBar
                    currentIndex: tabs.currentIndex
                    background: null

                    onCurrentIndexChanged: {
                        if (tabs.currentIndex !== currentIndex)
                            tabs.setCurrentIndex(currentIndex)
                    }

                    Repeater {
                        model: tabs

                        delegate: TabButton {
                            id: tabButton
                            required property Tab tab

                            readonly property string fullTitle: tab.title.length ? tab.title : qsTr("Nova aba")
                            property string elidedTitle: fullTitle

                            // Largura limitada: não cresce junto com o título.
                            width: Math.min(220, Math.max(130, Math.ceil(fullMetrics.advanceWidth) + 62))
                            text: elidedTitle

                            TextMetrics {
                                id: fullMetrics
                                font: Kirigami.Theme.defaultFont
                                text: tabButton.fullTitle
                            }

                            TextMetrics {
                                id: measure
                                font: Kirigami.Theme.defaultFont
                            }

                            function updateElided() {
                                var maxW = width - 70
                                measure.text = fullTitle
                                if (measure.advanceWidth <= maxW) {
                                    elidedTitle = fullTitle
                                    return
                                }
                                var s = fullTitle
                                while (s.length > 0) {
                                    s = s.slice(0, -1)
                                    measure.text = s + "\u2026"
                                    if (measure.advanceWidth <= maxW) {
                                        elidedTitle = s + "\u2026"
                                        return
                                    }
                                }
                                elidedTitle = "\u2026"
                            }

                            onFullTitleChanged: updateElided()
                            onWidthChanged: updateElided()
                            Component.onCompleted: updateElided()

                            ToolButton {
                                anchors.right: parent.right
                                anchors.verticalCenter: parent.verticalCenter
                                anchors.rightMargin: 4
                                width: 20
                                height: 20
                                flat: true
                                display: AbstractButton.IconOnly
                                icon.name: "window-close-symbolic"
                                icon.width: 14
                                icon.height: 14
                                ToolTip.visible: hovered
                                ToolTip.text: qsTr("Fechar aba")
                                ToolTip.delay: 600
                                onClicked: window.closeTabFor(tabButton.tab)
                            }
                        }
                    }
                }

                // Botão de nova aba, logo depois da última aba.
                ToolButton {
                    id: newTabButton
                    Layout.alignment: Qt.AlignVCenter
                    Layout.leftMargin: 2
                    display: AbstractButton.IconOnly
                    icon.name: "tab-new"
                    icon.width: 16
                    icon.height: 16
                    ToolTip.visible: hovered
                    ToolTip.text: qsTr("Nova aba")
                    ToolTip.delay: 600
                    onClicked: tabs.addTab(false)
                }

                Item { Layout.fillWidth: true }
            }
        }

        // ── Barra de navegação ───────────────────────────────────────────
        ToolBar {
            Layout.fillWidth: true
            // Mesma cor da aba ativa / fundo da janela.
            Kirigami.Theme.colorSet: Kirigami.Theme.Window
            Kirigami.Theme.inherit: false

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 5
                anchors.rightMargin: 5
                spacing: 2

                ToolButton {
                    display: AbstractButton.IconOnly
                    icon.name: "go-previous"
                    enabled: tabs.currentTab ? tabs.currentTab.canGoBack : false
                    ToolTip.visible: hovered
                    ToolTip.text: qsTr("Voltar")
                    ToolTip.delay: 600
                    onClicked: {
                        if (tabs.currentTab)
                            tabs.currentTab.goBack()
                    }
                }

                ToolButton {
                    display: AbstractButton.IconOnly
                    icon.name: "go-next"
                    enabled: tabs.currentTab ? tabs.currentTab.canGoForward : false
                    ToolTip.visible: hovered
                    ToolTip.text: qsTr("Avançar")
                    ToolTip.delay: 600
                    onClicked: {
                        if (tabs.currentTab)
                            tabs.currentTab.goForward()
                    }
                }

                ToolButton {
                    display: AbstractButton.IconOnly
                    icon.name: (tabs.currentTab && tabs.currentTab.loading) ? "process-stop" : "view-refresh"
                    ToolTip.visible: hovered
                    ToolTip.text: (tabs.currentTab && tabs.currentTab.loading) ? qsTr("Parar") : qsTr("Recarregar")
                    ToolTip.delay: 600
                    onClicked: {
                        if (!tabs.currentTab)
                            return
                        if (tabs.currentTab.loading)
                            tabs.currentTab.stop()
                        else
                            tabs.currentTab.reload()
                    }
                }

                ToolButton {
                    display: AbstractButton.IconOnly
                    icon.name: "go-home"
                    ToolTip.visible: hovered
                    ToolTip.text: qsTr("Página inicial")
                    ToolTip.delay: 600
                    onClicked: {
                        if (tabs.currentTab)
                            tabs.currentTab.navigateTo(ProfileManager.resolveAddress(""))
                    }
                }

                TextField {
                    id: addressBar
                    Layout.fillWidth: true
                    Layout.leftMargin: 8
                    Layout.rightMargin: 8
                    placeholderText: qsTr("Pesquisar ou digitar um endereço")
                    selectByMouse: true

                    function syncFromTab() {
                        if (activeFocus)
                            return
                        const t = tabs.currentTab
                        text = t ? t.url.toString() : ""
                    }

                    onAccepted: {
                        const t = tabs.currentTab
                        if (!t)
                            return
                        t.navigateTo(ProfileManager.resolveAddress(text))
                        focus = false
                    }

                    onActiveFocusChanged: {
                        if (activeFocus)
                            selectAll()
                    }

                    Component.onCompleted: syncFromTab()
                }

                ToolButton {
                    id: downloadsButton
                    visible: DownloadManager.model.count > 0
                    display: AbstractButton.IconOnly
                    icon.name: "download"
                    ToolTip.visible: hovered
                    ToolTip.text: qsTr("Downloads")
                    ToolTip.delay: 600
                    onClicked: downloadsPopup.opened ? downloadsPopup.close() : downloadsPopup.open()

                    ProgressBar {
                        anchors {
                            left: parent.left
                            right: parent.right
                            bottom: parent.bottom
                            margins: 4
                        }
                        height: 2
                        visible: DownloadManager.hasActiveDownloads
                        value: DownloadManager.activeProgress >= 0 ? DownloadManager.activeProgress : 0
                        indeterminate: DownloadManager.activeProgress < 0
                    }

                    DownloadsPopup {
                        id: downloadsPopup
                        x: downloadsButton.width - width
                        y: downloadsButton.height
                    }
                }

                ToolButton {
                    id: menuButton
                    display: AbstractButton.IconOnly
                    icon.name: "application-menu"
                    ToolTip.visible: hovered
                    ToolTip.text: qsTr("Menu")
                    ToolTip.delay: 600
                    onClicked: mainMenu.open()

                    Menu {
                        id: mainMenu

                        MenuItem {
                            text: qsTr("Nova aba")
                            icon.name: "tab-new"
                            onTriggered: tabs.addTab(false)
                        }
                        MenuItem {
                            text: qsTr("Nova aba privada")
                            icon.name: "view-private"
                            onTriggered: tabs.addTab(true)
                        }
                        MenuSeparator {}
                        MenuItem {
                            text: qsTr("Fechar aba")
                            icon.name: "window-close"
                            onTriggered: window.closeTabAt(tabs.currentIndex)
                        }
                        MenuSeparator {}
                        MenuItem {
                            text: qsTr("Find in Page…")
                            icon.name: "edit-find"
                            onTriggered: findBar.open()
                        }
                        MenuSeparator {}
                        MenuItem {
                            text: qsTr("Ampliar")
                            icon.name: "zoom-in"
                            onTriggered: {
                                if (tabs.currentTab)
                                    tabs.currentTab.zoomIn()
                            }
                        }
                        MenuItem {
                            text: qsTr("Reduzir")
                            icon.name: "zoom-out"
                            onTriggered: {
                                if (tabs.currentTab)
                                    tabs.currentTab.zoomOut()
                            }
                        }
                        MenuItem {
                            text: qsTr("Tamanho normal")
                            icon.name: "zoom-original"
                            onTriggered: {
                                if (tabs.currentTab)
                                    tabs.currentTab.resetZoom()
                            }
                        }
                        MenuSeparator {}
                        MenuItem {
                            text: qsTr("History")
                            icon.name: "view-history"
                            onTriggered: window.openHistory()
                        }
                        MenuSeparator {}
                        MenuItem {
                            text: qsTr("Configure Kondor…")
                            icon.name: "configure"
                            onTriggered: window.openSettings()
                        }
                        MenuSeparator {}
                        MenuItem {
                            text: qsTr("Sobre o Kondor")
                            icon.name: "help-about"
                        }
                    }
                }
            }
        }
    }

    // ── Área de conteúdo: uma WebEngineView por aba ─────────────────────
    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        FindBar {
            id: findBar
            tab: tabs.currentTab
            Layout.fillWidth: true
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: window.palette.base

            Repeater {
                model: tabs

                delegate: WebViewTab {
                    tabModel: tabs
                    anchors.fill: parent
                    visible: tabs.currentTab === tab
                }
            }
        }
    }

    // ── History window (created on demand) ──────────────────────────────
    property var historyWindow: null

    Component {
        id: historyWindowComponent
        HistoryWindow {
            tabModel: tabs
        }
    }

    // ── Settings window (created on demand) ─────────────────────────────
    property var settingsWindow: null

    Component {
        id: settingsWindowComponent
        SettingsWindow {
            tabModel: tabs
        }
    }

    // ── Save dialog for "Ask where to save each file" ───────────────────
    FileDialog {
        id: saveFileDialog
        title: qsTr("Save File")
        fileMode: FileDialog.SaveFile
        property var pendingDownload: null

        onAccepted: {
            if (!pendingDownload)
                return
            const path = window.localPath(selectedFile)
            const slash = path.lastIndexOf("/")
            if (slash > 0) {
                pendingDownload.downloadDirectory = path.slice(0, slash)
                pendingDownload.downloadFileName = path.slice(slash + 1)
            }
            pendingDownload.accept()
            pendingDownload = null
        }

        onRejected: {
            if (pendingDownload)
                pendingDownload.cancel()
            pendingDownload = null
        }
    }

    Connections {
        target: DownloadManager

        function onSaveLocationRequested(request, suggestedFile) {
            saveFileDialog.pendingDownload = request
            saveFileDialog.currentFile = suggestedFile
            saveFileDialog.open()
        }

        function onDownloadStarted() {
            downloadsPopup.open()
        }
    }

    Connections {
        target: DownloadManager.model

        function onCountChanged() {
            // The button (and so the popup's anchor) disappears when the list
            // becomes empty; do not leave the popup floating around.
            if (DownloadManager.model.count === 0)
                downloadsPopup.close()
        }
    }

    // ── Atalhos ─────────────────────────────────────────────────────────
    Shortcut {
        sequence: "Ctrl+T"
        onActivated: tabs.addTab(false)
    }
    Shortcut {
        sequence: "Ctrl+Shift+N"
        onActivated: tabs.addTab(true)
    }
    Shortcut {
        sequence: "Ctrl+W"
        onActivated: window.closeTabAt(tabs.currentIndex)
    }
    Shortcut {
        sequence: "Ctrl+L"
        onActivated: {
            addressBar.forceActiveFocus()
            addressBar.selectAll()
        }
    }
    Shortcut {
        sequence: "Ctrl+H"
        onActivated: window.openHistory()
    }
    Shortcut {
        sequences: [StandardKey.Preferences, "Ctrl+,"]
        onActivated: window.openSettings()
    }
    Shortcut {
        sequences: ["F5", "Ctrl+R"]
        onActivated: {
            if (tabs.currentTab)
                tabs.currentTab.reload()
        }
    }
    Shortcut {
        sequences: ["Alt+Left"]
        onActivated: {
            if (tabs.currentTab)
                tabs.currentTab.goBack()
        }
    }
    Shortcut {
        sequences: ["Alt+Right"]
        onActivated: {
            if (tabs.currentTab)
                tabs.currentTab.goForward()
        }
    }
    Shortcut {
        sequences: ["Ctrl++", "Ctrl+="]
        onActivated: {
            if (tabs.currentTab)
                tabs.currentTab.zoomIn()
        }
    }
    Shortcut {
        sequences: ["Ctrl+-"]
        onActivated: {
            if (tabs.currentTab)
                tabs.currentTab.zoomOut()
        }
    }
    Shortcut {
        sequence: "Ctrl+0"
        onActivated: {
            if (tabs.currentTab)
                tabs.currentTab.resetZoom()
        }
    }
    Shortcut {
        sequences: [StandardKey.Find]
        onActivated: findBar.open()
    }
    Shortcut {
        sequence: "F3"
        enabled: findBar.visible
        onActivated: findBar.findNext()
    }
    Shortcut {
        sequence: "Shift+F3"
        enabled: findBar.visible
        onActivated: findBar.findPrevious()
    }

    Connections {
        target: tabs
        function onCurrentIndexChanged() {
            if (tabBar.currentIndex !== tabs.currentIndex)
                tabBar.currentIndex = tabs.currentIndex
        }
        function onCurrentTabChanged() {
            addressBar.syncFromTab()
        }
    }

    Connections {
        target: tabs.currentTab
        function onUrlChanged() {
            addressBar.syncFromTab()
        }
    }
}
