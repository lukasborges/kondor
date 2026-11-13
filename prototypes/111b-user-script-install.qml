// #111 User scripts — install confirmation for a user script (Settings → Extensions).
import QtQuick
import "common"

SettingsDialogMock { withPasswords: true; withExtensions: true; page: 5; installDialog: true; installUserScript: true }
