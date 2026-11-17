from collections.abc import Callable

from PySide6.QtCore import QCoreApplication, QUrl

from kondor.app.instance.sessionprotocol import ClientIdentity
from kondor.app.instance.singleinstance import SingleInstance, server_name_for
from kondor.app.instance.singleinstancemessage import SingleInstanceMessage
from kondor.app.mcp.protocol.dispatcher import Dispatcher
from kondor.app.mcp.server import mcpoptions
from kondor.app.mcp.server.stdioserver import StdioServer
from kondor.app.mcp.session import browserprocess
from kondor.app.mcp.session.browserlink import BrowserLink
from kondor.app.mcp.session.remotebrowser import RemoteBrowser
from kondor.app.mcp.tools.toolset import all_tools
from kondor.app.startup.stagedbuild import PROJECT_VERSION
from kondor.profiles.activeprofile import ActiveProfile


def name_application(app: QCoreApplication) -> None:
    app.setOrganizationName("KDE")
    app.setApplicationName("Kondor")
    app.setApplicationVersion(PROJECT_VERSION)


def open_url_function(server_name: str) -> Callable[[str], bool]:
    sender = SingleInstance(server_name)
    return lambda url: sender.send_message(SingleInstanceMessage(urls=[QUrl(url)]))


def build_server(server_name: str) -> tuple[StdioServer, BrowserLink]:
    link = BrowserLink(server_name, browserprocess.start_detached)
    browser = RemoteBrowser(link, open_url_function(server_name))
    dispatcher = Dispatcher(all_tools(), browser, PROJECT_VERSION)
    dispatcher.on_client_known = lambda name, version: browser.set_client(
        ClientIdentity(name, version)
    )
    return StdioServer(dispatcher), link


def start_serving(profile_id: str) -> int:
    app = QCoreApplication.instance()
    ActiveProfile.select(profile_id)
    server, link = build_server(server_name_for(profile_id))
    server.finished.connect(app.quit)
    link.closed.connect(app.quit)
    app.exec()
    link.close()
    return 0


def run(arguments: list[str]) -> int:
    name_application(QCoreApplication(["kondor"]))
    options = mcpoptions.parse(arguments)
    if options is None:
        return mcpoptions.INVALID_ARGUMENT_STATUS
    profile_id = mcpoptions.profile_id_for(options.profile)
    return 1 if profile_id is None else start_serving(profile_id)
