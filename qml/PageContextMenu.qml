// Context menu of a web page: link, image, media, selection, editable field
// and page actions. The items are rebuilt on every popup so only the ones
// that apply to the request are shown.
import QtQuick
import QtQuick.Controls
import QtWebEngine
import Kondor

Menu {
    id: menu

    // The request that opened the menu. Null when the menu was opened from
    // the keyboard: there is no link, image or selection to act on then.
    property var request: null
    property WebEngineView webView: null
    property Tab tab: null
    property TabModel tabModel: null

    // Popup.Item keeps the menu inside the window, like the other menus.
    popupType: Popup.Item

    // Opens the menu at a point in the view's coordinates.
    function popupAt(point) {
        rebuild()
        popup(webView, point.x, point.y)
    }

    function rebuild() {
        while (count > 0)
            removeItem(itemAt(0))

        const r = request
        const blocks = []
        if (r && r.linkUrl.toString() !== "")
            blocks.push(linkBlock(r))
        if (r && r.mediaType === ContextMenuRequest.MediaTypeImage)
            blocks.push(imageBlock(r))
        else if (r && (r.mediaType === ContextMenuRequest.MediaTypeVideo
                       || r.mediaType === ContextMenuRequest.MediaTypeAudio))
            blocks.push(mediaBlock(r))
        // The editing block already has Copy when the field is editable.
        if (r && r.selectedText !== "" && !r.isContentEditable)
            blocks.push(selectionBlock(r))
        if (r && r.isContentEditable)
            blocks.push(editingBlock(r))
        // "Open Link in New Window" arrives with #14, "Save Page As…" and
        // "Print…" with #17.
        if (blocks.length === 0)
            blocks.push(pageBlock())
        blocks.push([{ text: qsTr("Inspect Element"), icon: "code-context", action: "inspectElement" }])

        // One separator between blocks, none at the start, the end or doubled.
        let previousWasSeparator = true
        for (let i = 0; i < blocks.length; ++i) {
            if (!previousWasSeparator) {
                addSeparator()
                previousWasSeparator = true
            }
            for (const entry of blocks[i]) {
                if (entry === null) {
                    if (!previousWasSeparator) {
                        addSeparator()
                        previousWasSeparator = true
                    }
                } else {
                    addEntry(entry)
                    previousWasSeparator = false
                }
            }
        }
    }

    function linkBlock(r) {
        return [
            { text: qsTr("Open Link in New Tab"), icon: "tab-new", action: "openLinkNewTab" },
            { text: qsTr("Open Link in New Private Tab"), icon: "view-private", action: "openLinkNewPrivateTab" },
            null,
            { text: qsTr("Copy Link Address"), icon: "edit-copy", action: "copyLink" },
            { text: qsTr("Save Link As…"), icon: "document-save", action: "saveLink" }
        ]
    }

    function imageBlock(r) {
        return [
            { text: qsTr("Open Image in New Tab"), icon: "tab-new", action: "openImageNewTab" },
            { text: qsTr("Save Image As…"), icon: "document-save", action: "saveImage" },
            { text: qsTr("Copy Image"), icon: "edit-copy", action: "copyImage" },
            { text: qsTr("Copy Image Address"), icon: "edit-copy", action: "copyImageAddress" }
        ]
    }

    function mediaBlock(r) {
        const entries = [
            { text: qsTr("Save Media As…"), icon: "document-save", action: "saveMedia" },
            { text: qsTr("Copy Media Address"), icon: "edit-copy", action: "copyMediaAddress" }
        ]
        if (r.mediaFlags & ContextMenuRequest.MediaCanToggleControls) {
            entries.push(null)
            entries.push({
                text: qsTr("Show Controls"),
                icon: "view-media-equalizer",
                action: "toggleMediaControls",
                checkable: true,
                checked: (r.mediaFlags & ContextMenuRequest.MediaControls) !== 0
            })
        }
        entries.push({
            text: qsTr("Loop"),
            icon: "media-playlist-repeat",
            action: "toggleMediaLoop",
            checkable: true,
            checked: (r.mediaFlags & ContextMenuRequest.MediaLoop) !== 0
        })
        return entries
    }

    function selectionBlock(r) {
        const engine = Settings.searchEngineName()
        const snippet = shortText(r.selectedText)
        const searchText = engine.length > 0
            //: %1 is the search engine name, %2 the selected text
            ? qsTr("Search %1 for “%2”").arg(engine).arg(snippet)
            //: %1 is the selected text
            : qsTr("Search for “%1”").arg(snippet)
        return [
            { text: qsTr("Copy"), icon: "edit-copy", action: "copySelection" },
            { text: searchText, icon: "edit-find", action: "searchSelection" }
        ]
    }

    function editingBlock(r) {
        const entries = []
        if (r.misspelledWord !== "") {
            for (const suggestion of r.spellCheckerSuggestions) {
                entries.push({
                    text: suggestion,
                    action: "replaceMisspelling",
                    data: suggestion
                })
            }
            if (entries.length > 0)
                entries.push(null)
        }
        entries.push({ text: qsTr("Undo"), icon: "edit-undo", action: "undo",
                       enabled: (r.editFlags & ContextMenuRequest.CanUndo) !== 0 })
        entries.push({ text: qsTr("Redo"), icon: "edit-redo", action: "redo",
                       enabled: (r.editFlags & ContextMenuRequest.CanRedo) !== 0 })
        entries.push(null)
        entries.push({ text: qsTr("Cut"), icon: "edit-cut", action: "cut",
                       enabled: (r.editFlags & ContextMenuRequest.CanCut) !== 0 })
        entries.push({ text: qsTr("Copy"), icon: "edit-copy", action: "copySelection",
                       enabled: (r.editFlags & ContextMenuRequest.CanCopy) !== 0 })
        entries.push({ text: qsTr("Paste"), icon: "edit-paste", action: "paste",
                       enabled: (r.editFlags & ContextMenuRequest.CanPaste) !== 0 })
        entries.push({ text: qsTr("Paste as Plain Text"), icon: "edit-paste", action: "pastePlain",
                       enabled: (r.editFlags & ContextMenuRequest.CanPaste) !== 0 })
        entries.push({ text: qsTr("Select All"), icon: "edit-select-all", action: "selectAll",
                       enabled: (r.editFlags & ContextMenuRequest.CanSelectAll) !== 0 })
        return entries
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

    // Single line, at most 30 characters, for the search item's label.
    function shortText(text) {
        const singleLine = text.replace(/\s+/g, " ").trim()
        return singleLine.length > 30 ? singleLine.slice(0, 30) + "…" : singleLine
    }

    function addEntry(entry) {
        // Create with a null parent and let addItem() take ownership; a Menu is a
        // Popup, not an Item, so parenting to it makes Qt warn that the object was
        // not placed in the graphics scene.
        const item = itemComponent.createObject(null, {
            "text": entry.text,
            "iconName": entry.icon ?? "",
            "actionId": entry.action,
            "actionData": entry.data ?? "",
            "enabled": entry.enabled !== false,
            "checkable": entry.checkable === true,
            "checked": entry.checked === true
        })
        addItem(item)
    }

    function addSeparator() {
        addItem(separatorComponent.createObject(null))
    }

    function perform(action, data) {
        switch (action) {
        case "openLinkNewTab":
            tabModel.addTabWithProfile(tab.profile, request.linkUrl, false)
            break
        case "openLinkNewPrivateTab":
            tabModel.addTab(true, request.linkUrl)
            break
        case "copyLink":
            webView.triggerWebAction(WebEngineView.CopyLinkToClipboard)
            break
        case "saveLink":
            webView.triggerWebAction(WebEngineView.DownloadLinkToDisk)
            break
        case "openImageNewTab":
            tabModel.addTabWithProfile(tab.profile, request.mediaUrl, false)
            break
        case "saveImage":
            webView.triggerWebAction(WebEngineView.DownloadImageToDisk)
            break
        case "copyImage":
            webView.triggerWebAction(WebEngineView.CopyImageToClipboard)
            break
        case "copyImageAddress":
            webView.triggerWebAction(WebEngineView.CopyImageUrlToClipboard)
            break
        case "saveMedia":
            webView.triggerWebAction(WebEngineView.DownloadMediaToDisk)
            break
        case "copyMediaAddress":
            webView.triggerWebAction(WebEngineView.CopyMediaUrlToClipboard)
            break
        case "toggleMediaControls":
            webView.triggerWebAction(WebEngineView.ToggleMediaControls)
            break
        case "toggleMediaLoop":
            webView.triggerWebAction(WebEngineView.ToggleMediaLoop)
            break
        case "copySelection":
            webView.triggerWebAction(WebEngineView.Copy)
            break
        case "searchSelection":
            tabModel.addTabWithProfile(tab.profile,
                                       ProfileManager.resolveAddress(request.selectedText), false)
            break
        case "replaceMisspelling":
            webView.replaceMisspelledWord(data)
            break
        case "undo":
            webView.triggerWebAction(WebEngineView.Undo)
            break
        case "redo":
            webView.triggerWebAction(WebEngineView.Redo)
            break
        case "cut":
            webView.triggerWebAction(WebEngineView.Cut)
            break
        case "paste":
            webView.triggerWebAction(WebEngineView.Paste)
            break
        case "pastePlain":
            webView.triggerWebAction(WebEngineView.PasteAndMatchStyle)
            break
        case "selectAll":
            webView.triggerWebAction(WebEngineView.SelectAll)
            break
        case "back":
            webView.goBack()
            break
        case "forward":
            webView.goForward()
            break
        case "reload":
            webView.reload()
            break
        case "inspectElement":
            tab.inspectElement()
            break
        case "viewSource":
            webView.triggerWebAction(WebEngineView.ViewSource)
            break
        }
    }

    Component {
        id: itemComponent

        MenuItem {
            property string actionId
            property string actionData
            property string iconName

            icon.name: iconName
            onTriggered: menu.perform(actionId, actionData)
        }
    }

    Component {
        id: separatorComponent

        MenuSeparator {}
    }
}
