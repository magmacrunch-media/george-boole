/**
 * Taptic Engine feedback. Bundled by package.mjs into www/shim/.
 *
 * The site has no haptics and no reason to gain a Capacitor dependency, so
 * this lives here rather than in web/ -- the same rule as gamekit-scores.js
 * and css/ios.css.
 *
 * ## It listens; it does not patch
 *
 * web/js/game.js announces five moments on the document -- boole:move,
 * boole:overflow, boole:height-bonus, boole:promotion, boole:game-over -- with
 * plain CustomEvents named for the game rather than for any platform. So
 * nothing here has to reach into the game, re-derive when a bonus was earned,
 * or survive the game's internals being rearranged. In a browser the events
 * are dispatched into a document with no listeners and cost one allocation.
 *
 * Reading them rather than patching AdAudio.playSfx also matters practically:
 * the audio bundle installs its exports as non-writable accessors, and more
 * importantly checkGameOver() replays moveLeft() four times to decide whether
 * the board is dead. The game's own _silent guard suppresses the events during
 * that probe. A wrapper around playSfx would have no such guard and would buzz
 * the phone four times every time the board filled up.
 *
 * ## 'HEAVY' and 'SUCCESS' are not typos for something the plugin matches
 *
 * @capacitor/haptics only string-matches MEDIUM and LIGHT for style, and
 * WARNING and ERROR for type; anything else falls through to the initial
 * values, which are .heavy and .success respectively
 * (node_modules/@capacitor/haptics/ios/Sources/HapticsPlugin/HapticsPlugin.swift).
 * So these two are the documented API and they do the right thing, just by
 * default rather than by comparison. Passing '' would behave identically,
 * which is exactly why they are spelled out here.
 *
 * ## The plugin may not be there
 *
 * Capacitor injects window.Capacitor.Plugins.* from the native side at
 * document start. In a browser -- including any static server pointed at
 * ios/www -- there is no injection, plugin() is null, and every call here is
 * a no-op. That is the same degrade-quietly contract gamekit-scores.js uses.
 */
(function () {
  'use strict';

  var STORAGE_KEY = 'gb_haptics';

  function plugin() {
    var cap = typeof window !== 'undefined' ? window.Capacitor : null;
    return (cap && cap.Plugins && cap.Plugins.Haptics) || null;
  }

  var haptics = plugin();
  if (!haptics) return;

  var enabled = true;
  try {
    enabled = localStorage.getItem(STORAGE_KEY) !== 'off';
  } catch (e) {
    // Private mode, or storage disabled. Default to on.
  }

  function impact(style) {
    if (!enabled) return;
    try {
      var p = haptics.impact({ style: style });
      if (p && p.catch) p.catch(function () {});
    } catch (e) {
      // A device with no Taptic Engine rejects these. Never the player's
      // problem, and never worth interrupting a move for.
    }
  }

  function notify(type) {
    if (!enabled) return;
    try {
      var p = haptics.notification({ type: type });
      if (p && p.catch) p.catch(function () {});
    } catch (e) {}
  }

  function on(name, fn) {
    document.addEventListener('boole:' + name, fn);
  }

  // Fires on most swipes, so it has to stay under the threshold where it
  // becomes something you notice. LIGHT for a slide, MEDIUM for a merge --
  // enough to tell the two apart by feel without looking.
  on('move', function (e) {
    impact(e.detail && e.detail.merged ? 'MEDIUM' : 'LIGHT');
  });

  // A new personal best. Rare by construction: the height bonus refuses to
  // celebrate any value the spawn table can hand out for free.
  on('height-bonus', function () {
    impact('HEAVY');
  });

  // NOT(max) clears the tile and pays three times the ceiling -- the biggest
  // single payout in the game, and the only way to overflow. A *notification*
  // pattern is multi-tap and categorically unlike any impact, which is the
  // point: this is the one moment that should not feel like a merge.
  on('overflow', function () {
    notify('SUCCESS');
  });

  // A Gauntlet promotion arrives ~800ms after the overflow that earned it, so
  // a second SUCCESS would be indistinguishable from the first. Three heavy
  // taps read as a fanfare instead of a repeat.
  on('promotion', function () {
    impact('HEAVY');
    setTimeout(function () { impact('HEAVY'); }, 90);
    setTimeout(function () { impact('HEAVY'); }, 180);
  });

  on('game-over', function (e) {
    // A win and a loss should not feel the same. wasVictory means the player
    // reached the ceiling rather than ran out of board.
    if (e.detail && e.detail.victory) notify('SUCCESS');
    else notify('ERROR');
  });

  // Nothing on boole:move's spawn counterpart and nothing per tile: a tile
  // appears after every single move, so feedback there is not information.

  window.GameBoole = window.GameBoole || {};
  window.GameBoole.haptics = {
    get available() {
      return true;
    },
    get enabled() {
      return enabled;
    },
    set: function (on) {
      enabled = !!on;
      try {
        localStorage.setItem(STORAGE_KEY, enabled ? 'on' : 'off');
      } catch (e) {}
      return enabled;
    },
  };
})();
