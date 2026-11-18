import json
import os
import sys
from pathlib import Path

os.environ["QTWEBENGINE_REMOTE_DEBUGGING"] = "127.0.0.1:" + sys.argv[1]

from PySide6.QtCore import QFile, QIODevice, QPoint, Qt, QUrl  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402
from PySide6.QtWebChannel import QWebChannel  # noqa: E402
from PySide6.QtWebEngineCore import QWebEngineScript  # noqa: E402
from PySide6.QtWebEngineWidgets import QWebEngineView  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from kondor.app.mcp.cdp.blocking import wait_until  # noqa: E402
from kondor.app.mcp.cdp.cdpconnection import CdpConnection  # noqa: E402
from kondor.app.mcp.cdp.pagetargets import TargetLister  # noqa: E402
from kondor.browser.pointer.agentpointerbridge import AgentPointerBridge  # noqa: E402
from kondor.browser.pointer.realinputwatch import RealInputWatch  # noqa: E402

SOURCE = Path(sys.argv[2])
HTML = "<html><body><button id='go' style='width:150px;height:60px'>Go</button></body></html>"
MAIN_WORLD = QWebEngineScript.ScriptWorldId.MainWorld
CHANNEL_SCRIPT = (
    "window.__kondorChannel = new Promise(resolve => new QWebChannel("
    "qt.webChannelTransport, channel => resolve(channel.objects)));"
)
BUTTON = {"x": 40, "y": 30}


def read_resource(path: str) -> str:
    file = QFile(path)
    file.open(QIODevice.OpenModeFlag.ReadOnly)
    return bytes(file.readAll().data()).decode()


class Scenario:
    def __init__(self) -> None:
        self.app = QApplication([])
        self.bridge = AgentPointerBridge()
        self.moves: list[tuple[float, float]] = []
        self.presses: list[tuple[float, float]] = []
        self.bridge.agentMoved.connect(lambda x, y: self.moves.append((x, y)))
        self.bridge.agentPressed.connect(lambda x, y: self.presses.append((x, y)))
        self.view = QWebEngineView()
        self.view.resize(400, 300)
        self.install_scripts()
        self.view.show()
        self.watch = RealInputWatch()
        self.watch.window = self.view.windowHandle()
        self.watch.active = True
        self.load_page()
        self.cdp = self.connect_cdp()

    def install_scripts(self) -> None:
        channel = QWebChannel(self.view)
        channel.registerObject("kondorAgentPointer", self.bridge.pageApi())
        self.view.page().setWebChannel(channel, MAIN_WORLD.value)
        channel_source = read_resource(":/qtwebchannel/qwebchannel.js")
        source = channel_source + CHANNEL_SCRIPT + SOURCE.read_text()
        script = QWebEngineScript()
        script.setSourceCode(source)
        script.setWorldId(MAIN_WORLD.value)
        script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
        self.view.page().scripts().insert(script)

    def load_page(self) -> None:
        self.view.setHtml(HTML, QUrl("http://localhost/"))
        wait_until(lambda: False, 3000)

    def connect_cdp(self) -> CdpConnection:
        target = TargetLister(int(sys.argv[1])).list_pages()[0]
        connection = CdpConnection(target.socket_url)
        assert connection.open()
        return connection

    def settle(self) -> None:
        wait_until(lambda: False, 600)

    def reset(self) -> None:
        self.moves.clear()
        self.presses.clear()

    def real_press(self) -> None:
        window = self.view.windowHandle()
        point = QPoint(BUTTON["x"], BUTTON["y"])
        QTest.mouseMove(window, point)
        wait_until(lambda: False, 1000)
        self.reset()
        QTest.mouseClick(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, point)
        self.settle()

    def cdp_mouse(self, kind: str) -> None:
        params = {**BUTTON, "type": kind, "button": "left", "clickCount": 1}
        self.cdp.call("Input.dispatchMouseEvent", params)

    def cdp_click(self) -> None:
        self.reset()
        for kind in ("mouseMoved", "mousePressed", "mouseReleased"):
            self.cdp_mouse(kind)
        self.settle()

    def scripted_click(self) -> None:
        self.reset()
        self.cdp.call("Runtime.evaluate", {"expression": "document.body.click()"})
        self.settle()

    def cdp_enter_key(self) -> None:
        self.cdp.call("Runtime.evaluate", {"expression": "document.getElementById('go').focus()"})
        self.reset()
        for kind in ("keyDown", "keyUp"):
            key = {"type": kind, "key": "Enter", "code": "Enter", "windowsVirtualKeyCode": 13}
            self.cdp.call("Input.dispatchKeyEvent", {**key, "text": "\r"})
        self.settle()


def main() -> None:
    scenario = Scenario()
    results: dict[str, dict[str, int]] = {}
    for name, action in (
        ("real_press", scenario.real_press),
        ("scripted_click", scenario.scripted_click),
        ("cdp_enter", scenario.cdp_enter_key),
        ("cdp_click", scenario.cdp_click),
    ):
        action()
        results[name] = {"moves": len(scenario.moves), "presses": len(scenario.presses)}
    print("RESULT" + json.dumps(results))


if __name__ == "__main__":
    main()
