/**
 * Game Center seam. Bundled by package.mjs into www/shim/, loaded after the
 * ScoreClient bootstrap and before the game's own scripts.
 *
 * The app has no leaderboard backend of its own: score-server.js is dropped
 * from the bundle, so there is no shared arcade board. personal-bests.js keeps
 * each player's own record on the device, and Game Center is where scores are
 * compared with anyone else's -- it has a full-screen UI of its own, which is
 * what showLeaderboard is for.
 *
 * ## Every finished game is submitted
 *
 * This file used to wrap scoreClient.save. That call happens only from
 * submitInitials(), which runs only when a score makes the local top ten AND
 * the player types initials -- so a leaderboard fed that way would have missed
 * nearly every game. It now submits on boole:game-over, which game.js
 * announces for every game that ends, whatever the score. Game Center keeps
 * each player's best per leaderboard itself, so submitting a lower score than
 * one already recorded is harmless.
 *
 * ## What this file does NOT do
 *
 * It does not implement Game Center. It defines the interface the native side
 * has to provide and degrades to doing nothing when that side is missing --
 * which is always in a browser, and in the app until GameCenterPlugin is
 * registered (see ios/AGENTS.md on why that registration is explicit).
 *
 * ## The contract
 *
 * A Capacitor plugin registered as `GameCenter`, with:
 *
 *     signIn()                                  -> { authenticated: boolean }
 *     submitScore({ leaderboardId, score })     -> void
 *     showLeaderboard({ leaderboardId })        -> void
 *
 * All three may reject, and nothing here treats a rejection as fatal: a
 * refused Game Center sign-in must not cost the player anything.
 * personal-bests.js records the game from the same event regardless.
 *
 * ## Why the ids come from the terminal version
 *
 * tui/boole/modes.py defines the eight modes and says in its own docstring
 * that `key` IS the leaderboard id and must stay stable and distinct. Game
 * Center ids are permanent once a leaderboard exists, so taking them from the
 * place that already promised not to change them is the whole point. The web
 * difficulty values ('2'..'8', 'endless') are the ones this game speaks, so
 * this is the translation between the two and the only place it lives.
 */
(function () {
  'use strict';

  var PREFIX = 'com.magmacrunch.georgeboole.';

  /**
   * Web difficulty -> Game Center leaderboard id.
   *
   * '11' (CLASSIC) is deliberately absent. It is not selectable -- no
   * data-difficulty="11" exists in the page -- and survives only as the label
   * migrateOldScores() stamps on scores saved before the difficulty field
   * existed. A leaderboard nobody can play is a leaderboard nobody can ever
   * top, so those scores stay local.
   */
  var LEADERBOARDS = {
    '2': PREFIX + 'crumb',
    '3': PREFIX + 'trit',
    '4': PREFIX + 'nibble',
    '5': PREFIX + 'pentad',
    '6': PREFIX + 'hexad',
    '7': PREFIX + 'ascii',
    '8': PREFIX + 'byte',
    endless: PREFIX + 'gauntlet',
  };

  function plugin() {
    var cap = typeof window !== 'undefined' ? window.Capacitor : null;
    return (cap && cap.Plugins && cap.Plugins.GameCenter) || null;
  }

  var available = !!plugin();
  var authenticated = false;

  if (available) {
    // Fire and forget: the game is playable signed out, and blocking the
    // first frame on a network round trip to Apple would be a poor trade.
    plugin()
      .signIn()
      .then(function (r) {
        authenticated = !!(r && r.authenticated);
      })
      .catch(function () {
        authenticated = false;
      });
  }

  document.addEventListener('boole:game-over', function (e) {
    var d = e.detail || {};
    var id = LEADERBOARDS[String(d.difficulty)];
    var score = Number(d.score) || 0;
    // A zero is not a leaderboard entry anyone wants to see.
    if (!available || !authenticated || !id || score <= 0) return;

    Promise.resolve()
      .then(function () {
        return plugin().submitScore({ leaderboardId: id, score: score });
      })
      .catch(function () {
        // A failed submission is not the player's problem. Game Center
        // queues and retries submissions itself once signed in again.
      });
  });

  window.GameBoole = window.GameBoole || {};
  window.GameBoole.leaderboards = LEADERBOARDS;
  window.GameBoole.gameCenter = {
    get available() {
      return available;
    },
    get authenticated() {
      return authenticated;
    },
    show: function (difficulty) {
      var p = plugin();
      if (!p) return Promise.resolve(false);
      return p
        .showLeaderboard({ leaderboardId: LEADERBOARDS[difficulty] || null })
        .then(function () {
          return true;
        })
        .catch(function () {
          return false;
        });
    },
  };
})();
