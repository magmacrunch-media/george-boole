# george-boole

A Wii homebrew game built on [magnolia](../magnolia).

## Layout

```
george-boole/
├── Makefile
├── meta.xml          Homebrew Channel entry
├── source/           game code
├── sprites/          PNGs, embedded into the binary by bin2s
├── audio/            raw PCM, embedded into the binary by bin2s
└── ../magnolia/      the engine, checked out beside this directory
```

## Building

```bash
export DEVKITPRO=/opt/devkitpro
export DEVKITPPC=/opt/devkitpro/devkitPPC
export PATH=$DEVKITPPC/bin:$PATH

make            # build build/george-boole.dol
make deploy     # stage sdcard/apps/george-boole/
make dolphin    # push that to the folder Dolphin reads as its SD card
```

`make dolphin` clears the app directory rather than merging, so **saved scores
and settings are deleted on every deploy**. That is right for a dev loop and
wrong to mistake for the game failing to save.

## Onto a real Wii

Two routes, and they do different jobs.

```bash
make card SD=/mnt/e             # install onto an SD card (permanent)
make wii  WIILOAD=tcp:<wii-ip>  # send this build to a running console (temporary)
```

**`make card`** is the one that installs the game. It needs the card's mount
point because a removable drive's letter moves — a card showing as `E:` in
Windows is `/mnt/e` in WSL. Eject it, put it in the console, and the game appears
in the Homebrew Channel under the name in `meta.xml`.

Unlike `make dolphin`, this **merges**: only `boot.dol` and `meta.xml` are
overwritten, so `scores.json` and `settings.json` on the card survive an update.
Wiping is right for a dev loop against an emulator and wrong when it is somebody's
high scores.

**`make wii`** sends the `.dol` over the network and runs it immediately, without
installing anything. It is the fast loop for real hardware — no card, no ejecting,
a couple of seconds. Open the Homebrew Channel, press Home for the netloader
screen, and use the IP address it displays:

```bash
export WIILOAD=tcp:192.168.1.50   # once per shell, then just `make wii`
```

The console has to be sitting on that netloader screen when you send. Nothing is
written to the card, so the game is gone when you quit it.

## Assets

Sprites and audio are linked into the binary, not read from the card: assets on a
card can go missing, go stale, or disagree with the code.

Audio is raw signed 16-bit little-endian PCM:

```bash
ffmpeg -i in.ogg -f s16le -acodec pcm_s16le -ar 48000 -ac 2 audio/track.pcm
```

Budget the memory before committing to a format. Clips are held decoded in RAM:

| Format | Rate | One minute |
|---|---|---|
| 48kHz stereo | ~192 KB/s | ~11.5 MB |
| 24kHz mono | ~48 KB/s | ~2.9 MB |

Against the Wii's 24MB, a long track at 48kHz stereo does not fit. Downsample the
music loop with `audio_play_music_fmt()`; keep short effects at 48kHz stereo.

## Testing without a controller

Driving the D-pad into an emulator window is unreliable: Windows ignores
`SetForegroundWindow` from a background process, and Dolphin reads the keyboard
through DirectInput, which polls device state rather than window messages. A
mouse click gets through; arrow keys do not. So the game drives itself instead:

```c
#define AUTOSTART_GAMEPLAY      1   /* boot straight into a run */
#define DEBUG_AUTOPLAY_FRAMES   12  /* one move every 12 frames */
```

That plays continuously, restarting on game over, and exercises the board, the
renderer, the scoring and the Gauntlet promotion path with no input at all. It
doubles as a soak test.


Reaching gameplay by hand needs button presses into an emulator window. Instead:

```c
#define AUTOSTART_GAMEPLAY      1
#define DEBUG_HEARTBEAT_FRAMES  120
```

Then run the `.dol` and read the log. For `printf` to reach Dolphin's log, its
`Logger.ini` needs `OSREPORT = True` and `WriteToFile = True` -- both default to
False, which makes a working trace look like a dead one.

Dolphin also reuses an already-running instance, so kill it between runs or you
will read the previous run's log and debug a binary that is not running.
