#!/usr/bin/env bash
# Builds the AppDir of the Kondor AppImage from the packages of the host (Fedora).
# Used by .github/workflows/release.yml and scripts/local-appimage.sh.
#
#   packaging/appimage/prepare-appdir.sh <AppDir>
set -euo pipefail

appdir="$(realpath -m "${1:?usage: prepare-appdir.sh <AppDir>}")"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repository="$(cd "$here/../.." && pwd)"
qt_libraries=/usr/lib64/qt6
python_version="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
python_library="$appdir/usr/lib/python$python_version"

copy_python() {
  mkdir -p "$appdir/usr/bin" "$python_library"
  cp "$(readlink -f /usr/bin/python3)" "$appdir/usr/bin/python3"
  cp -r "/usr/lib64/python$python_version/." "$python_library/"
  rm -rf "$python_library/site-packages" "$python_library/test"
  mkdir -p "$python_library/site-packages"
}

copy_pyside() {
  local site="/usr/lib/python$python_version/site-packages" target="$python_library/site-packages"
  cp -r "$site/shiboken6" "$site/jeepney" "$site/langdetect" "$site/six.py" "$target/"
  mkdir -p "$target/PySide6"
  cp "$site/PySide6/__init__.py" "$site/PySide6/_config.py" "$target/PySide6/"
  while read -r module; do
    cp "$site"/PySide6/Qt"$module".*.so "$target/PySide6/"
  done < "$here/pyside-modules.txt"
}

copy_web_engine() {
  mkdir -p "$appdir/usr/libexec" "$appdir/usr/lib" "$appdir/usr/share/qt6"
  cp "$qt_libraries/libexec/QtWebEngineProcess" "$appdir/usr/libexec/"
  cp -P /usr/lib64/libQt6Quick*.so* "$appdir/usr/lib/"
  cp -r /usr/share/qt6/resources /usr/share/qt6/translations "$appdir/usr/share/qt6/"
}

copy_qml_modules() {
  local module
  mkdir -p "$appdir/usr/qml/org/kde"
  for module in QtQuick QtQml QtWebEngine QtWebChannel QtCore; do
    cp -r "$qt_libraries/qml/$module" "$appdir/usr/qml/"
  done
  cp -r "$qt_libraries"/qml/org/kde/{kirigami,desktop,qqc2desktopstyle,sonnet,union,kitemmodels} "$appdir/usr/qml/org/kde/"
}

copy_plugin() {
  mkdir -p "$appdir/usr/plugins/$(dirname "$1")"
  cp -r "$qt_libraries/plugins/$1" "$appdir/usr/plugins/$1"
}

copy_plugins() {
  local plugin
  copy_plugin tls
  for plugin in platforms/libqxcb.so platforms/libqwayland.so platforms/libqoffscreen.so \
      sqldrivers/libqsqlite.so platformthemes/KDEPlasmaPlatformTheme6.so styles/breeze6.so \
      kf6/kirigami/platform/org.kde.desktop.so iconengines/libqsvgicon.so; do
    copy_plugin "$plugin"
  done
  for plugin in "$qt_libraries"/plugins/wayland-*; do
    copy_plugin "${plugin#"$qt_libraries"/plugins/}"
  done
}

install_kondor() {
  python3 "$repository/scripts/build.py" --out "$(mktemp -d)" --install "$appdir/usr"
  cp "$here/AppRun" "$appdir/AppRun"
  cp "$repository/packaging/kondor.desktop" "$repository/packaging/kondor.png" "$appdir/"
}

copy_python
copy_pyside
copy_web_engine
copy_qml_modules
copy_plugins
install_kondor
