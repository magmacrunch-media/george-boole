#!/bin/bash
# Capture App Store screenshots from a simulator. Run on the Mac, after a
# build, with shots.js beside the output directory:
#
#   mkdir -p ~/gb-shots && cp ios/tools/screenshots/shots.js ~/gb-shots/
#   bash ios/tools/screenshots/capture.sh <device-udid> iphone-6.9
#
# App Store Connect wants one 6.9" iPhone size and, because the app is
# universal, one 13" iPad size. iPhone 17 Pro Max gives 1320x2868 and iPad
# Pro 13-inch 2064x2752, both of which it accepts; `xcrun simctl list devices`
# has the udids.
#
# The staging script is injected into a COPY of the built app, so nothing in
# the checkout or the real bundle is touched. It drives the real UI, so the
# screenshots are of the app as it is, arranged rather than faked.
#
# The offsets below are a timeline, not guesses to nudge one at a time: the
# staging script reloads once after seeding, and the codex announces seven
# unlocks at 2.4s each, which is why the board shot waits so long. A shot
# landing on a toast means the two drifted apart.
set -e
export DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer
export PATH=/opt/homebrew/bin:/usr/local/bin:$PATH
D="$1"
NAME="$2"
APP=~/Library/Developer/gb-derived/Build/Products/Debug-iphonesimulator/App.app
OUT=~/gb-shots/"$NAME"
mkdir -p "$OUT"

# Inject the staging script into a copy of the built app, so the checkout and
# the real bundle stay clean.
STAGED=/tmp/gb-staged.app
rm -rf "$STAGED"
cp -R "$APP" "$STAGED"
python3 - "$STAGED/public/index.html" <<'PY'
import sys, pathlib
p = pathlib.Path(sys.argv[1])
html = p.read_text()
assert '</body>' in html
html = html.replace('</body>', '<script src="shots.js"></script>\n</body>', 1)
p.write_text(html)
PY
cp ~/gb-shots/shots.js "$STAGED/public/shots.js"

xcrun simctl boot "$D" 2>/dev/null || true
xcrun simctl bootstatus "$D" >/dev/null 2>&1 || true
xcrun simctl uninstall "$D" com.magmacrunch.georgeboole 2>/dev/null || true
xcrun simctl install "$D" "$STAGED"
xcrun simctl status_bar "$D" override --time "9:41" --batteryState charged \
  --batteryLevel 100 --cellularMode active --cellularBars 4 --wifiMode active --wifiBars 3
xcrun simctl launch "$D" com.magmacrunch.georgeboole >/dev/null

shoot () { sleep "$1"; xcrun simctl io "$D" screenshot --type=png "$OUT/$2.png" >/dev/null 2>&1; echo "  $2"; }
# Offsets are cumulative; the staging script reloads once after seeding.
shoot 7  1-title
shoot 7  2-rules
shoot 31 3-board
shoot 9  4-codex
shoot 10 5-bests

xcrun simctl terminate "$D" com.magmacrunch.georgeboole 2>/dev/null || true
sips -g pixelWidth -g pixelHeight "$OUT"/1-title.png | tail -2
ls "$OUT"
