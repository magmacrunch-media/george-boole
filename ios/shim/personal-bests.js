/**
 * Personal bests, in place of the arcade scoreboard. Bundled by package.mjs
 * into www/shim/.
 *
 * ## Why the app does not keep the arcade board
 *
 * On magmacrunch.com the scoreboard is a cabinet: type your initials, compete
 * for the top ten against everyone who played. That works because ScoreClient
 * is connected to a shared backend. The App Store build removes the connection
 * -- it runs offline, and package.mjs drops score-server.js -- so the same board
 * would only ever show one person's games, on one phone, under initials they
 * typed to compete with themselves.
 *
 * So in the app a finished game records itself here, per mode, with nothing to
 * type; the scoreboard modal becomes a "your bests" card; and the competitive
 * half moves to Game Center, which already knows who the player is.
 *
 * ## How it attaches
 *
 * - Setting GameBoole.scoreboard to 'personal' is the whole switch. game.js
 *   checks it at game over and skips the initials prompt. The website never
 *   sets it.
 * - The result arrives on boole:game-over, the same seam haptics and
 *   achievements use. Nothing here reaches into the game's state.
 * - The modal's contents are rebuilt once, keeping the #closeScoreboard button
 *   and the modal's own id, so main.js's open and close wiring still applies.
 *   main.js also calls updateScoreboard(), which returns early when
 *   #scoreColumns is absent, and updateCustomDropdownValue(), which does
 *   nothing when there are no dropdown options -- both verified, so neither
 *   needs patching.
 */
(function () {
  'use strict';

  var STORAGE_KEY = 'gb_bests';

  // The same eight modes, names and order as the difficulty selector.
  var MODES = [
    ['2', '2-BIT', 'crumb'],
    ['3', '3-BIT', 'tribit'],
    ['4', '4-BIT', 'nibble'],
    ['5', '5-BIT', 'pentad'],
    ['6', '6-BIT', 'hexad'],
    ['7', '7-BIT', 'ascii'],
    ['8', '8-BIT', 'byte'],
    ['endless', 'GAUNTLET', 'progressive'],
  ];

  window.GameBoole = window.GameBoole || {};
  window.GameBoole.scoreboard = 'personal';

  function load() {
    try {
      var parsed = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
      return parsed && typeof parsed === 'object' ? parsed : {};
    } catch (e) {
      return {};
    }
  }

  function save(bests) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(bests));
    } catch (e) {
      // Storage full or disabled. The game is still playable; only the record
      // of it is lost, which is not worth interrupting a game-over screen for.
    }
  }

  var bests = load();

  // ── game over ──────────────────────────────────────────────────────────────

  function gameOverLine() {
    var existing = document.getElementById('gameOverBest');
    if (existing) return existing;
    var content = document.querySelector('#gameOver .game-over-content');
    var button = document.getElementById('restartGame');
    if (!content || !button) return null;
    var line = document.createElement('p');
    line.id = 'gameOverBest';
    line.className = 'game-over-best';
    content.insertBefore(line, button);
    return line;
  }

  document.addEventListener('boole:game-over', function (e) {
    var d = e.detail || {};
    var key = String(d.difficulty);
    var score = Number(d.score) || 0;

    var entry = bests[key] || { best: 0, bestTile: 0, games: 0 };
    var previous = entry.best || 0;
    // A zero-point game is not a best, even if it is the first game played.
    var isNewBest = score > previous;

    entry.games = (entry.games || 0) + 1;
    entry.lastPlayed = Date.now();
    if (isNewBest) entry.best = score;
    if ((Number(d.highest) || 0) > (entry.bestTile || 0)) entry.bestTile = Number(d.highest);
    bests[key] = entry;
    save(bests);

    var line = gameOverLine();
    if (line) {
      if (isNewBest) {
        line.textContent = previous > 0 ? 'NEW BEST! (was ' + previous + ')' : 'NEW BEST!';
        line.classList.add('is-new');
      } else {
        line.textContent = 'your best: ' + previous;
        line.classList.remove('is-new');
      }
    }

    // The arcade build plays this when a score makes the board. Here, the
    // board is your own history, so a new best is the equivalent moment.
    if (isNewBest && typeof AdAudio !== 'undefined' && AdAudio.playSfx) {
      AdAudio.playSfx('highScore');
    }
  });

  // ── the "your bests" card ──────────────────────────────────────────────────

  function lastPlayed() {
    try {
      return localStorage.getItem('lastPlayedDifficulty');
    } catch (e) {
      return null;
    }
  }

  function render(list) {
    var current = lastPlayed();
    while (list.firstChild) list.removeChild(list.firstChild);

    MODES.forEach(function (m) {
      var entry = bests[m[0]];
      var row = document.createElement('div');
      row.className = 'best-row' + (m[0] === current ? ' is-last-played' : '');

      var mode = document.createElement('span');
      mode.className = 'best-mode';
      mode.textContent = m[1];

      var name = document.createElement('span');
      name.className = 'best-name';
      name.textContent = m[2];

      var value = document.createElement('span');
      value.className = 'best-score';
      value.textContent = entry && entry.best > 0 ? String(entry.best) : '—';

      row.appendChild(mode);
      row.appendChild(name);
      row.appendChild(value);
      list.appendChild(row);
    });
  }

  function gameCenter() {
    return (window.GameBoole && window.GameBoole.gameCenter) || null;
  }

  function build() {
    var modal = document.getElementById('scoreboardModal');
    var content = modal && modal.querySelector('.scoreboard-content');
    var close = document.getElementById('closeScoreboard');
    if (!modal || !content || !close) {
      // Say so rather than leave the arcade board half-replaced: this shim
      // exists because a silent miss here ships the wrong scoreboard.
      console.error('personal-bests: scoreboard markup not found; leaving it unchanged');
      return;
    }

    var title = document.createElement('h3');
    title.textContent = 'your bests';

    var list = document.createElement('div');
    list.className = 'bests-list';
    list.id = 'bestsList';

    var note = document.createElement('p');
    note.className = 'bests-note';
    note.textContent = 'saved on this device';

    var boards = document.createElement('button');
    boards.id = 'gameCenterBoards';
    boards.className = 'game-center-button';
    boards.textContent = 'game center leaderboards';
    boards.hidden = true;
    boards.addEventListener('click', function () {
      var gc = gameCenter();
      if (gc) gc.show(lastPlayed());
    });

    while (content.firstChild) content.removeChild(content.firstChild);
    content.appendChild(title);
    content.appendChild(list);
    content.appendChild(note);
    content.appendChild(boards);
    content.appendChild(close);

    function refresh() {
      render(list);
      var gc = gameCenter();
      boards.hidden = !(gc && gc.available && gc.authenticated);
    }

    // Re-render every time the modal opens, whichever button opened it.
    new MutationObserver(function () {
      if (modal.classList.contains('active')) refresh();
    }).observe(modal, { attributes: true, attributeFilter: ['class'] });
    refresh();

    var quick = document.querySelector('#quickHighScores span');
    if (quick) quick.textContent = 'YOUR BESTS';
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', build);
  } else {
    build();
  }

  window.GameBoole.bests = {
    get all() {
      return JSON.parse(JSON.stringify(bests));
    },
    // For putting a test device back to a known state.
    reset: function () {
      bests = {};
      try {
        localStorage.removeItem(STORAGE_KEY);
      } catch (e) {}
    },
  };
})();
