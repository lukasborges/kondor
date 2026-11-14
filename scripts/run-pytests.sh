#!/usr/bin/env bash
# Runs the Python tests offscreen, on a private D-Bus session and with temporary XDG folders, then
# stops every process that session started. Tests can wake desktop services (ksecretd,
# xdg-desktop-portal-kde) that outlive a plain `dbus-run-session` and keep the output pipe open,
# so `… | tail` would never return (#222).
#
#   scripts/run-pytests.sh                     # all of pytests/
#   scripts/run-pytests.sh pytests/passwords -x
set -uo pipefail

main() {
  local bus address daemon home status
  bus="$(dbus-daemon --session --fork --print-address --print-pid)" || exit 1
  address="$(sed -n 1p <<<"$bus")"
  daemon="$(sed -n 2p <<<"$bus")"
  home="$(mktemp -d)"
  run_tests "$address" "$home" "$@"
  status=$?
  stop_bus "$address" "$daemon"
  rm -rf "$home"
  exit "$status"
}

run_tests() {
  local address="$1" home="$2"
  shift 2
  DBUS_SESSION_BUS_ADDRESS="$address" QT_QPA_PLATFORM=offscreen \
    XDG_CONFIG_HOME="$home/config" XDG_DATA_HOME="$home/data" XDG_CACHE_HOME="$home/cache" \
    python3 -m pytest "${@:-pytests}" </dev/null
}

# Stops the processes attached to this private bus, then the bus itself. Processes on any other
# bus, such as the desktop session's, are never touched.
stop_bus() {
  local pid
  for pid in $(pgrep -u "$(id -u)"); do
    on_bus "$pid" "$1" && kill "$pid" 2>/dev/null
  done
  kill "$2" 2>/dev/null
}

on_bus() {
  tr '\0' '\n' 2>/dev/null <"/proc/$1/environ" | grep -qxF "DBUS_SESSION_BUS_ADDRESS=$2"
}

main "$@"
