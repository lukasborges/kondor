import os

from PySide6.QtCore import QProcess

from kondor.app.remotecontrol import mcpcommand


def start_detached() -> None:
    words = mcpcommand.launch_words(os.environ)
    QProcess.startDetached(words[0], words[1:])
