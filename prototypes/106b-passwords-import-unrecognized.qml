// #106 Import passwords — the chosen file is not a password export.
import QtQuick
import "common"

SettingsDialogMock { withPasswords: true; page: 4; innerTab: 0; importDialog: true; importUnrecognized: true }
