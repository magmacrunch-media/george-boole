# 🔊 Sound Effects System Guide
## George Boole has entered the chat

## File Structure

Create this folder structure in your project:

```
audio/
├── game-loop.ogg          # Your 4-minute background music
└── sfx/                   # NEW: Sound effects folder
    ├── merge.ogg          # Tile merge sound
    ├── spawn.ogg          # New tile appears
    ├── victory.ogg        # Reached target tile
    ├── gameover.ogg       # Lost the game
    ├── highscore.ogg      # NEW HIGH SCORE!
    └── move.ogg           # Valid move (optional)
```

---

## Sound Effect Triggers

### 🎯 **merge.ogg** - Tile Merge
**When it plays**: Two tiles combine into one
**How often**: Multiple times per game (core gameplay sound)
**Suggested characteristics**:
- Warm, resonant tone
- Duration: 100-300ms
- Pitch should increase with tile value (optional enhancement later)
- Think: Two wooden blocks clicking together, but synth

**Code location**: `game.js` line 146
```javascript
if (mergeOccurred) {
    SoundEffects.play('merge');
}
```

---

### ✨ **spawn.ogg** - New Tile Spawn
**When it plays**: After every valid move, a new 2 or 4 appears
**How often**: Very frequent (every successful move)
**Suggested characteristics**:
- Soft, gentle tone
- Duration: 50-200ms
- Subtle - shouldn't dominate
- Think: A small object being gently placed

**Code location**: `game.js` line 111
```javascript
SoundEffects.play('spawn');
```

---

### 🎉 **victory.ogg** - Victory!
**When it plays**: Player reaches target tile (4, 16, 256, 2048, etc.)
**How often**: Once per successful game
**Suggested characteristics**:
- Triumphant but not harsh
- Duration: 500-1500ms
- Warm, satisfying resolution
- Think: Achievement unlocked, but acoustic/organic

**Code location**: `game.js` line 188
```javascript
SoundEffects.play('victory');
```

---

### 💔 **gameover.ogg** - Game Over
**When it plays**: Board is full, no moves left (loss condition)
**How often**: Once per failed game
**Suggested characteristics**:
- Gentle descent, not harsh
- Duration: 500-1500ms
- Somber but not aggressive
- Think: Winding down, acceptance

**Code location**: `game.js` line 194
```javascript
SoundEffects.play('gameOver');
```

---

### 🏆 **highscore.ogg** - NEW HIGH SCORE!
**When it plays**: Your score makes it into the top 10 for that difficulty
**How often**: Occasionally (when you do well)
**Suggested characteristics**:
- Exciting but not jarring
- Duration: 500-1000ms
- Celebratory, rewarding feeling
- Think: Achievement unlocked, fanfare, but acoustic

**Code location**: `game.js` (in handleGameOver when rank detected)
```javascript
SoundEffects.play('highScore');
```

---

### 🎮 **move.ogg** - Valid Move (OPTIONAL)
**When it plays**: Tiles slide but don't merge
**How often**: Very frequent
**Suggested characteristics**:
- Very subtle sliding/swoosh
- Duration: 50-150ms
- Quiet - just tactile feedback
- **NOTE**: This might be too much if also using merge/spawn sounds

**Code location**: `game.js` line 148
```javascript
else {
    SoundEffects.play('move');
}
```

**Recommendation**: Start without this one. Test merge + spawn first. Add move sound later if game feels too quiet.

---

## Volume Settings

Default volumes are set in `main.js`:

```javascript
audio.volume = 0.3; // 30% volume for SFX
```

### Recommended Volume Balance:
- **Background Music**: 100% (adjust with music toggle)
- **merge.ogg**: 30-40% (most frequent, keep subtle)
- **spawn.ogg**: 20-30% (very frequent, even more subtle)
- **victory.ogg**: 50-60% (rare, can be louder)
- **gameover.ogg**: 40-50% (rare, noticeable but not jarring)
- **highscore.ogg**: 50-60% (rare, celebratory)
- **move.ogg**: 15-25% (if used, must be very quiet)

### To adjust individual sound volumes:
```javascript
// In main.js after SoundEffects.init()
SoundEffects.setVolume('merge', 0.35);
SoundEffects.setVolume('spawn', 0.25);
SoundEffects.setVolume('victory', 0.6);
SoundEffects.setVolume('gameOver', 0.45);
SoundEffects.setVolume('highScore', 0.55);
SoundEffects.setVolume('move', 0.2);
```

---

## Using Your Placeholder Sounds

### Quick Setup:
1. Take one of your analog synth sounds from your other game
2. Create 6 copies (or just use the same file 6 times as placeholder)
3. Name them: `merge.ogg`, `spawn.ogg`, `victory.ogg`, `gameover.ogg`, `highscore.ogg`, `move.ogg`
4. Put them in `audio/sfx/` folder
5. Load your game - sounds will play!

### File Format:
- ✅ **.ogg** (recommended - best browser support)
- ✅ **.wav** (works, but larger files)
- ✅ **.mp3** (works, but ogg is better for games)

If using .wav or .mp3, update the file extensions in `main.js`:
```javascript
merge: this.createSound('audio/sfx/merge.wav'),
```

---

## Sound Design Tips for Analog Synth

Since you're making these with your modular:

