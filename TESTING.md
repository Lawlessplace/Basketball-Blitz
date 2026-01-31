# Basketball Blitz - Testing & Balancing Guide

## Testing Checklist

### 1. Lobby Creation & Player Management
- [ ] `/newgame` creates a new lobby (single per guild)
- [ ] Cannot create a second `/newgame` while one is active
- [ ] `/join` adds players in order (6 player cap)
- [ ] Players assigned alternately: Team 1 PG, Team 2 PG, Team 1 SG, Team 2 SG, Team 1 CE, Team 2 CE
- [ ] `/leave` removes players before game starts
- [ ] `/leave` fails during active game
- [ ] `/livescore` displays correct team assignments and scores

### 2. Game Start & Coin Toss
- [ ] `/start` (host-only) requires both teams full (6 players)
- [ ] `/start` fails if not host
- [ ] `/toss` initializes coin toss
- [ ] `/tosschoose` (captain-only) accepts HIGH/LOW
- [ ] Toss resolves when both captains choose
- [ ] Winner gets possession at PG with `/ctn`

### 3. Attacker Actions (PG)
- [ ] PG options appear in dropdown:
  - Side-pass to SG
  - Dribble → Layup
  - Dribble → Jump shot
  - Halfcourt shot (PG)
  - Fullcourt shot (PG)
  - Hold (bounce pass)
  - Play back
- [ ] Timeout after 30s marks attacker AFK → possession to opponent
- [ ] CE receives defender guess prompt immediately

### 4. Attacker Actions (SG)
- [ ] SG options appear in dropdown:
  - Dribble → Layup
  - Dribble → Dunk
  - 3-pointer Halfcourt
  - 3-pointer Fullcourt
- [ ] 3-pointer actions award 3 pts on success, 2 pts otherwise

### 5. Defender Guessing
- [ ] Defender (CE) receives dropdown with guesses
- [ ] Correct guess (matching attacker choice) → CE gains possession
- [ ] Incorrect guess:
  - If sidepass: SG receives dropdown for shot choice
  - If direct shot: attacker proceeds to save attempt
- [ ] Timeout after 30s → treat as incorrect guess
- [ ] Move count increments on guess resolution

### 6. Sidepass Flow
- [ ] PG side-pass triggers SG dropdown
- [ ] SG chooses shot (2 or 3 pts)
- [ ] CE attempts save on SG shot
- [ ] If SG not present: automatic 2pt score for team

### 7. Save Attempts
- [ ] CE receives save dropdown
- [ ] Correct save (matching shot type) → CE gains possession
- [ ] Incorrect save or timeout → attacker scores (2 or 3 pts)
- [ ] After score: possession goes to opponent PG

### 8. Substitutions
- [ ] `/sub team position @player` (captain-only)
- [ ] Player receives 15s dropdown: Accept/Decline
- [ ] Accept → player joins team, slot replaced
- [ ] Decline → sub request cleared
- [ ] Timeout → sub request cleared

### 9. Move & Halftime
- [ ] Move count increments after each possession resolves
- [ ] At move 18: `/ctn` triggers halftime message
- [ ] Halftime shows team scores
- [ ] `/ctn` resumes second half

### 10. Game End & Overtime
- [ ] At move 36: game ends, final scores displayed
- [ ] If scores tied: sudden death overtime triggered
- [ ] Move count resets to 36 for OT
- [ ] Game continues until one team scores

### 11. Persistence
- [ ] Game state saved after every state change
- [ ] Bot restart loads active games
- [ ] `/yeet` deletes game from database

### 12. AFK Handling
- [ ] Attacker timeout (30s) → AFK marked
- [ ] Defender timeout (30s) → incorrect guess processed
- [ ] AFK players can still receive sub requests

## Balance Review

### Timeouts
- **Attacker action**: 30s (reasonable for complex dropdown)
- **Defender guess**: 30s (adequate for 10 options)
- **SG/Save attempt**: 30s (matches difficulty)
- **Sub accept**: 15s (quick decision)
- **Verdict**: ✅ Balanced; timeouts are generous

### Scoring
- **2pt shot**: layup, dunk, dribble → layup, dribble → dunk
- **3pt shot**: halfcourt, fullcourt
- **Verdict**: ✅ 2/3 distribution reasonable; defenders can swing games with smart guesses

### Possession Flow
- **Attacker-first**: PG/SG choose, CE guesses, CE saves = skill-based
- **CE gains possession on correct guess or save**: Encourages defensive plays
- **AFK → opponent possession**: Penalizes inactivity
- **Verdict**: ✅ Flow favors active participation

### Game Length
- **36 moves** (18 per half) ≈ ~30-45 min if 2-3 min per possession
- **Sudden death OT**: Prevents stalemate
- **Verdict**: ✅ Appropriate for Discord casual play

### Guess Matching
- **3-pointer variants** match '3-pointer', 'halfcourt', 'fullcourt'
- **Dribble variants** match 'dribble'
- **Suffix matching** for specific moves
- **Verdict**: ⚠️ May be too forgiving; consider stricter matching if desired

## Known Issues & Fixes

### Potential Issues:
1. **DefenderGuessView.on_timeout()** doesn't send message to channel (best-effort in design)
   - **Fix**: Store interaction/message ref for timeout fallback
   - **Severity**: Low (game continues, just no user feedback)

2. **SaveAttemptView options** are limited (4 options) vs DefenderGuessView (10)
   - **Fix**: Add more save types if desired (bank shot, hook shot)
   - **Severity**: Low (by design to simplify)

3. **No rate-limiting** on command spam
   - **Fix**: Add cooldowns if needed
   - **Severity**: Low (Discord's native rate limiting)

4. **Persistence doesn't track join_order**
   - **Fix**: Modify persistence schema to store join_order if needed
   - **Severity**: Low (only used for lobby lock)

## Recommendations

1. **Run a 10-game test series** with 6 players to verify balance
2. **Test AFK scenarios** explicitly (leave during game, timeout attacker)
3. **Test sub flow** with accept/decline/timeout
4. **Test persistence** by restarting bot mid-game
5. **Gather feedback** on timeout durations from test players
6. **Log game results** to monitor final scores and possession patterns

## Balancing Adjustments (if needed)

| Issue | Adjustment |
|-------|-----------|
| Games too long | Reduce moves to 24 (12 per half) |
| Defenders too weak | Make save-only on correct guess (no possession) |
| Attackers too weak | Reduce CE options in dropdown to 6 |
| Sidepass too risky | Auto-score for sidepass if no SG |
| Matches too close | Add score multipliers or sudden death rules |
