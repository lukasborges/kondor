import re
from pathlib import Path

from PySide6.QtCore import QCoreApplication, QEvent, QObject, QSize, QUrl
from PySide6.QtGui import QImage
from PySide6.QtQml import QQmlComponent, QQmlEngine, QQmlExpression, qmlContext
from PySide6.QtQuick import QQuickImageProvider, QQuickWindow
from PySide6.QtTest import QTest

from kondor.browser.tabs.tabmodel import TabModel
from tests.qmlsupport import error_text, load_component

QML_APP_DIRECTORY = Path(__file__).resolve().parents[3] / "qml" / "app"
FAVICON_PROVIDER = "kondor-favicon"
ROW_SCRIPT = (
    "(function(menu) { const rows = [];"
    " for (let i = 0; i < menu.count; ++i) { const it = menu.itemAt(i);"
    "   const kind = it.toString();"
    "   if (kind.indexOf('MenuSeparator') >= 0) rows.push('-');"
    "   else if (typeof it.text === 'string') rows.push(it.text);"
    "   else rows.push('[row]'); }"
    " return rows.join('|') })(%s)"
)
KEPT_COMPONENTS: list[QQmlComponent] = []


def expected_top_level_rows() -> list[str]:
    return [
        *["New Tab", "New Private Tab", "New Window", "New Private Window", "Profiles", "-"],
        *["Bookmarks", "History", "-", "Find in Page…", "Print…", "Save Page As…", "-"],
        *["[row]", "-", "More Tools", "-", "Configure Kondor Browser…", "Help"],
    ]


def expected_more_tools_rows() -> list[str]:
    return ["Developer Tools", "Save as PDF…", "Site Permissions…"]


def expected_help_rows() -> list[str]:
    return ["Report a Bug…", "-", "About Kondor Browser"]


def without_separators(rows: list[str]) -> list[str]:
    return [row for row in rows if row != "-"]


def sequences_in(file_name: str, pattern: str) -> list[str]:
    text = (QML_APP_DIRECTORY / file_name).read_text()
    return [match.group(1) for match in re.finditer(pattern, text)]


class EmptyImageProvider(QQuickImageProvider):
    def __init__(self) -> None:
        super().__init__(QQuickImageProvider.ImageType.Image)

    def requestImage(self, id: str, size: QSize, requestedSize: QSize) -> QImage:  # noqa: A002, N803
        image = QImage(1, 1, QImage.Format.Format_ARGB32)
        image.fill(0)
        size.setWidth(1)
        size.setHeight(1)
        return image


def add_favicon_provider(engine: QQmlEngine) -> None:
    if engine.imageProvider(FAVICON_PROVIDER) is not None:
        return
    engine.addImageProvider(FAVICON_PROVIDER, EmptyImageProvider())


def create_window(engine: QQmlEngine, source: str) -> QQuickWindow:
    component = load_component(engine, source)
    created = component.create()
    assert isinstance(created, QQuickWindow), error_text(component)
    QQmlEngine.setObjectOwnership(created, QQmlEngine.ObjectOwnership.CppOwnership)
    KEPT_COMPONENTS.append(component)
    return created


class MainMenuHarness:
    def __init__(self, engine: QQmlEngine, source: str) -> None:
        self.window = create_window(engine, source)
        self.tabs = self.window.findChild(TabModel)

    def show(self) -> None:
        self.tabs.addTab(False, QUrl("https://a.example"))
        self.window.show()
        self.window.requestActivate()
        assert QTest.qWaitForWindowActive(self.window)

    def evaluate(self, script: str) -> object:
        expression = QQmlExpression(qmlContext(self.window), self.window, script)
        value, _is_undefined = expression.evaluate()
        return value

    def wait_until_opened(self) -> bool:
        for _ in range(100):
            if self.evaluate("mainMenu.opened") is True:
                return True
            QTest.qWait(20)
        return False

    def rows_of(self, menu_expression: str) -> list[str]:
        return str(self.evaluate(ROW_SCRIPT % menu_expression)).split("|")

    def close(self) -> None:
        self.window.close()
        self.window.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def stub_property(window: QObject, name: str) -> object:
    return window.property(name)
