/**
 * Game Center seam. Bundled by package.mjs into www/shim/, loaded after the
 * ScoreClient bootstrap and before the game's own scripts.
 *
 * The app has no leaderboard backend. score-server.js is dropped from the
 * bundle, so `scoreClient` is constructed unconnected and falls back to
 * localStorage, which works offline and is per-device. Game Center replaces
 * that -- but only the submitting half. Reading stays local, because Game
 * Center has no "give me the scores" call worth rendering into this game's own
 * scoreboard; it has a full-screen UI of its own, which is what showLeaderboard
 * is for.
 *
 * ## What this file does NOT do
 *
 * It does not implement Game Center. It defines the interface the native side
 * has to provide and degrades to exactly the current behaviour when that side
 * is missing -- which is always, today, and always in a browser. Nothing here
 * changes what the game does until a plugin answers.
 *
 * ## The contract
 *
 * A Capacitor plugin registered as `GameCenter`, with:
 *
 *     signIn()                                  -> { authenticated: boolean }
 *     submitScore({ leaderboardId, score })     -> void
 *     showLeaderboard({ leaderboardId })        -> void
 *
 * All three may reject; nothing here treats a rejection as fatal, because a
 * refused Game Center sign-in must not cost the player their score. That is
 * why the localStorage write happens first and unconditionally.
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

  // `scoreClient` is declared `const` in an inline <script>, so it is in the
  // global lexical scope but NOT a property of window -- patching the object
  // it points at is the only way to reach it from another file.
  if (typeof scoreClient === 'undefined' || !scoreClient) return;

  var localSave = scoreClient.save.bind(scoreClient);

  scoreClient.save = function (game, name, score, extra) {
    // Local first, and awaited, so the player's own scoreboard is correct
    // whatever Game Center does. This is also what returns the rank.
    var result = localSave(game, name, score, extra);

    var id = extra && LEADERBOARDS[extra.difficulty];
    if (available && authenticated && id) {
      Promise.resolve()
        .then(function () {
          return plugin().submitScore({ leaderboardId: id, score: score });
        })
        .catch(function () {
          // A failed submission is not the player's problem. Game Center
          // queues and retries submissions itself once signed in again.
        });
    }
    return result;
  };

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
