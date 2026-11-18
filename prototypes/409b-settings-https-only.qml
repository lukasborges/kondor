// #409 HTTPS-only mode: the option on Settings → Privacy, off by default (checked here).
import QtQuick
import "common"

SettingsDialogMock { page: 3; withHttpsOnly: true }
