import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import QtCore
import Kondor

StackLayout {
    id: root

    property bool offerToSave: true
    property int tab: 0
    signal offerToSaveToggled(bool checked)

    readonly property bool walletDenied: PasswordStore.state === "unavailable"
    readonly property bool active: root.visible && Window.window !== null && Window.window.visible
    readonly property RevealedPasswords revealed: RevealedPasswords {}
    readonly property ImportResult importResult: ImportResult {}

    function openPage() {
        PasswordStore.ensureOpen()
        savedTab.rebuild()
    }

    function closePage() {
        root.revealed.clear()
        addDialog.close()
        addDialog.clear()
        importDialog.close()
        PasswordStore.cancelImport()
        root.importResult.done = false
    }

    function askToDelete(origin, username) {
        deleteDialog.origin = origin
        deleteDialog.username = username
        deleteDialog.open()
    }

    function prepareImport(file) {
        root.importResult.done = false
        importDialog.openFor(PasswordStore.prepareImport(file))
        root.importResult.file = file
    }

    currentIndex: root.tab
    onActiveChanged: root.active ? root.openPage() : root.closePage()

    AddPasswordDialog {
        id: addDialog
        parent: Overlay.overlay
        onSaved: function(origin, username) { savedTab.showLogin(origin, username) }
    }

    FileDialog {
        id: importFileDialog
        title: qsTr("Import Passwords")
        fileMode: FileDialog.OpenFile
        currentFolder: StandardPaths.writableLocation(StandardPaths.DownloadLocation)
        nameFilters: [qsTr("CSV files (*.csv)"), qsTr("All files (*)")]
        onAccepted: root.prepareImport(selectedFile)
    }

    ImportPasswordsDialog {
        id: importDialog
        parent: Overlay.overlay
        onImported: function(count, fileName) { root.importResult.finish(count, fileName) }
    }

    ConfirmDialog {
        id: deleteDialog
        property string origin: ""
        property string username: ""
        title: qsTr("Delete Saved Password")
        message: qsTr("Delete the saved password for %1 on %2?")
                 .arg(deleteDialog.username).arg(deleteDialog.origin.replace(/^https?:[/][/]/, ""))
        acceptText: qsTr("Delete")
        acceptIcon: "edit-delete"
        onAccepted: PasswordStore.remove(deleteDialog.origin, deleteDialog.username)
    }

    SavedPasswordsTab {
        id: savedTab
        walletDenied: root.walletDenied
        offerToSave: root.offerToSave
        importResult: root.importResult
        revealed: root.revealed
        onOfferToSaveToggled: function(checked) { root.offerToSaveToggled(checked) }
        onAddRequested: addDialog.open()
        onImportRequested: importFileDialog.open()
        onDeleteRequested: function(origin, username) { root.askToDelete(origin, username) }
    }

    NeverSavedTab {}
}
