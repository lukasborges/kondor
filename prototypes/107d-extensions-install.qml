// #107 Kondor extensions — install confirmation for a catalog extension.
import QtQuick
import "common"

SettingsDialogMock { withPasswords: true; withExtensions: true; page: 5; installDialog: true }
