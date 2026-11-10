pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import org.kde.kirigami as Kirigami
import Kondor

// "Configure" window (Ctrl+,), modelled on KDE's KConfigDialog: a sidebar
// with a search field and one icon per page, the page title on top, tabs
// inside a page when it has several groups, and Defaults / OK / Apply /
// Cancel at the bottom. Controls edit a pending copy of the settings; only
// OK and Apply write to `Settings`.
ApplicationWindow {
    id: root
    width: 860
    height: 600
    minimumWidth: 640
    minimumHeight: 480
    //: %1 is the application name
    title: qsTr("Configure — %1").arg(Qt.application.displayName)
    visible: false

    required property TabModel tabModel

    onClosing: function(close) {
        // Do not destroy: just hide and drop the pending changes.
        close.accepted = false
        root.discardChanges()
    }

    // ── Page list ───────────────────────────────────────────────────────
    // `keywords` are the translated labels of the page's options, so the
    // search field finds a page by what it configures.
    readonly property var pages: [
        {
            title: qsTr("General"),
            icon: "internet-web-browser",
            keywords: [qsTr("Startup"), qsTr("New Tabs"), qsTr("On startup:"),
                       qsTr("Home page:"), qsTr("Show top sites")],
            component: generalPage
        },
        {
            title: qsTr("Search"),
            icon: "system-search",
            keywords: [qsTr("Search engine:"), qsTr("Custom URL:")],
            component: searchPage
        },
        {
            title: qsTr("Downloads"),
            icon: "folder-download",
            keywords: [qsTr("Save files to:"), qsTr("Ask where to save each file")],
            component: downloadsPage
        },
        {
            title: qsTr("Privacy"),
            icon: "preferences-security",
            keywords: [qsTr("Cookies:"), qsTr("On exit:"),
                       qsTr("Clear cookies, cache and history"),
                       qsTr("Browsing data:"), qsTr("Clear Cookies and Cache Now"),
                       qsTr("Site permissions:"), qsTr("Manage Site Permissions…")],
            component: privacyPage
        }
    ]

    property int currentPage: 0
    // Set while the search field recreates the list model: the ListView
    // resets currentIndex to 0 as it adopts the new model, and that reset
    // must not move the shown page.
    property bool syncingPageList: false
    // Kept here so it survives the page contents being reloaded.
    property int generalTab: 0
    property bool modified: false
    property bool defaultsEnabled: false

    // Indices into `pages`, never the page objects: a ListView over a JS array
    // hands each delegate a converted copy, so comparing objects with === or
    // looking them up with indexOf() always fails. Integers are safe.
    readonly property var visiblePages: {
        const text = searchField.text.trim().toLowerCase()
        const all = pages.map(function(page, index) { return index })
        if (text.length === 0)
            return all
        return all.filter(function(index) {
            const page = pages[index]
            return (page.title + " " + page.keywords.join(" ")).toLowerCase().includes(text)
        })
    }

    onCurrentPageChanged: {
        root.refresh()
        root.ensureVisiblePage()
    }
    onVisiblePagesChanged: {
        root.syncingPageList = true
        root.ensureVisiblePage()
        // Adopting a new model makes the ListView reset currentIndex after
        // this signal returns; restore the index once that reset has passed.
        Qt.callLater(root.finishPageListSync)
    }

    function finishPageListSync() {
        root.syncingPageList = false
        root.ensureVisiblePage()
    }

    // ── Pending state ───────────────────────────────────────────────────
    // Opening the window copies every option here; the controls edit only
    // this object, and Apply/OK write the differences to `Settings`.
    QtObject {
        id: pending

        // Neutral values: `readSettings()` fills them in before the window
        // is shown, and `Settings::defaultValue()` owns the real defaults.
        property string homePage: ""
        property string searchEngine: ""
        property string customSearchUrl: ""
        property string downloadDirectory: ""
        property bool askWhereToSave: false
        property string startupBehavior: ""
        property bool showTopSites: false
        property bool clearDataOnExit: false
        property bool blockThirdPartyCookies: false

        readonly property var values: [homePage, searchEngine, customSearchUrl,
            downloadDirectory, askWhereToSave, startupBehavior, showTopSites,
            clearDataOnExit, blockThirdPartyCookies]
        onValuesChanged: root.refresh()
    }

    function readSettings() {
        pending.homePage = Settings.homePage
        pending.searchEngine = Settings.searchEngine
        pending.customSearchUrl = Settings.customSearchUrl
        pending.downloadDirectory = Settings.downloadDirectory
        pending.askWhereToSave = Settings.askWhereToSave
        pending.startupBehavior = Settings.startupBehavior
        pending.showTopSites = Settings.showTopSites
        pending.clearDataOnExit = Settings.clearDataOnExit
        pending.blockThirdPartyCookies = Settings.blockThirdPartyCookies
        root.refresh()
    }

    function refresh() {
        root.modified = pending.homePage !== Settings.homePage
                || pending.searchEngine !== Settings.searchEngine
                || pending.customSearchUrl !== Settings.customSearchUrl
                || pending.downloadDirectory !== Settings.downloadDirectory
                || pending.askWhereToSave !== Settings.askWhereToSave
                || pending.startupBehavior !== Settings.startupBehavior
                || pending.showTopSites !== Settings.showTopSites
                || pending.clearDataOnExit !== Settings.clearDataOnExit
                || pending.blockThirdPartyCookies !== Settings.blockThirdPartyCookies
        root.defaultsEnabled = !root.pageAtDefaults()
    }

    function pageAtDefaults() {
        switch (root.currentPage) {
        case 0:
            return pending.startupBehavior === Settings.defaultValue("startupBehavior")
                    && pending.homePage === Settings.defaultValue("homePage")
                    && pending.showTopSites === Settings.defaultValue("showTopSites")
        case 1:
            return pending.searchEngine === Settings.defaultValue("searchEngine")
                    && pending.customSearchUrl === Settings.defaultValue("customSearchUrl")
        case 2:
            return pending.downloadDirectory === Settings.defaultValue("downloadDirectory")
                    && pending.askWhereToSave === Settings.defaultValue("askWhereToSave")
        case 3:
            return pending.blockThirdPartyCookies
                        === Settings.defaultValue("blockThirdPartyCookies")
                    && pending.clearDataOnExit === Settings.defaultValue("clearDataOnExit")
        }
        return true
    }

    function restoreDefaults() {
        switch (root.currentPage) {
        case 0:
            pending.startupBehavior = Settings.defaultValue("startupBehavior")
            pending.homePage = Settings.defaultValue("homePage")
            pending.showTopSites = Settings.defaultValue("showTopSites")
            break
        case 1:
            pending.searchEngine = Settings.defaultValue("searchEngine")
            pending.customSearchUrl = Settings.defaultValue("customSearchUrl")
            break
        case 2:
            pending.downloadDirectory = Settings.defaultValue("downloadDirectory")
            pending.askWhereToSave = Settings.defaultValue("askWhereToSave")
            break
        case 3:
            pending.blockThirdPartyCookies = Settings.defaultValue("blockThirdPartyCookies")
            pending.clearDataOnExit = Settings.defaultValue("clearDataOnExit")
            break
        }
        root.refresh()
    }

    function applyChanges() {
        if (pending.homePage !== Settings.homePage)
            Settings.homePage = pending.homePage
        if (pending.searchEngine !== Settings.searchEngine)
            Settings.searchEngine = pending.searchEngine
        if (pending.customSearchUrl !== Settings.customSearchUrl)
            Settings.customSearchUrl = pending.customSearchUrl
        if (pending.downloadDirectory !== Settings.downloadDirectory)
            Settings.downloadDirectory = pending.downloadDirectory
        if (pending.askWhereToSave !== Settings.askWhereToSave)
            Settings.askWhereToSave = pending.askWhereToSave
        if (pending.startupBehavior !== Settings.startupBehavior)
            Settings.startupBehavior = pending.startupBehavior
        if (pending.showTopSites !== Settings.showTopSites)
            Settings.showTopSites = pending.showTopSites
        if (pending.clearDataOnExit !== Settings.clearDataOnExit)
            Settings.clearDataOnExit = pending.clearDataOnExit
        if (pending.blockThirdPartyCookies !== Settings.blockThirdPartyCookies)
            Settings.blockThirdPartyCookies = pending.blockThirdPartyCookies
        root.refresh()
    }

    function acceptAndClose() {
        root.applyChanges()
        root.discardChanges()
    }

    function discardChanges() {
        root.visible = false
    }

    // Keep the sidebar list selection in sync with the current page once the
    // search filter may have hidden it.
    function ensureVisiblePage() {
        if (root.visiblePages.length === 0)
            return
        let index = root.visiblePages.indexOf(root.currentPage)
        if (index === -1) {
            root.currentPage = root.visiblePages[0]
            index = 0
        }
        pageList.currentIndex = index
    }

    function showWindow() {
        // The folder may have been deleted (or recreated) since the window was
        // last shown; re-read it before displaying the warning.
        Settings.refreshDownloadDirectory()
        searchField.text = ""
        root.readSettings()
        root.visible = true
        root.raise()
        root.requestActivate()
        pageList.forceActiveFocus()
    }

    function openSitePermissions() {
        if (!sitePermissionsWindow)
            sitePermissionsWindow = sitePermissionsComponent.createObject(root)
        sitePermissionsWindow.showWindow()
    }

    // FolderDialog hands a file:// URL to QML; Settings stores a local path.
    function localPath(url) {
        let path = url.toString()
        if (path.startsWith("file://"))
            path = path.slice(7)
        return decodeURIComponent(path)
    }

    Shortcut {
        sequences: [StandardKey.Find]
        onActivated: searchField.forceActiveFocus()
    }

    Shortcut {
        sequences: [StandardKey.Cancel]
        onActivated: root.discardChanges()
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            // ── Sidebar ─────────────────────────────────────────────────
            Rectangle {
                Layout.preferredWidth: Kirigami.Units.gridUnit * 8
                Layout.fillHeight: true
                Kirigami.Theme.colorSet: Kirigami.Theme.View
                Kirigami.Theme.inherit: false
                color: Kirigami.Theme.backgroundColor

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: Kirigami.Units.smallSpacing
                    spacing: Kirigami.Units.smallSpacing

                    Kirigami.SearchField {
                        id: searchField
                        Layout.fillWidth: true
                        placeholderText: qsTr("Search…")
                    }

                    ListView {
                        id: pageList
                        objectName: "pageList"
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        focus: true
                        keyNavigationEnabled: true
                        model: root.visiblePages

                        delegate: ItemDelegate {
                            required property int modelData
                            required property int index
                            width: ListView.view.width
                            highlighted: modelData === root.currentPage
                            display: AbstractButton.TextUnderIcon
                            icon.name: root.pages[modelData].icon
                            icon.width: Kirigami.Units.iconSizes.medium
                            icon.height: Kirigami.Units.iconSizes.medium
                            text: root.pages[modelData].title
                            onClicked: root.currentPage = modelData
                        }

                        onCurrentIndexChanged: {
                            // Only user navigation moves the shown page; see
                            // `syncingPageList` for the model reset.
                            if (root.syncingPageList)
                                return
                            if (currentIndex < 0 || currentIndex >= root.visiblePages.length)
                                return
                            const page = root.visiblePages[currentIndex]
                            if (page !== undefined && page !== root.currentPage)
                                root.currentPage = page
                        }
                    }
                }
            }

            Kirigami.Separator { Layout.fillHeight: true }

            // ── Page ────────────────────────────────────────────────────
            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 0

                Kirigami.Heading {
                    id: pageHeading
                    objectName: "pageHeading"
                    Layout.fillWidth: true
                    Layout.margins: Kirigami.Units.smallSpacing
                    Layout.leftMargin: Kirigami.Units.largeSpacing
                    level: 1
                    text: root.pages[root.currentPage].title
                }

                TabBar {
                    Layout.fillWidth: true
                    visible: root.currentPage === 0
                    currentIndex: root.generalTab
                    onCurrentIndexChanged: root.generalTab = currentIndex

                    TabButton { text: qsTr("Startup") }
                    TabButton { text: qsTr("New Tabs") }
                }

                Kirigami.Separator {
                    Layout.fillWidth: true
                    visible: root.currentPage !== 0
                }

                StackLayout {
                    id: pageStack
                    objectName: "pageStack"
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.margins: Kirigami.Units.gridUnit
                    currentIndex: root.currentPage

                    Repeater {
                        model: root.pages

                        delegate: Loader {
                            required property var modelData
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            sourceComponent: modelData.component
                        }
                    }
                }
            }
        }

        // ── Buttons ─────────────────────────────────────────────────────
        Kirigami.Separator { Layout.fillWidth: true }

        RowLayout {
            Layout.fillWidth: true
            Layout.margins: Kirigami.Units.smallSpacing

            Button {
                text: qsTr("Defaults")
                icon.name: "document-revert"
                enabled: root.defaultsEnabled
                onClicked: root.restoreDefaults()
            }

            Item { Layout.fillWidth: true }

            Button {
                text: qsTr("OK")
                icon.name: "dialog-ok"
                highlighted: true
                onClicked: root.acceptAndClose()
            }

            Button {
                text: qsTr("Apply")
                icon.name: "dialog-ok-apply"
                enabled: root.modified
                onClicked: root.applyChanges()
            }

            Button {
                text: qsTr("Cancel")
                icon.name: "dialog-cancel"
                onClicked: root.discardChanges()
            }
        }
    }

    // ── General page ────────────────────────────────────────────────────
    Component {
        id: generalPage

        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: root.generalTab

            // ── General → Startup ───────────────────────────────────
            ScrollView {
                id: startupView
                contentWidth: availableWidth
                ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

                ColumnLayout {
                    width: startupView.availableWidth
                    spacing: Kirigami.Units.largeSpacing

                    Kirigami.FormLayout {
                        Layout.fillWidth: true

                        RadioButton {
                            id: homePageRadio
                            Kirigami.FormData.label: qsTr("On startup:")
                            text: qsTr("Open the home page")
                            onClicked: pending.startupBehavior = "homepage"
                        }

                        Binding {
                            target: homePageRadio
                            property: "checked"
                            value: pending.startupBehavior === "homepage"
                        }

                        RadioButton {
                            id: restoreRadio
                            text: qsTr("Open the tabs from last time")
                            onClicked: pending.startupBehavior = "restore"
                        }

                        Binding {
                            target: restoreRadio
                            property: "checked"
                            value: pending.startupBehavior === "restore"
                        }

                        Item { Kirigami.FormData.isSection: true }

                        TextField {
                            id: homeField
                            Kirigami.FormData.label: qsTr("Home page:")
                            placeholderText: qsTr("New Tab page")
                            Layout.preferredWidth: Kirigami.Units.gridUnit * 18
                            onTextEdited: pending.homePage = text
                            onEditingFinished: {
                                // A blank field means the New Tab page.
                                pending.homePage = text.trim().length === 0
                                        ? ""
                                        : ProfileManager.resolveAddress(text).toString()
                            }
                        }

                        Binding {
                            target: homeField
                            property: "text"
                            value: pending.homePage
                        }

                        RowLayout {
                            Button {
                                text: qsTr("Use Current Page")
                                icon.name: "go-home"
                                // A private tab's URL must never land on disk.
                                enabled: root.tabModel.currentTab !== null
                                         && !root.tabModel.currentTab.isPrivate
                                onClicked: {
                                    const tab = root.tabModel.currentTab
                                    if (tab)
                                        pending.homePage = tab.url.toString()
                                }
                            }

                            Button {
                                text: qsTr("Use New Tab Page")
                                icon.name: "tab-new"
                                enabled: pending.homePage.length > 0
                                onClicked: pending.homePage = ""
                            }
                        }
                    }

                    Item { Layout.fillHeight: true }
                }
            }

            // ── General → New Tabs ──────────────────────────────────
            ScrollView {
                id: newTabsView
                contentWidth: availableWidth
                ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

                ColumnLayout {
                    width: newTabsView.availableWidth
                    spacing: Kirigami.Units.largeSpacing

                    Kirigami.FormLayout {
                        Layout.fillWidth: true

                        CheckBox {
                            id: topSitesCheck
                            Kirigami.FormData.label: qsTr("New Tab page:")
                            text: qsTr("Show top sites")
                            onToggled: pending.showTopSites = checked
                        }

                        Binding {
                            target: topSitesCheck
                            property: "checked"
                            value: pending.showTopSites
                        }

                        Button {
                            text: qsTr("Restore Removed Sites")
                            icon.name: "edit-undo"
                            enabled: Settings.hiddenTopSites.length > 0
                            onClicked: Settings.hiddenTopSites = []
                        }
                    }

                    Item { Layout.fillHeight: true }
                }
            }
        }
    }

    // ── Search page ─────────────────────────────────────────────────────
    Component {
        id: searchPage

        ScrollView {
            id: searchView
            contentWidth: availableWidth
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

            ColumnLayout {
                width: searchView.availableWidth
                spacing: Kirigami.Units.largeSpacing

                Kirigami.FormLayout {
                    Layout.fillWidth: true

                    ComboBox {
                        id: engineBox
                        Kirigami.FormData.label: qsTr("Search engine:")
                        Layout.preferredWidth: Kirigami.Units.gridUnit * 14
                        model: [
                            { value: "duckduckgo", label: "DuckDuckGo" },
                            { value: "google", label: "Google" },
                            { value: "startpage", label: "Startpage" },
                            { value: "brave", label: "Brave Search" },
                            { value: "custom", label: qsTr("Custom…") }
                        ]
                        textRole: "label"
                        valueRole: "value"
                        onActivated: pending.searchEngine = currentValue
                    }

                    Binding {
                        target: engineBox
                        property: "currentIndex"
                        value: Math.max(0, engineBox.indexOfValue(pending.searchEngine))
                    }

                    TextField {
                        id: customField
                        Kirigami.FormData.label: qsTr("Custom URL:")
                        Layout.preferredWidth: Kirigami.Units.gridUnit * 18
                        enabled: pending.searchEngine === "custom"
                        placeholderText: "https://www.bing.com/search?q=%1"
                        onTextEdited: pending.customSearchUrl = text
                        onEditingFinished: pending.customSearchUrl = text
                    }

                    Binding {
                        target: customField
                        property: "text"
                        value: pending.customSearchUrl
                    }
                }

                Kirigami.InlineMessage {
                    Layout.fillWidth: true
                    visible: pending.searchEngine === "custom"
                             && pending.customSearchUrl.indexOf("%1") === -1
                    type: Kirigami.MessageType.Warning
                    text: qsTr("The URL must contain “%1” where the search terms go.").arg("%1")
                }

                Item { Layout.fillHeight: true }
            }
        }
    }

    // ── Downloads page ──────────────────────────────────────────────────
    Component {
        id: downloadsPage

        ScrollView {
            id: downloadsView
            contentWidth: availableWidth
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

            ColumnLayout {
                width: downloadsView.availableWidth
                spacing: Kirigami.Units.largeSpacing

                Kirigami.FormLayout {
                    Layout.fillWidth: true

                    RowLayout {
                        Kirigami.FormData.label: qsTr("Save files to:")

                        TextField {
                            Layout.preferredWidth: Kirigami.Units.gridUnit * 16
                            text: pending.downloadDirectory
                            readOnly: true
                            selectByMouse: true
                        }

                        Button {
                            text: qsTr("Choose…")
                            icon.name: "document-open-folder"
                            onClicked: downloadFolderDialog.open()
                        }
                    }

                    CheckBox {
                        id: askCheck
                        text: qsTr("Ask where to save each file")
                        onToggled: pending.askWhereToSave = checked
                    }

                    Binding {
                        target: askCheck
                        property: "checked"
                        value: pending.askWhereToSave
                    }
                }

                Kirigami.InlineMessage {
                    Layout.fillWidth: true
                    visible: !Settings.downloadDirectoryValid
                    type: Kirigami.MessageType.Warning
                    text: qsTr("The selected folder no longer exists. Downloads are saved to %1.")
                              .arg(Settings.downloadDirectory)
                }

                Item { Layout.fillHeight: true }
            }
        }
    }

    // ── Privacy page ────────────────────────────────────────────────────
    Component {
        id: privacyPage

        ScrollView {
            id: privacyView
            contentWidth: availableWidth
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

            ColumnLayout {
                width: privacyView.availableWidth
                spacing: Kirigami.Units.largeSpacing

                Kirigami.FormLayout {
                    Layout.fillWidth: true

                    CheckBox {
                        id: cookiesCheck
                        Kirigami.FormData.label: qsTr("Cookies:")
                        text: qsTr("Block third-party cookies")
                        onToggled: pending.blockThirdPartyCookies = checked
                    }

                    Binding {
                        target: cookiesCheck
                        property: "checked"
                        value: pending.blockThirdPartyCookies
                    }

                    CheckBox {
                        id: clearOnExitCheck
                        Kirigami.FormData.label: qsTr("On exit:")
                        text: qsTr("Clear cookies, cache and history")
                        onToggled: pending.clearDataOnExit = checked
                    }

                    Binding {
                        target: clearOnExitCheck
                        property: "checked"
                        value: pending.clearDataOnExit
                    }

                    Item { Kirigami.FormData.isSection: true }

                    Button {
                        Kirigami.FormData.label: qsTr("Browsing data:")
                        text: qsTr("Clear Cookies and Cache Now")
                        icon.name: "edit-clear-history"
                        onClicked: ProfileManager.clearCookiesAndCacheNow()
                    }

                    Item { Kirigami.FormData.isSection: true }

                    Button {
                        Kirigami.FormData.label: qsTr("Site permissions:")
                        text: qsTr("Manage Site Permissions…")
                        icon.name: "security-high"
                        onClicked: root.openSitePermissions()
                    }
                }

                Item { Layout.fillHeight: true }
            }
        }
    }

    // ── Site Permissions window (created on demand) ─────────────────────
    property var sitePermissionsWindow: null

    Component {
        id: sitePermissionsComponent
        SitePermissionsDialog {}
    }

    FolderDialog {
        id: downloadFolderDialog
        title: qsTr("Choose Download Folder")
        currentFolder: "file://" + pending.downloadDirectory
        onAccepted: pending.downloadDirectory = root.localPath(selectedFolder)
    }
}
