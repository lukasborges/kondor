// #102 Add a password by hand — the dialog when the login is already saved.
import QtQuick
import "common"

SettingsDialogMock { withPasswords: true; page: 4; innerTab: 0; addPasswordDialog: true; addPasswordDuplicate: true }
