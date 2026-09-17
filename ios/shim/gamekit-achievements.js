/**
 * Game Center achievements. Bundled by package.mjs into www/shim/.
 *
 * The other half of gamekit-scores.js, and the same contract: this file
 * defines what the native side must provide and does nothing at all when it
 * is missing -- which is always, today, and always in a browser.
 *
 * It needs one method beyond the three gamekit-scores.js documents:
 *
 *     reportAchievement({ achievementId, percent })  -> void
 *
 * ## Why these eight
 *
 * Overflow is the only way to clear the ceiling: NOT(max) makes 0, no tile can
 * hold 0, so the tile goes and pays three times the maximum. It is the hardest
 * thing the game asks for and it gets harder with every bit of width, so "you
 * overflowed at n bits" is the one axis worth an achievement per step.
 *
 * Keyed on bit *width* rather than on mode, deliberately: the same achievement
 * is reachable either by picking that difficulty or by climbing to it in
 * Gauntlet. `bitMode` is what makes the overflow hard, not which menu entry
 * you came in through.
 *
 * The Gauntlet clear is defined as overflowing *at 8-bit while in Gauntlet*,
 * because bitMode stops there -- every promotion is guarded by
 * `if (this.bitMode < 8)`, so there is no ninth promotion to observe and
 * "promoted to 8-bit" would be the easier thing wearing the name of the
 * harder one.
 *
 * ## Discoveries
 *
 * web/js/codex.js announces boole:discovery when a player first does the thing
 * that shows a gate's defining property -- XOR a number with itself, AND two
 * numbers with nothing in common, and so on. Each is also an achievement here,
 * `learn.<id>`, so the codex and Game Center agree about what was found. The
 * ids are codex.js's DISCOVERIES ids and must not be renamed there once these
 * exist in App Store Connect.
 *
 * ## Points
 *
 * App Store Connect allows at most 100 points per achievement and 1000 across
 * the app. An earlier version of this comment planned the Gauntlet clear at
 * 300, which the form would never have accepted. Fifteen achievements now:
 *
 *   overflow.<n>bit  x7   50 each   350
 *   gauntlet.clear   x1  100        100
 *   learn.<id>       x7   50 each   350
 *                                   ---
 *                                   800, leaving 200 for later
 *
 * Nothing is created in App Store Connect yet, so this is free to change until
 * it is. The ids are permanent once created and a deleted one cannot be reused.
 *
 * ## Reporting once
 *
 * GameKit tolerates re-reporting an achievement at 100%, but it can re-show
 * the banner, and a banner for something earned three weeks ago reads as a
 * bug. The set of ids already sent is kept locally, per device, which is the
 * same place this game keeps its scores when unconnected.
 */
(function () {
  'use strict';

  var PREFIX = 'com.magmacrunch.georgeboole.';
  var STORAGE_KEY = 'gb_achievements';

  var GAUNTLET_CLEAR = PREFIX + 'gauntlet.clear';

  function overflowId(bits) {
    // 2..8 only. Anything else is a mode this file has not been told about,
    // and inventing an id for it would create a leaderboard-shaped mistake
    // that cannot be renamed later.
    if (typeof bits !== 'number' || bits < 2 || bits > 8) return null;
    return PREFIX + 'overflow.' + bits + 'bit';
  }

  function plugin() {
    var cap = typeof window !== 'undefined' ? window.Capacitor : null;
    return (cap && cap.Plugins && cap.Plugins.GameCenter) || null;
  }

  function loadReported() {
    try {
      var raw = localStorage.getItem(STORAGE_KEY);
      var parsed = raw ? JSON.parse(raw) : [];
      return Array.isArray(parsed) ? parsed : [];
    } catch (e) {
      return [];
    }
  }

  var reported = loadReported();

  function remember(id) {
    if (reported.indexOf(id) !== -1) return;
    reported.push(id);
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(reported));
    } catch (e) {
      // Storage full or disabled. The worst case is a repeated banner, which
      // is not worth failing an achievement over.
    }
  }

  function award(id) {
    if (!id || reported.indexOf(id) !== -1) return;

    var p = plugin();
    if (!p || typeof p.reportAchievement !== 'function') {
      // No native half yet. Do NOT remember it: the player has earned this,
      // and the day the plugin lands they should get it on their next
      // overflow rather than having it silently written off now.
      return;
    }

    // Optimistic: recorded before the round trip, so a slow or failed
    // submission cannot produce two banners. GameKit queues and retries
    // submissions itself once signed in again.
    remember(id);
    Promise.resolve()
      .then(function () {
        return p.reportAchievement({ achievementId: id, percent: 100 });
      })
      .catch(function () {
        // A failed report is not the player's problem and not worth a dialog.
      });
  }

  document.addEventListener('boole:overflow', function (e) {
    var d = e.detail || {};
    award(overflowId(d.bits));
    if (d.bits === 8 && d.difficulty === 'endless') award(GAUNTLET_CLEAR);
  });

  // The codex's discoveries. Only ids codex.js defines are reported: an id
  // Game Center has never heard of fails the report, and a typo'd achievement
  // cannot be tidied up once created.
  var LEARN = ['self_inverse', 'nothing_in_common', 'all_lit', 'opposites',
    'wraparound', 'chain_reaction', 'full_set'];

  document.addEventListener('boole:discovery', function (e) {
    var id = e.detail && e.detail.id;
    if (LEARN.indexOf(id) !== -1) award(PREFIX + 'learn.' + id);
  });

  window.GameBoole = window.GameBoole || {};
  window.GameBoole.achievements = {
    ids: [2, 3, 4, 5, 6, 7, 8].map(overflowId).concat([GAUNTLET_CLEAR])
      .concat(LEARN.map(function (id) { return PREFIX + 'learn.' + id; })),
    get reported() {
      return reported.slice();
    },
    // Exists so a device can be put back to a known state while testing
    // against the Game Center sandbox, which has its own reset.
    reset: function () {
      reported = [];
      try {
        localStorage.removeItem(STORAGE_KEY);
      } catch (e) {}
    },
  };
})();
