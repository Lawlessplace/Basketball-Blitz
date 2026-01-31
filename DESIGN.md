Basketball Blitz — Design Document

Overview
- Fast-paced, turn-based Discord game played by two teams.
- Each team fields 3 active players: Point Guard (PG), Shooting Guard (SG), Centre (CE). Subs are unlimited.
- A single game ends after 36 moves (combined turns) or when `yeet` is used to end the game.
- No RNG/probabilities; outcomes are determined by player choices and opponent guesses.
- No stamina, fouls, or power-ups for now.

Game setup
- Create a game with `/newgame`.
- The lobby holds a maximum of 6 players (two teams of 3). Once 6 players have joined the lobby is locked.
- Players join with `/join` and are auto-assigned to positions (PG, SG, CE) in join order.
- Captains: the CE of each team is auto-assigned as captain at start. Host can change captains before the game.
- Team names can be changed pre-game with `/ctn`.
- Toss (tip-off) is performed with `/toss` before the game starts. Captains choose `high` or `low` jump; the bot randomly picks `high` or `low` and the captain who matches wins first possession.

Turn & move rules
- The game is limited to 36 total moves. Increment move count at the start of each ball possession/action sequence.
  - Halftime occurs after 18 moves (half of 36). At halftime captains may perform `/swap` operations.
- Each possession begins with the attacking teams PG (except tip-off resolution).
  - Players have 30 seconds to respond to their prompted action.
    - If the attacking player fails to choose within 30 seconds they are marked AFK and possession turns over to the opposing team (the team who would make the defensive guess; opposing PG gains possession).
    - If the defending player (the guesser, usually the CE) fails to submit a guess within 30 seconds, the guess is treated as incorrect and the attacking move plays out; the CE still receives the normal one-save opportunity on the resulting shot as described in "Scoring & possession outcomes."
  - Input order: the attacking player chooses their action first, then the opposing player (usually the CE) makes their defensive guess.
- Action order and available choices (high level):
  1. PG phase: PG may `dribble`, `sidepass` (to SG), `hold` (which unlocks `bounce pass`), or `play back`.
  2. If PG beats opposing PG (structure: PG vs PG guess/choice), PG can attempt to dribble past CE or pass to SG.
   3. SG options on receiving a side-pass: the SG can choose to `take shot` or `dribble`.
     - If the SG chooses `dribble`, their available shots are `layup` or `dunk` (both 2 points).
     - If the SG chooses `take shot` as a 3-pointer, they must select `halfcourt` or `fullcourt` (3 points).
     - Side-pass gives immediate possession to the SG.
  4. PG shot options: `halfcourt` or `fullcourt` (treated as long shots; scoring values follow the 2/3 rules above per shot type).
   5. CE (defense) may guess/choose in response: the CE can guess `3-pointer`, `dribble`, or `sidepass` when prompted, and may also guess specific shot types the attacker selects (e.g., `layup`, `dunk`, `halfcourt`, `fullcourt`, `jump shot`, `bank shot`, `hook shot`).
       - If the CE's guess matches the attacking player's choice exactly, the defensive outcome applies immediately (see "Scoring & possession outcomes").
       - Examples:
         - If the CE guesses `layup` and the attacker selected `layup`, the defence is correct — treat as a successful defensive play (possession turns over to the opposing PG unless the specific shot rule states otherwise).
         - If the CE guesses `3-pointer` and the attacker attempts a `fullcourt` or `halfcourt` 3-point, the defence is correct and will attempt the 3-pointer save outcome.
       - If the CE's guess is incorrect, the attacking team proceeds to take their chosen shot; the CE then has one chance to save on the resulting attempt (as described in scoring rules).

Scoring & possession outcomes
- 2-point shot scored → add 2 points to scoring team and possession turns over to the conceding teams PG (attacking next).
- 3-point shot scored → add 3 points to scoring team and possession turns over to the conceding teams PG.
 - If defense guesses correctly on a 2-point shot → the CE gains possession (centre who guessed correctly).
 - If defense saves a 3-pointer (guesses correctly), CE gains possession (centre who saved it).
 - If defence guesses correctly during dribble attempts, possession turns over to the opposing PG and play continues.
 - If the defence fails a guess, the attacking team gets the shot; the CE then has one chance to save. If the CE saves, the CE gains possession; otherwise points are added and possession goes to conceding team’s PG.
 - If scores are tied after 36 moves the match goes to sudden-death overtime: play continues move-by-move until one team scores; the first score wins.

Substitutions, swaps, and halftime rules
- Subs are unlimited. Captains initiate a substitution by specifying the player to sub out and the player to sub in. The incoming player will receive an `Accept` / `Decline` dropdown and has 15 seconds to respond; if they accept the substitution it takes effect immediately, otherwise it is cancelled. Captains may sub out players during the game subject to incoming-player confirmation.
- `/swap` allowed at game start and at halftime only; captains can swap players by position number.

Administrative rules
- `/ctn` and `/toss` must be done before `/start` (pre-game).
- `/swap` allowed pre-game and at halftime only.
- `/yeet` forcibly ends the game at any time.
- `/livescore` shows current lineup and scores.
- `/start` begins the match after setup and toss resolution.

Edge cases
 - Players cannot fully leave an ongoing game. If a player attempts to leave or becomes unresponsive during an active match they are marked AFK. While AFK their slot remains assigned but they will not be able to act; if a required action times out (30s) the possession turns over to the opposing player they were facing.
 - If captains agree a player is AFK they may immediately replace that player using `/sub` to restore an active participant in that position.
- UI: player choices are presented via dropdown lists containing all valid options for the current decision. When the attacking player picks an option the bot will ping the defending player to prompt their defensive guess.
- Simultaneous inputs: resolve by timestamp; earliest valid input wins when order matters.

Persistence
- Game state should be saved (recommended: SQLite) so restarts do not lose ongoing matches.

Telemetry & balancing
- Log actions and outcomes for later tuning. The game is deterministic based on choices and guesses; balance tuning primarily adjusts allowed choices and turn flow.

This document encodes the core rules you provided. If you want, I can now create `COMMANDS.md` that maps each slash command to exact bot behavior and permissions, then implement the first prototype (in-memory) of the game logic and commands. 
