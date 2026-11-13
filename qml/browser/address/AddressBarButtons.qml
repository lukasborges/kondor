import QtQuick
import Kondor

Row {
    id: root

    required property TabModel tabs
    required property Item addressField

    signal passwordsManageRequested()

    readonly property alias bookmarkEditor: bookmarkButton.editor

    AdBlockButton {
        tabs: root.tabs
        addressField: root.addressField
    }

    ZoomButton { tabs: root.tabs }

    PasswordButton {
        tabs: root.tabs
        onManageRequested: root.passwordsManageRequested()
    }

    ReaderButton { tabs: root.tabs }

    BookmarkButton {
        id: bookmarkButton
        tabs: root.tabs
    }
}
