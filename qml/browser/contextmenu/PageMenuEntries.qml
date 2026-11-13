import QtQuick
import QtWebEngine
import Kondor

QtObject {
    id: root

    required property WebEngineView webView

    readonly property var linkEntries: [
        { text: qsTr("Open Link in New Tab"), icon: "tab-new", action: "openLinkNewTab" },
        { text: qsTr("Open Link in New Private Tab"), icon: "view-private", action: "openLinkNewPrivateTab" },
        null,
        { text: qsTr("Copy Link Address"), icon: "edit-copy", action: "copyLink" },
        { text: qsTr("Save Link As…"), icon: "document-save", action: "saveLink" }
    ]
    readonly property var imageEntries: [
        { text: qsTr("Open Image in New Tab"), icon: "tab-new", action: "openImageNewTab" },
        { text: qsTr("Save Image As…"), icon: "document-save", action: "saveImage" },
        { text: qsTr("Copy Image"), icon: "edit-copy", action: "copyImage" },
        { text: qsTr("Copy Image Address"), icon: "edit-copy", action: "copyImageAddress" }
    ]
    readonly property var mediaEntries: [
        { text: qsTr("Save Media As…"), icon: "document-save", action: "saveMedia" },
        { text: qsTr("Copy Media Address"), icon: "edit-copy", action: "copyMediaAddress" }
    ]
    readonly property var historyEditEntries: [
        { text: qsTr("Undo"), icon: "edit-undo", action: "undo", flag: ContextMenuRequest.CanUndo },
        { text: qsTr("Redo"), icon: "edit-redo", action: "redo", flag: ContextMenuRequest.CanRedo }
    ]
    readonly property var clipboardEditEntries: [
        { text: qsTr("Cut"), icon: "edit-cut", action: "cut", flag: ContextMenuRequest.CanCut },
        { text: qsTr("Copy"), icon: "edit-copy", action: "copySelection", flag: ContextMenuRequest.CanCopy },
        { text: qsTr("Paste"), icon: "edit-paste", action: "paste", flag: ContextMenuRequest.CanPaste },
        { text: qsTr("Paste as Plain Text"), icon: "edit-paste", action: "pastePlain", flag: ContextMenuRequest.CanPaste },
        { text: qsTr("Select All"), icon: "edit-select-all", action: "selectAll", flag: ContextMenuRequest.CanSelectAll }
    ]
    readonly property var inspectBlock: [
        { text: qsTr("Inspect Element"), icon: "code-context", action: "inspectElement" }
    ]

    function blocksFor(request) {
        const blocks = request ? requestBlocks(request) : []
        if (blocks.length === 0)
            blocks.push(pageBlock())
        blocks.push(inspectBlock)
        return blocks
    }

    function requestBlocks(request) {
        const blocks = []
        if (request.linkUrl.toString() !== "")
            blocks.push(linkEntries)
        return blocks.concat(mediaBlocks(request), selectionOrEditingBlocks(request))
    }

    function mediaBlocks(request) {
        if (request.mediaType === ContextMenuRequest.MediaTypeImage)
            return [imageEntries]
        const isMedia = request.mediaType === ContextMenuRequest.MediaTypeVideo
                || request.mediaType === ContextMenuRequest.MediaTypeAudio
        return isMedia ? [mediaBlock(request)] : []
    }

    function selectionOrEditingBlocks(request) {
        if (request.isContentEditable)
            return [editingBlock(request)]
        return request.selectedText !== "" ? [selectionBlock(request)] : []
    }

    function toggleEntry(entry, isChecked) {
        return Object.assign({ checkable: true, checked: isChecked }, entry)
    }

    function mediaBlock(request) {
        const flags = request.mediaFlags
        const canToggleControls = (flags & ContextMenuRequest.MediaCanToggleControls) !== 0
        const controls = canToggleControls ? [null, controlsEntry(flags)] : []
        return mediaEntries.concat(controls, [loopEntry(flags)])
    }

    function controlsEntry(flags) {
        return toggleEntry({ text: qsTr("Show Controls"), icon: "view-media-equalizer",
                             action: "toggleMediaControls" },
                           (flags & ContextMenuRequest.MediaControls) !== 0)
    }

    function loopEntry(flags) {
        return toggleEntry({ text: qsTr("Loop"), icon: "media-playlist-repeat",
                             action: "toggleMediaLoop" },
                           (flags & ContextMenuRequest.MediaLoop) !== 0)
    }

    function selectionBlock(request) {
        return [
            { text: qsTr("Copy"), icon: "edit-copy", action: "copySelection" },
            { text: searchText(request.selectedText), icon: "edit-find", action: "searchSelection" }
        ]
    }

    function searchText(selectedText) {
        const engine = Settings.searchEngineName()
        const snippet = shortText(selectedText)
        //: %1 is the search engine name, %2 the selected text
        return engine.length > 0 ? qsTr("Search %1 for “%2”").arg(engine).arg(snippet)
                                 //: %1 is the selected text
                                 : qsTr("Search for “%1”").arg(snippet)
    }

    function editEntry(entry, editFlags) {
        return Object.assign({}, entry, { enabled: (editFlags & entry.flag) !== 0 })
    }

    function suggestionEntries(request) {
        const entries = request.spellCheckerSuggestions.slice(0, 5).map(function(suggestion) {
            return { text: suggestion, action: "replaceMisspelling", data: suggestion, bold: true }
        })
        return entries.length > 0 ? entries.concat([null]) : entries
    }

    function editingBlock(request) {
        const flags = request.editFlags
        const suggestions = request.misspelledWord !== "" ? suggestionEntries(request) : []
        return suggestions
            .concat(historyEditEntries.map(entry => editEntry(entry, flags)), [null])
            .concat(clipboardEditEntries.map(entry => editEntry(entry, flags)), spellCheckEntries())
    }

    function spellCheckEntries() {
        const isAvailable = Settings.spellCheckEnabled && Settings.availableSpellCheckLanguages().length > 0
        return isAvailable ? [null, { spellCheckLanguages: true }] : []
    }

    function pageBlock() {
        return [
            { text: qsTr("Back"), icon: "go-previous", action: "back", enabled: webView.canGoBack },
            { text: qsTr("Forward"), icon: "go-next", action: "forward", enabled: webView.canGoForward },
            { text: qsTr("Reload"), icon: "view-refresh", action: "reload" },
            null,
            { text: qsTr("View Page Source"), icon: "text-html", action: "viewSource" }
        ]
    }

    function shortText(text) {
        const singleLine = text.replace(/\s+/g, " ").trim()
        return singleLine.length > 30 ? singleLine.slice(0, 30) + "…" : singleLine
    }
}
