import QtQuick
import Kondor

QtObject {
    id: draft

    property string homePage: ""
    property string searchEngine: ""
    property string customSearchUrl: ""
    property string downloadDirectory: ""
    property bool askWhereToSave: false
    property string startupBehavior: ""
    property bool showTopSites: false
    property string tabStyle: "floating"
    property bool tabSleepEnabled: true
    property int tabSleepMinutes: 30
    property bool clearDataOnExit: false
    property bool blockThirdPartyCookies: false
    property bool adBlockEnabled: true
    property bool searchSuggestions: false
    property bool spellCheckEnabled: false
    property var spellCheckLanguages: []
    property bool offerToSavePasswords: true
    property bool extensionsAutoUpdate: true
    property bool remoteControlEnabled: false
    property int remoteControlPort: 9222

    readonly property var optionNames: [
        "homePage", "searchEngine", "customSearchUrl", "downloadDirectory",
        "askWhereToSave", "startupBehavior", "showTopSites", "tabStyle", "tabSleepEnabled",
        "tabSleepMinutes", "clearDataOnExit",
        "blockThirdPartyCookies", "adBlockEnabled", "searchSuggestions",
        "spellCheckEnabled", "spellCheckLanguages", "offerToSavePasswords",
        "extensionsAutoUpdate", "remoteControlEnabled", "remoteControlPort"
    ]

    readonly property var values: [homePage, searchEngine, customSearchUrl,
        downloadDirectory, askWhereToSave, startupBehavior, showTopSites,
        tabStyle, tabSleepEnabled, tabSleepMinutes, clearDataOnExit, blockThirdPartyCookies, adBlockEnabled, searchSuggestions,
        spellCheckEnabled, spellCheckLanguages, offerToSavePasswords, extensionsAutoUpdate,
        remoteControlEnabled, remoteControlPort]

    function read() {
        optionNames.forEach(name => { draft[name] = Settings[name] })
    }

    function isModified() {
        return optionNames.some(name => !isSame(draft[name], Settings[name]))
    }

    function apply() {
        const changed = optionNames.filter(name => !isSame(draft[name], Settings[name]))
        changed.forEach(name => { Settings[name] = draft[name] })
    }

    function isAtDefaults(names) {
        return names.every(name => isSame(draft[name], Settings.defaultValue(name)))
    }

    function restoreDefaults(names) {
        names.forEach(name => { draft[name] = Settings.defaultValue(name) })
    }

    function isSame(first, second) {
        if (typeof first !== "object")
            return first === second
        return first.length === second.length && first.every((value, i) => value === second[i])
    }
}
