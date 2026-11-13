import QtQuick
import Kondor

Row {
    id: root

    required property TabModel tabs
    required property Item addressField

    readonly property alias bookmarkEditor: bookmarkButton.editor

    AdBlockButton {
        tabs: root.tabs
        addressField: root.addressField
    }

    ZoomButton { tabs: root.tabs }

    PasswordButton { tabs: root.tabs }

    ReaderButton { tabs: root.tabs }

    BookmarkButton {
        id: bookmarkButton
        tabs: root.tabs
    }
}
