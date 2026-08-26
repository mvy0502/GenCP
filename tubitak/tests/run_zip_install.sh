#!/bin/bash
# Install gencp_plugin.zip into a CLEAN QGIS profile and run one generation from it.
#
# The profile is DESTROYED before the run, so "clean" means clean and not "clean the first
# time". The development profile (default) is never touched, and neither is its symlink.
set -e
APP="${QGIS_APP:-/Applications/QGIS-final-4_2_1.app}"
BIN="$(ls "$APP/Contents/MacOS/" | grep -E '^QGIS' | head -1)"
PROFILE="${GENCP_TEST_PROFILE:-gencp_zip_test}"
PROFDIR="$HOME/Library/Application Support/QGIS/QGIS4/profiles/$PROFILE"

export GENCP_REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
export GENCP_PLUGIN_ZIP="${GENCP_PLUGIN_ZIP:-$GENCP_REPO_ROOT/tubitak/data/dist/gencp_plugin.zip}"
export GENCP_TEST_OUT="${GENCP_TEST_OUT:-/tmp/gencp_zip_install.txt}"
# (no QT_QPA_PLATFORM here on purpose - see the note below)

if [ ! -f "$GENCP_PLUGIN_ZIP" ]; then
  echo "no zip at $GENCP_PLUGIN_ZIP - run tubitak/scripts/build_plugin_zip.py first" >&2
  exit 2
fi
case "$PROFDIR" in
  *"/profiles/gencp_zip_test") rm -rf "$PROFDIR" ;;
  *) echo "refusing to delete profile '$PROFILE' - only gencp_zip_test is disposable" >&2
     exit 2 ;;
esac
rm -f "$GENCP_TEST_OUT"

# One setting is pre-seeded into the otherwise-empty profile, and it is not about the
# plugin. On a profile it has never seen before, QGIS calls
# QgsAuthManager::createAndStoreRandomMasterPasswordInKeyChain(), which asks the macOS
# Keychain for permission and blocks in an event loop until a human answers. Offscreen
# there is no human, so QGIS never finishes starting and the --code script never runs -
# observed here as a 22-minute hang with an empty output file and a main-thread stack
# sitting in passwordHelperWrite(). Turning the password helper off is the documented way
# to run QGIS unattended; it installs nothing and enables no plugin.
# Getting QGIS to start at all on a profile it has never seen is the whole difficulty
# here, and none of it is about the plugin. On a fresh profile QgisApp calls
# QgsAuthManager::createAndStoreRandomMasterPasswordInKeyChain(), and QtKeychain's macOS
# WRITE never completes under QT_QPA_PLATFORM=offscreen: the run sits in
# passwordHelperWrite() forever with an empty output file. Observed three times, at 22
# minutes each, with the stack sampled to confirm it. The default profile does not hit
# this only because it already HAS a stored password, so QGIS reads instead of writing -
# and reads do complete offscreen.
#
# So the item is created here, non-interactively, with -A so no authorization dialog can
# be raised. QGIS then finds it and never writes. This grants nothing to the plugin and
# installs nothing: the profile still has no plugins and no symlink, which is what "clean"
# has to mean for this test.
KEYCHAIN_ACCT="QGIS-Master-Password$PROFILE"
security delete-generic-password -s "QGIS" -a "$KEYCHAIN_ACCT" >/dev/null 2>&1 || true
security add-generic-password -s "QGIS" -a "$KEYCHAIN_ACCT" \
    -w "gencp-zip-install-test" -U -A >/dev/null 2>&1 || true

mkdir -p "$PROFDIR/qgis.org"
cat > "$PROFDIR/qgis.org/QGIS4.ini" <<'INI'
[authentication]
password_helper_enabled=true
INI

"$APP/Contents/MacOS/$BIN" --profile "$PROFILE" --nologo \
    --code "$GENCP_REPO_ROOT/tubitak/tests/plugin_zip_install.py" >/dev/null 2>&1 &
PID=$!
for i in $(seq 1 900); do
  kill -0 $PID 2>/dev/null || break
  sleep 2
done
kill $PID 2>/dev/null || true
wait $PID 2>/dev/null || true
cat "$GENCP_TEST_OUT"
grep -q "^FAILED:" "$GENCP_TEST_OUT" && exit 1 || exit 0
