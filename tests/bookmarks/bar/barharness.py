from PySide6.QtCore import QCoreApplication, QEvent, QObject
from PySide6.QtQml import QQmlComponent, QQmlEngine, QQmlExpression, qmlContext
from PySide6.QtTest import QTest

from kondor.browser.profile.profilemanager import ProfileManager
from kondor.browser.tabs.tabmodel import TabModel
from tests.bookmarks.bookmarkrows import add_page, manager
from tests.qmlsupport import error_text, load_component

BAR_QML = """
import QtQml
import QtWebEngine
import Kondor

BookmarksBar {
    width: %d
    height: 36
}
"""
MENU_QML = """
import QtQml
import Kondor

BookmarkMenu {
    property var texts: {
        const found = []
        for (let i = staticCount; i < count; ++i)
            found.push(itemAt(i).text)
        return found
    }
}
"""
TARGETS_QML = """
import QtQuick
import Kondor

Item {
    function moveDragged(id, position) {
        controller.draggedId = id
        controller.dropPosition = position
        dropTargets.completeMove()
    }

    function titleOfDrop(drop) {
        return linkDrop.linkOf(drop).title
    }

    function dropLinkAtTheStart() {
        controller.dropPosition = 0
        dropTargets.completeLinkDrop({ url: "https://dropped.example/", title: "Dropped" })
    }

    function dropPositionAt(x) {
        dropTargets.dropAtPosition(dropTargets.itemUnder(x))
        return controller.dropPosition
    }

    Item { id: previewItem }
    BookmarkFolderTree { id: tree; folders: BookmarkManager.folders }
    BookmarkDragController { id: controller; preview: previewItem; folderTree: tree }
    Repeater {
        id: items
        model: 3
        Item { required property int index; x: index * 60; width: 50; height: 20 }
    }
    BookmarksBarDropTargets {
        id: dropTargets
        drag: controller
        folderTree: tree
        items: items
        visibleCount: 3
    }
    BookmarksBarLinkDrop { id: linkDrop; targets: dropTargets }
}
"""
KEPT: list[QQmlComponent] = []
CREATED: list[QObject] = []


def create_with(engine: QQmlEngine, source: str, properties: dict[str, object]) -> QObject:
    component = load_component(engine, source)
    KEPT.append(component)
    created = component.createWithInitialProperties(properties)
    assert created is not None, error_text(component)
    CREATED.append(created)
    return created


def release_created_objects() -> None:
    for created in reversed(CREATED):
        created.deleteLater()
    CREATED.clear()
    KEPT.clear()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def create_bar(engine: QQmlEngine, tabs: TabModel, width: int) -> QObject:
    return create_with(engine, BAR_QML % width, {"tabModel": tabs})


def create_menu(engine: QQmlEngine, folder_id: int, can_add_page: bool) -> QObject:
    return create_with(
        engine,
        MENU_QML,
        {"folderId": folder_id, "showFolderActions": True, "canAddPage": can_add_page},
    )


def evaluate(item: QObject, engine: QQmlEngine, script: str) -> object:
    expression = QQmlExpression(qmlContext(item) or engine.rootContext(), item, script)
    value = expression.evaluate()
    assert not expression.hasError(), expression.error().toString()
    return value[0]


def fill_toolbar(count: int) -> None:
    for number in range(count):
        add_page(manager().toolbarFolderId(), f"Bookmark number {number}", f"page{number}")
    QTest.qWait(50)


def release_profiles() -> None:
    profiles = ProfileManager.instance()
    for profile in [*profiles._private_profiles, profiles._default_profile]:
        if profile is not None:
            profile.deleteLater()
    profiles._default_profile = None
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