### For Merge Sound:
- **Oscillator**: Triangle or sine wave
- **Envelope**: Quick attack (5-20ms), short decay
- **Filter**: Low-pass, slightly resonant
- **Effect**: Subtle reverb for warmth
- **Pitch**: Start around C3-C4
- **Variation idea**: Make 3-5 variations for different tile values

### For Spawn Sound:
- **Oscillator**: Sine wave or soft FM
- **Envelope**: Very quick attack (2-10ms), quick decay
- **Filter**: High-pass to keep it light
- **Effect**: Tiny bit of delay or subtle verb
- **Pitch**: Higher than merge (C5-C6)

### For Victory Sound:
- **Oscillator**: Chord (major triad) or arpeggio
- **Envelope**: Medium attack (50-100ms), long release
- **Filter**: Open, bright
- **Effect**: Reverb, maybe light chorus
- **Pitch**: Upward movement, resolving to tonic

### For Game Over Sound:
- **Oscillator**: Sad chord or descending notes
- **Envelope**: Gentle attack, long release
- **Filter**: Dark, low-pass filtering
- **Effect**: Deep reverb
- **Pitch**: Downward movement

### For High Score Sound:
- **Oscillator**: Bright major chord or ascending arpeggio
- **Envelope**: Quick attack (20-50ms), medium sustain
- **Filter**: Open, bright high-pass
- **Effect**: Sparkling reverb or delay
- **Pitch**: Upward trajectory, triumphant
- **Vibe**: "You did it!" celebration

---

## Testing Your Sounds

### In-Game Test:
1. Load the game
2. Click "settings" → toggle SFX on/off to test
3. When you enable SFX, it plays the "spawn" sound as confirmation
4. Play a game and listen for:
   - Spawn: Every move
   - Merge: When tiles combine
   - Victory: When you reach target
   - Game Over: When board fills

### Console Test:
Open browser console and type:
```javascript
SoundEffects.play('merge');    // Test merge sound
SoundEffects.play('spawn');    // Test spawn sound
SoundEffects.play('victory');  // Test victory sound
SoundEffects.play('gameOver'); // Test game over sound
```

---

## Advanced: Pitch Variation by Tile Value (Future Enhancement)

Want merge sounds to get higher-pitched as tiles get bigger? Add this to `game.js`:

```javascript
// In moveLeft() after merge occurs:
if (row[j] === row[j + 1]) {
    row[j] *= 2;
    this.score += row[j];
    
    // Play merge with pitch based on value
    this.playMergeSound(row[j]);
    
    row.splice(j + 1, 1);
    mergeOccurred = true;
}

// Add this method to Game2048 class:
playMergeSound(tileValue) {
    // Map tile value to pitch multiplier
    const pitchMap = {
        4: 0.9,    // Lower
        8: 1.0,    // Normal
        16: 1.1,   // Slightly higher
        32: 1.2,
        64: 1.3,
        128: 1.4,
        256: 1.5,  // Much higher
        512: 1.6,
        1024: 1.7,
        2048: 1.8,
        4096: 1.9,
        8192: 2.0  // Double pitch!
    };
    
    const sound = SoundEffects.sounds.merge.cloneNode();
    sound.playbackRate = pitchMap[tileValue] || 1.0;
    sound.volume = 0.3;
    sound.play();
}
```

---

## Browser Audio Gotchas

### Autoplay Prevention:
- Browsers block audio until user interaction
- First click/tap enables audio
- This is normal behavior (your code handles it gracefully)

### Sound Cloning:
- Code uses `cloneNode()` to allow overlapping sounds
- Multiple merges can play at once
- Clones are cleaned up after playing

### Missing Files:
- If a sound file is missing, game continues without error
- Check browser console for warnings
- Placeholders work fine - just use same file for all

---

## File Size Guidelines

For your .ogg files:
- **Spawn/Move**: 5-20 KB (short, simple)
- **Merge**: 10-30 KB (slightly longer)
- **Victory/GameOver**: 20-80 KB (longer, more complex)

Keep total SFX folder under 200 KB for quick loading.

---

## Quick Checklist

- [ ] Create `audio/sfx/` folder
- [ ] Export 6 sounds from your modular synth as .ogg files
- [ ] Name them: merge, spawn, victory, gameover, highscore, move
- [ ] Place in `audio/sfx/` folder
- [ ] Replace `main.js` with `main-with-sfx.js`
- [ ] Replace `game.js` with `game-with-sfx.js`
- [ ] Test in browser
- [ ] Adjust volumes in code if needed
- [ ] Make custom sounds when you have time!

---

## Troubleshooting

**Q: Sounds aren't playing**
A: Check browser console for "Sound effect not found" errors. Verify file paths.

**Q: Sounds are too loud/quiet**
A: Use `SoundEffects.setVolume('soundName', 0.5)` or adjust in code

**Q: Want different sounds for different tile values**
A: See "Advanced: Pitch Variation" section above

**Q: Sounds play but music doesn't**
A: Check that `gameMusic` audio element exists and music toggle is ON

**Q: Can I use .wav instead of .ogg?**
A: Yes! Just change file extensions in the code

---

## Summary

Your sound effects system is now ready! It:
- ✅ Plays sounds at the right moments
- ✅ Allows individual volume control
- ✅ Respects the SFX toggle in settings
- ✅ Handles missing files gracefully
- ✅ Supports overlapping sounds
- ✅ Is performance-optimized

Just drop in your analog synth sounds and you're good to go! 🎛️🔊
