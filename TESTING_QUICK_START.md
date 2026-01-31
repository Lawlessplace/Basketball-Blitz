# Basketball Blitz - Quick Start Testing Guide

## Setup for Testing

### Prerequisites
1. Discord bot token in `.env`
2. 6 test players (can be alts or real users)
3. Test Discord server

### Enable Test Commands
In `bot.py`, add before `if __name__`:
```python
from test_utils import create_test_commands
test_cog = create_test_commands(bot, games)
bot.add_cog(test_cog)
```

## Manual Test Scenarios

### Scenario 1: Happy Path (Full Game)
**Goal**: Verify a complete 36-move game works end-to-end

1. `/newgame` → 6 players join
2. `/start` (host) → begin
3. `/toss` + both `/tosschoose` → coin toss resolves
4. Repeat `/ctn` + attacker action + defender guess + save (×18)
5. See HALFTIME message
6. Repeat (×18)
7. See GAME OVER message
8. Verify final scores recorded

**Expected**: ~40 min, both teams score 15-30 pts each

---

### Scenario 2: AFK Attacker
**Goal**: Verify timeout transfers possession

1. Game active, `/ctn` prompts attacker
2. Attacker does NOT respond for 31s
3. Verify view closes, "Attacker AFK" behavior
4. Next `/ctn` shows opponent possession

**Expected**: Smooth possession transfer without error

---

### Scenario 3: Defender Timeout
**Goal**: Verify timeout → incorrect guess → save attempt

1. Game active, defender receives guess dropdown
2. Defender does NOT respond for 31s
3. Next action: auto-continues as incorrect guess
4. CE receives save attempt dropdown

**Expected**: Game flow uninterrupted

---

### Scenario 4: Sub Accept/Decline
**Goal**: Verify substitution flow

**Test A - Accept**:
1. Captain: `/sub 1 pg @NewPlayer`
2. NewPlayer: Click "Accept" in dropdown
3. Verify NewPlayer now in Team 1 PG slot
4. `/livescore` confirms change

**Test B - Decline**:
1. Captain: `/sub 1 sg @Player2`
2. Player2: Click "Decline"
3. Verify Player2 not in slot
4. Original SG still active

**Test C - Timeout**:
1. Captain: `/sub 2 ce @Player3`
2. Player3: Do NOT respond for 16s
3. Verify sub request cleared, original CE active

**Expected**: All three flows work cleanly

---

### Scenario 5: Sidepass Flow
**Goal**: Verify complex sidepass → SG → save sequence

1. PG chooses "Side-pass to SG"
2. CE makes guess (say, 'dribble')
3. Guess is wrong → SG gets dropdown
4. SG chooses shot (say, "Dribble → Layup")
5. CE gets save attempt dropdown
6. CE saves or fails → score awarded

**Expected**: All prompts appear correctly, score awarded at end

---

### Scenario 6: No Defender
**Goal**: Verify auto-score when CE missing

1. Team 2 CE leaves (`/leave` before game, or sub them out)
2. Team 1 attacks with PG action
3. Verify message: "No defender present — scored X points"
4. Move count increments, no CE guess/save

**Expected**: Auto-score without error

---

### Scenario 7: Persistence
**Goal**: Verify save/load across restart

1. Play game to move 10
2. `/livescore` shows scores, move 10
3. Kill bot (Ctrl+C)
4. Restart bot
5. `/livescore` shows same state (move 10, same scores)

**Expected**: Game state fully restored

---

### Scenario 8: Halftime Transition
**Goal**: Verify halftime message and resume

1. Use `/test_advance 8` to jump to move 8
2. `/ctn` (moves to 9, 10, ..., 18)
3. At move 18: `/ctn` shows HALFTIME message
4. `/ctn` again → resumes second half (move 19)

**Expected**: Clear halftime break, smooth resume

---

### Scenario 9: Sudden Death OT
**Goal**: Verify tie → overtime

1. Use `/test_score 1 20` and `/test_score 2 20` (equal scores)
2. Use `/test_advance 18` to move to 36
3. One team scores → should show GAME OVER + "SUDDEN DEATH OVERTIME"
4. Game continues (active = True, moves reset to 36)

**Expected**: Smooth transition to OT, game continues

---

### Scenario 10: Guess Matching
**Goal**: Verify guess logic works correctly

**Test A - 3-pointer**:
1. PG chooses "Fullcourt shot"
2. CE guesses "3-pointer"
3. Should match ✓

**Test B - Dribble**:
1. SG chooses "Dribble → Layup"
2. CE guesses "dribble"
3. Should match ✓

**Test C - Suffix**:
1. PG chooses "Dribble → Jump shot"
2. CE guesses "jump shot"
3. Should match ✓

**Test D - Wrong guess**:
1. PG chooses "Halfcourt"
2. CE guesses "dribble"
3. Should NOT match ✗

**Expected**: Matching logic works as intended

---

## Checklist for Tester

- [ ] Created test Discord server
- [ ] Invited 6+ test players
- [ ] Bot running with test commands enabled
- [ ] All 10 scenarios completed
- [ ] No errors or unexpected behavior
- [ ] Persistence works (restart test)
- [ ] Game takes ~40 min
- [ ] Both teams can win
- [ ] Timeouts work as expected
- [ ] Final scores range 15-30 points

## Issues Found
(Record any bugs or balance concerns here during testing)

### Bug Template
```
**Title**: [e.g., "Sidepass doesn't prompt SG"]
**Steps to reproduce**:
1. 
2. 
3. 
**Expected**: 
**Actual**: 
**Severity**: [Critical/High/Medium/Low]
```

### Balance Feedback Template
```
**Issue**: [e.g., "Defenders too weak"]
**Observation**: [e.g., "CEs won every game"]
**Suggestion**: [e.g., "Reduce guess options to 7"]
```

## Success Criteria

✅ **Ready for launch if**:
- All 10 scenarios complete without errors
- No critical bugs found
- Game feels balanced (both teams win sometimes)
- Timeouts feel natural (not too fast/slow)
- Persistence works across restart

⚠️ **Needs tweaks if**:
- One team always wins
- Timeouts too short/long
- Persistence loses data
- Command errors occur
- Bottlenecks in UI/flow

## Reporting
After testing, submit results:
- Scenario completion status
- Bug reports (with reproduction steps)
- Balance feedback
- Time logged per game
- Player enjoyment rating (1-10)
