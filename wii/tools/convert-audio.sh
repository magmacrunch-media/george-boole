#!/bin/sh
# Converts the web game's audio into the raw PCM magnolia plays, and into a
# memory budget a Wii actually has.
#
#   tools/convert-audio.sh [path-to-web-game-audio-dir]
#
# Clips are held decoded in main RAM, so the format is a memory decision before
# it is a fidelity one:
#
#   48kHz stereo  ~192 KB/s     24kHz mono  ~48 KB/s
#
# The source loop is 3m50s. At 48kHz stereo that decodes to about 43MB against a
# console with 24MB -- it cannot be loaded at all, at any quality. So the music
# is trimmed to a loop and taken down to 24kHz mono, which costs about 2.8MB.
# Effects stay 48kHz stereo: they are short, and they are what the player hears
# most sharply.
#
# LOOP_SECONDS is the honest knob here. The source is a composed piece and this
# takes the opening minute of it, crossfading the seam so the repeat does not
# click. If a different passage loops better, change the offset and length --
# that is a musical decision, not a technical one.
set -e

SRC=${1:-"$HOME/Documents/website/arcade/george-boole/audio"}
OUT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)/audio

LOOP_START=${LOOP_START:-0}
LOOP_SECONDS=${LOOP_SECONDS:-60}
CROSSFADE=${CROSSFADE:-1.5}
MUSIC_RATE=${MUSIC_RATE:-24000}

if [ ! -d "$SRC" ]; then
    echo "error: no audio directory at $SRC" >&2
    echo "  pass the web game's audio/ directory as the first argument." >&2
    exit 1
fi

command -v ffmpeg >/dev/null 2>&1 || { echo "error: ffmpeg not found" >&2; exit 1; }

mkdir -p "$OUT"

echo "music: ${LOOP_SECONDS}s from ${LOOP_START}s, ${MUSIC_RATE}Hz mono"
# The tail is crossfaded into a second copy of the opening, so the point where
# the buffer wraps lands mid-blend instead of on a hard edit.
ffmpeg -v error -y \
    -ss "$LOOP_START" -t "$LOOP_SECONDS" -i "$SRC/game-loop.ogg" \
    -ss "$LOOP_START" -t "$CROSSFADE"    -i "$SRC/game-loop.ogg" \
    -filter_complex "[0:a][1:a]acrossfade=d=$CROSSFADE:c1=tri:c2=tri[a]" \
    -map "[a]" -f s16le -acodec pcm_s16le -ar "$MUSIC_RATE" -ac 1 \
    "$OUT/music.pcm"

for name in move spawn merge gameover victory highscore; do
    [ -f "$SRC/sfx/$name.ogg" ] || { echo "  skipping $name (not found)"; continue; }
    ffmpeg -v error -y -i "$SRC/sfx/$name.ogg" \
        -f s16le -acodec pcm_s16le -ar 48000 -ac 2 "$OUT/$name.pcm"
done

echo ""
echo "Resident audio:"
total=0
for f in "$OUT"/*.pcm; do
    [ -f "$f" ] || continue
    size=$(wc -c < "$f")
    total=$((total + size))
    printf "  %-16s %6s KB\n" "$(basename "$f")" "$((size / 1024))"
done
printf "  %-16s %6s KB\n" "TOTAL" "$((total / 1024))"
echo ""
echo "All of this is linked into the .dol and resident for the whole session."
echo "The Wii has 24MB. Keep an eye on the total."
