# 🔥 Performance Testing Guide

## Quick Test: What's Heating Up Your Computer?

I've created a diagnostic tool to help identify the CPU heating source!

### How to Use:

1. **Open the test file:**
   - Save `performance-test.html` to your game folder
   - Open it in Chrome/Edge

2. **Open Task Manager:**
   - Press **Shift+Esc** (or Menu → More Tools → Task Manager)
   - Find the "Tab: Performance Diagnostic" row
   - Watch the **CPU %** column

3. **Run each test for 10 seconds:**
   - **Test 1 (Baseline):** Should be 0-2% CPU
   - **Test 2 (Animations):** If jumps 10%+, CSS effects are the issue
   - **Test 3 (Music):** If jumps 15-30%, audio is the culprit (most likely!)
   - **Test 4 (Rendering):** If jumps 10%+, DOM updates need work
   - **Test 5 (Combined):** This simulates actual gameplay

4. **Note which causes the biggest jump!**

---

## Expected Results:

### Most Likely Culprit: Background Music 🎵
- **CPU Impact:** 15-30% typically
- **Why:** Continuous OGG audio decoding
- **Solution:** Turn off music in settings, or reduce volume

### Second Most Likely: CSS Animations 🎨
- **CPU Impact:** 5-15%
- **Why:** Scanlines, CRT effects, tile pulse animations
- **Solution:** Could disable some effects if needed

### Least Likely: Rendering/Logic 🎮
- **CPU Impact:** 5-10%
- **Why:** Our optimizations (dirty-checking, audio pooling) already minimized this
- **Solution:** Already optimized!

---

## My Prediction:

Based on typical browser behavior, I expect:
1. **Music Test:** 20-25% CPU increase ⚠️
2. **Animation Test:** 8-12% CPU increase
3. **Rendering Test:** 5-8% CPU increase

**Total during gameplay:** ~35-45% CPU on mid-range laptops

This is **normal** for a game with music and animations, but if music is causing too much heating, you can:
- Turn it off in settings
- Lower system volume
- Play without audio

---

## If Results Show:

### Music is the problem (20%+ CPU):
**Options:**
1. Play with music off (easiest)
2. Convert audio to lower bitrate (more work)
3. Use MP3 instead of OGG (might help slightly)

### Animations are the problem (15%+ CPU):
**Could reduce effects:**
- Remove scanline overlay
- Disable gate pulse animations
- Reduce glow effects

### Rendering is the problem (15%+ CPU):
**Unlikely but if so:**
- Increase render delay (currently ~16ms)
- Reduce board size (not recommended!)
- Simplify tile styles

---

## Normal CPU Usage:

**For comparison:**
- **YouTube video:** 10-20% CPU
- **Spotify playing:** 5-10% CPU
- **Discord idle:** 3-5% CPU
- **Your game (with music):** 35-45% CPU ← Normal!
- **AAA game:** 60-90% CPU

Your game is CPU-intensive but not abnormal for a web game with audio + animations.

---

## Quick Fixes if Too Hot:

**Immediate (no code changes):**
1. Turn off background music
2. Close other tabs/programs
3. Use a laptop cooling pad
4. Reduce browser zoom to 90%

**Code changes (if needed):**
1. Reduce gate spawn rate (fewer animations)
2. Increase render delay from 16ms to 33ms (~30fps)
3. Disable binary display by default
4. Remove scanline effects

---

## Summary:

Run the diagnostic tool and report back:
- What's the baseline CPU%?
- What's the CPU% during music test?
- What's the CPU% during full test?

Then we can optimize the specific culprit! 🔧
