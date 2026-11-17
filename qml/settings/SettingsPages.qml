import QtQuick

QtObject {
    id: root

    readonly property var pages: [
        {
            id: "general",
            title: qsTr("General"),
            icon: "internet-web-browser",
            keywords: [qsTr("Startup"), qsTr("New Tabs"), qsTr("On startup:"),
                       qsTr("Home page:"), qsTr("Show top sites"),
                       qsTr("Appearance"), qsTr("Tabs:"), qsTr("Floating"),
                       qsTr("Below Address Bar"), qsTr("Classic"),
                       qsTr("Performance"), qsTr("Memory:"),
                       qsTr("Put inactive tabs to sleep"), qsTr("Sleep after:")],
            options: ["startupBehavior", "homePage", "showTopSites", "tabStyle",
                       "tabSleepEnabled", "tabSleepMinutes"]
        },
        {
            id: "search",
            title: qsTr("Search"),
            icon: "system-search",
            keywords: [qsTr("Search engine:"), qsTr("Custom URL:"),
                       qsTr("Show search suggestions")],
            options: ["searchEngine", "customSearchUrl", "searchSuggestions"]
        },
        {
            id: "downloads",
            title: qsTr("Downloads"),
            icon: "folder-download",
            keywords: [qsTr("Save files to:"), qsTr("Ask where to save each file")],
            options: ["downloadDirectory", "askWhereToSave"]
        },
        {
            id: "privacy",
            title: qsTr("Privacy"),
            icon: "preferences-security",
            keywords: [qsTr("Cookies:"), qsTr("On exit:"),
                       qsTr("Clear cookies, cache and history"),
                       qsTr("Browsing data:"), qsTr("Clear Cookies and Cache Now"),
                       qsTr("Pop-ups:"), qsTr("Block pop-ups that open without a click"),
                       qsTr("Site permissions:"), qsTr("Manage Site Permissions…"),
                       qsTr("Remote control:"), qsTr("Allow automation tools to control pages"),
                       qsTr("Port:")],
            options: ["blockThirdPartyCookies", "clearDataOnExit", "adBlockEnabled",
                      "blockPopups",
                      "remoteControlEnabled", "remoteControlPort"]
        },
        {
            id: "passwords",
            title: qsTr("Passwords"),
            icon: "preferences-desktop-user-password",
            keywords: [qsTr("Offer to save passwords"), qsTr("Saved Passwords"),
                       qsTr("Never Saved"), qsTr("KWallet"),
                       qsTr("Filter by site or username…")],
            options: ["offerToSavePasswords"]
        },
        {
            id: "extensions",
            title: qsTr("Extensions"),
            icon: "preferences-plugin",
            keywords: [qsTr("Filter extensions…"), qsTr("Get New Extensions…"),
                       qsTr("Install from File…"), qsTr("Update extensions automatically")],
            options: ["extensionsAutoUpdate"]
        },
        {
            id: "spelling",
            title: qsTr("Spelling"),
            icon: "tools-check-spelling",
            keywords: [qsTr("Check spelling while typing"), qsTr("Languages:")],
            options: ["spellCheckEnabled", "spellCheckLanguages"]
        }
    ]

    function indexOf(pageId) {
        return pages.findIndex(page => page.id === pageId)
    }

    function matching(text) {
        const needle = text.trim().toLowerCase()
        const all = pages.map((page, index) => index)
        return needle.length === 0 ? all : all.filter(index => matchesPage(index, needle))
    }

    function matchesPage(index, needle) {
        const page = pages[index]
        return (page.title + " " + page.keywords.join(" ")).toLowerCase().includes(needle)
    }
}
