# George Boole Has Entered The Chat

Logic-gate puzzle game. One repo, every version of the game.

| Version | Folder | Engine | Where it runs |
|---------|--------|--------|---------------|
| Browser | [`web/`](web/) | [adenosine](https://github.com/magmacrunchmedia/adenosine) | [magmacrunch.com/arcade/george-boole](https://magmacrunch.com/arcade/george-boole/) |
| Wii | [`wii/`](wii/) | [magnolia](https://github.com/magmacrunchmedia/magnolia) | Homebrew Channel |
| Terminal | [`tui/`](tui/) | [texastoast](https://pypi.org/project/texastoast/) | any terminal |

## Layout

- `web/` — the browser version. **This folder is the source of truth**; the
  copy served from the website repo at `arcade/george-boole/` is generated
  from it via `make sync-george-boole` in that repo. Edit here, sync there.
- `wii/` — the Wii port. Builds with devkitPPC and expects the magnolia engine
  checked out beside this repo (`../../magnolia` from inside `wii/`). See
  [`wii/README.md`](wii/README.md).
- `tui/` — the terminal version. Runs on the
  [texastoast](https://pypi.org/project/texastoast/) engine's terminal backend.
  Install with `pipx install magmacrunch-george-boole` and launch with
  `george-boole`. Also available as part of the
  [magmacrunch](https://pypi.org/project/magmacrunch/) arcade.
  See [`tui/README.md`](tui/README.md).

## Working on the game

A rules or balance change usually lands in all three versions: the browser
sources under `web/js/` are the reference implementation the Wii port was
checked against, and the TUI's Python scenes mirror the same logic. Change
`web/` first, then carry the change into `wii/source/` and `tui/`.

This repo was formed from `george-boole-wii` (whose history it keeps) plus
the browser version imported from the website repo.

## License

[PolyForm Noncommercial License 1.0.0](LICENSE) — read it, learn from it, build
on it, play with it. Any noncommercial purpose is permitted; commercial use is
reserved. The game's name, art, audio and visual design are reserved outright
and are not covered by that licence: see [NOTICE](NOTICE) for the exact
boundary and the third-party components.
