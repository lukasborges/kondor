// #107 Kondor extensions — install confirmation for a .kondorext file.
import QtQuick
import "common"

SettingsDialogMock { withPasswords: true; withExtensions: true; page: 5; installDialog: true; installFromFile: true }
