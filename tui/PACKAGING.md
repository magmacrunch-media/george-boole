# Publishing the terminal games

Notes toward `pip install magmacrunch` — a terminal arcade. Nothing here is
built yet; this records the decisions so they are not re-litigated, and the
blockers so they are not tripped over.

## The shape

```
george-boole/tui/            → magmacrunch-george-boole
texas-holdem-lava-dome/tui/  → magmacrunch-thld            (not written yet)
moonlight-drift/tui/         → magmacrunch-moonlight-drift (not written yet)

magmacrunch  =  depends on all three  +  an arcade launcher
```

**The launcher is the reason to do it.** Without one, `pip install magmacrunch`
is an alias for three pip installs. With one, typing `magmacrunch` opens a
terminal arcade menu — `website/arcade/index.html`'s category cards in a shell.
`boole/scenes.py`'s `MenuScene` is the working proof of that screen; the
launcher is the same idea one level up.

There is a practical payoff beyond the novelty: the Pi arcade already runs
Python under systemd, so `pip install magmacrunch` on the Pi is a cleaner
deploy path than the current git-clone-and-rsync.

## Each game stays in its own repo

The games are **not** vendored into a `magmacrunch` repo. `AGENTS.md` in each
game repo says one repo per game, every platform version together, and a
gameplay change is not done until all versions have it. Moving `tui/` out would
put the terminal version away from the `web/` and `wii/` versions it has to
stay in lockstep with.

Copying it there instead is the `make sync-<game>` footgun already documented
in the website repo: *"Never edit the website repo's copy directly — it gets
overwritten."* One source, one repo, per game.

So each game repo publishes a small wheel built from its own `tui/` directory,
and `magmacrunch` lists them as dependencies. No duplication anywhere.

## Naming

PyPI has no scoping like the npm `@magmacrunch/adenosine-*` packages, so a name
**prefix** is the only way to claim a family. It is also the only protection
against a name being taken: `adenosine` and `magnolia` both already belong to
other people on PyPI.

| name | | status |
|---|---|---|
| `magmacrunch` | the arcade launcher — the command you type | available |
| `magmacrunch-george-boole` | game | available |
| `magmacrunch-thld` | game | — |
| `magmacrunch-moonlight-drift` | game | — |
| `texastoast` | the engine | **already ours**, 0.5.0 published |

Distribution names are prefixed; **import** packages are not. `boole` is what
you type in code and is not competing for anything.

Console scripts stay short and unprefixed — `george-boole`, not
`magmacrunch-george-boole` — since the whole point is a thing that is pleasant
to type.

## Licensing

Verified to work with no fudging:

- Engines stay **Apache-2.0** (`texastoast`).
- Games stay **PolyForm Noncommercial 1.0.0**. `PolyForm-Noncommercial-1.0.0`
  is a valid SPDX identifier and modern PyPI metadata accepts it — a built
  wheel carries `License-Expression: PolyForm-Noncommercial-1.0.0`. No
  `License :: Other/Proprietary` classifier fudge needed.
- `magmacrunch` depends on Noncommercial games, so it is Noncommercial too.
  A permissive dependency under a restrictive package is fine; the reverse
  would not be.

## Blockers, in order

1. **`texastoast` 0.6.0 is not published.** The `[tui]` extra exists only
   locally, so `magmacrunch-george-boole` cannot resolve
   `texastoast[tui]>=0.6.0` from a clean clone. `release.yml` publishes on a
   `v*` tag; nothing ships until `v0.6.0` is tagged.
2. **Only one of the three TUI games exists.** A one-cabinet arcade is a
   strange first release. THLD is the cheap next one — `state.js`, `dome.js`,
   `betting.js` and `config.js` are 662 lines with no browser dependency, and
   `website/arcade/scandinavian-stud/server.py` already contains a complete
   Python `Card`/`Deck`/`HandEvaluator`. Watch the point table: AdCards scores
   a royal flush at rank 9, the Sökö evaluator at 11, and `dome.js` reads
   `result.points` against a threshold.
3. Registering `magmacrunch` with a placeholder is cheap insurance whenever
   convenient — both names are free today, and the two engine names show what
   happens if they are not claimed.

## Not decided

- Whether the launcher discovers games by entry point (so a game published
  later is found without a `magmacrunch` release) or by a hardcoded list.
  Entry points are the better answer if games will be added independently.
- Whether `magmacrunch` pins exact game versions or floors them.
- Whether the SSH front door (`ssh play@magmacrunch.com`) reuses this launcher.
  It should, but it is a separate piece of work with its own security review.
