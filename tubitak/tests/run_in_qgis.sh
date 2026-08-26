#!/bin/bash
# Run a script inside the QGIS APPLICATION process, headless.
#
# Use the app binary, not Contents/MacOS/python3.12. On macOS the app executable is signed
# with com.apple.security.cs.disable-library-validation and the bundled python3.12 is not,
# so onnxruntime's native extension loads in the former and is blocked in the latter
# ("different Team IDs"). The plugin runs in the app process, so that is what we test.
#
# QT_QPA_PLATFORM=offscreen replaces Xvfb (macOS has no X server).
set -e
APP="${QGIS_APP:-/Applications/QGIS-final-4_2_1.app}"
BIN="$(ls "$APP/Contents/MacOS/" | grep -E '^QGIS' | head -1)"
export QT_QPA_PLATFORM=offscreen
export GENCP_REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
export GENCP_TEST_OUT="${GENCP_TEST_OUT:-/tmp/gencp_plugin_test.txt}"
rm -f "$GENCP_TEST_OUT"
"$APP/Contents/MacOS/$BIN" --nologo --code "$@" >/dev/null 2>&1 &
PID=$!
for i in $(seq 1 900); do
  kill -0 $PID 2>/dev/null || break
  sleep 2
done
kill $PID 2>/dev/null || true
wait $PID 2>/dev/null || true
cat "$GENCP_TEST_OUT"
grep -q "^FAILED:" "$GENCP_TEST_OUT" && exit 1 || exit 0
