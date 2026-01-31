# Basketball Blitz - Balance & Mechanics Review

## Game Overview
**Basketball Blitz** is a 6v6 Discord turn-based guessing game where:
- 36 moves total (18 per half)
- Attacker chooses action → Defender guesses → CE saves (optional)
- Possession transfers based on guess/save success
- Scoring: 2pt or 3pt per move

## Current Mechanics

### Positions & Roles
| Position | Attacker Moves | Defender Role |
|----------|---|---|
| **PG** (Point Guard) | 7 options (2-3 pts) | Guess action |
| **SG** (Shooting Guard) | 4 options (2-3 pts) | Guess + Save |
| **CE** (Centre) | N/A (always defender) | Guess + Save |

### Possession Transitions
```
Attacker Choose
    ↓
CE Guesses:
  ✓ Correct → CE possession
  ✗ Incorrect → Continue to CE Save
        ↓
  ✓ Save → CE possession
  ✗ Save Fail → Attacker scores → Opponent PG possession
```

### Special Cases
- **Sidepass**: PG passes to SG → SG chooses shot → CE saves
- **No Defender**: Auto-score (2 or 3 pts based on action)
- **AFK**: Attacker timeout → opponent possession; Defender timeout → incorrect guess

### Move Timing
```
Total game: 36 moves
Halftime: After move 18
Overtime: If tied at move 36 (sudden death)
```

## Balance Analysis

### Attack vs Defense
**Current**: 
- Attacker advantages: first-mover, 7-10 options
- Defender advantages: guessing can steal possession

**Verdict**: ✅ **Balanced**
- Attackers can win games by smart play
- Defenders can stop attackers with correct guesses
- High variance creates exciting gameplay

### Scoring Distribution
- 2pt shots: 70% (layup, dunk, dribble shots)
- 3pt shots: 30% (halfcourt, fullcourt)

**Verdict**: ✅ **Realistic**
- Majority are 2pt (common in basketball)
- 3pt available but risky
- Leads to 20-35 point games (reasonable)

### Guess Matching Logic
Current rules:
```python
if '3' in choice or 'halfcourt' in choice or 'fullcourt' in choice:
    match '3-pointer', 'halfcourt', 'fullcourt'
if 'dribble' in choice:
    match 'dribble'
suffix match for specific moves
```

**Analysis**:
- ✅ Forgiving for defenders (one guess works for all 3-pointers)
- ⚠️ Could be stricter if desired (e.g., require exact position match)
- ✅ Encourages defensive play without requiring memorization

**Verdict**: ✅ **Good for casual play**

### Game Length
Estimated: 30-45 min per game
- 36 moves × 60s avg per move = 36 min
- With halftime messages: +5 min
- Natural breaks at 18 & 36 moves

**Verdict**: ✅ **Discord-friendly duration**

### Timeout Values
| Timeout | Current | Assessment |
|---------|---------|---|
| Attacker action | 30s | ✅ Generous, allows dropdown selection |
| Defender guess | 30s | ✅ Adequate for 10 options |
| SG/Save attempt | 30s | ✅ Matches defender difficulty |
| Sub accept | 15s | ✅ Quick but not rushed |

**Verdict**: ✅ **Well-tuned for human reaction time**

### Sidepass Risk
Current: PG can sidepass → SG must choose → CE can save
- Risk: SG might time out, auto-scores 2pt
- Reward: Bypasses CE's guess on first action

**Verdict**: ✅ **Interesting risk/reward**
- Sidepass is viable but not overpowered
- Creates team coordination opportunities

### Halftime & Overtime
- Halftime at move 18: ✅ Good psychological break
- Sudden death OT: ✅ Prevents ties (exciting)

**Verdict**: ✅ **Adds narrative drama**

## Potential Tweaks

### Minor Adjustments
If feedback suggests unbalance:

**If Attacks are too strong**:
- Reduce attacker options from 7 to 5 (remove Hold/Play Back)
- Increase defender timeout to 40s
- Make sidepass auto-score (no CE save)

**If Defense is too strong**:
- Reduce defender guess options from 10 to 7
- Make correct guess only grant possession to CE, no move increment
- Increase attacker timeout to 45s

**If games drag**:
- Reduce moves to 24 (12 per half)
- Reduce timeouts by 5s across the board
- Remove sudden death (end at 36 with tiebreaker rule)

**If games are too short**:
- Increase moves to 48 (24 per half)
- Add "challenge" mechanic (limited rerolls per team)

### Data to Collect
During testing, track:
- Average game duration
- Final score distribution (typically 15-30 range?)
- Win rate by starting possession
- Timeout frequency
- Most common winning strategies

## Design Philosophy

**Basketball Blitz** prioritizes:
1. **Simplicity**: 3 positions, clear roles, 30s timeouts
2. **Parity**: 36 moves ensures both teams attack equally
3. **Skill**: Guess matching rewards game knowledge
4. **Pace**: ~40 min games fit Discord culture
5. **Drama**: Sudden death OT and last-minute saves

## Conclusion

**Current balance is SOLID** ✅

- Mechanics are fair and straightforward
- Game length is appropriate for async Discord play
- Guess/save system encourages both attack and defense
- Timeouts are reasonable for human players
- Sudden death prevents unexciting ties

**Recommended**: Run 10-game test season with feedback survey on:
- Was the game fun?
- Was balance fair (both teams had chance to win)?
- Was pace okay?
- Would you change timeout durations?
- Suggest rule tweaks?

No major balance changes needed at launch.
