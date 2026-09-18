/* Staging for App Store screenshots. Injected into a built App.app's
   public/index.html on the Mac; never committed, never in the bundle that
   ships. It only drives the real UI -- taps the real buttons, plays real
   moves -- so what is captured is the app, arranged rather than faked. */
(function () {
  var W = function (ms) { return new Promise(function (r) { setTimeout(r, ms); }); };
  var $ = function (id) { return document.getElementById(id); };
  var E = function () { return [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]; };
  var press = function (k) {
    document.dispatchEvent(new KeyboardEvent('keydown', { key: k, bubbles: true }));
  };

  // A history worth showing on the bests card. personal-bests.js reads this
  // once at load, so it is seeded and then the page is reloaded.
  if (localStorage.getItem('gb_shot') !== '1') {
    var day = 86400000;
    localStorage.setItem('gb_bests', JSON.stringify({
      '4': { best: 1284, bestTile: 15, games: 12, lastPlayed: Date.now() - 2 * day },
      '6': { best: 3960, bestTile: 63, games: 7, lastPlayed: Date.now() - day },
      '8': { best: 8215, bestTile: 255, games: 3, lastPlayed: Date.now() - 3 * day },
      'endless': { best: 12480, bestTile: 255, games: 5, lastPlayed: Date.now() - 1800000 }
    }));
    localStorage.setItem('lastPlayedDifficulty', '6');
    localStorage.removeItem('gb_codex');
    localStorage.setItem('gb_shot', '1');
    location.reload();
    return;
  }

  function stage(rows) {
    // main.js declares `let currentGame` at the top level of a classic
    // script, which is a global lexical binding: in scope by name, and NOT a
    // property of window. Reaching for window.currentGame silently staged
    // nothing and produced five screenshots of an empty board.
    var g = typeof currentGame !== 'undefined' ? currentGame : null;
    if (!g) return;
    var b = E();
    for (var i = 0; i < rows.length; i++) b[rows[i][0]] = rows[i][1];
    g.board = b;
    g.previousBoard = E();
    g.render();
  }

  async function run() {
    await W(2200);

    // 1 — the title screen.
    await W(7000);

    // 2 — the rules, drawn as tiles.
    $('startButton').click();
    await W(8000);

    // The three gates, unlocked by playing them: XOR a number with itself,
    // OR into all ones, AND with no bits in common. Each is a discovery too.
    // Done here, before either shot that would otherwise carry its toast
    // across the top of the frame. Six of them queue here, three gates and
    // three discoveries, at 2.4s each.
    $('loreContinue').click();
    await W(500);
    document.querySelector('.difficulty-btn[data-difficulty="4"]').click();
    await W(1200);
    stage([[1, [5, -1, 5, 0]]]);
    press('ArrowLeft');
    await W(600);
    stage([[1, [12, -2, 3, 0]]]);
    press('ArrowLeft');
    await W(600);
    stage([[1, [9, -3, 6, 0]]]);
    press('ArrowLeft');
    await W(600);
    // Two gates in one swipe: the chain-reaction discovery, which the board
    // staged for shot 3 would otherwise announce over the top of it.
    stage([[1, [5, -1, 5, 0]], [2, [12, -2, 3, 0]]]);
    press('ArrowLeft');
    await W(22000);

    // 3 - a board mid-game, with the point labels and the math card. The card
    // clears itself after 1.3s, so the move is replayed until this shot is
    // safely past.
    var replay = setInterval(function () {
      stage([[1, [6, -1, 3, 0]], [2, [0, 5, -3, 12]], [3, [2, 0, 0, 9]]]);
      press('ArrowLeft');
    }, 1200);
    await W(7500);
    clearInterval(replay);

    // 4 - the gate codex: three of the four gates, and the discoveries they
    // came with.
    BooleCodex.open();
    await W(9000);

    // 5 — your bests. The shim re-renders whenever the modal opens.
    BooleCodex.close();
    await W(300);
    $('scoreboardModal').classList.add('active');
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', run);
  } else {
    run();
  }
})();
