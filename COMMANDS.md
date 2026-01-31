/newgame
- Create a new game lobby. Host becomes game host.
- Usage: `/newgame <team_size=3>` (team_size fixed at 3 for now).

/join
- Join the current lobby. Auto-assigns available position (PG, SG, CE) in join order.
- Usage: `/join`

/leave
- Leave the lobby when no game is active. During an active game `/leave` marks the player as AFK but does not free the slot; AFK players cannot act and timeouts will hand possession to the opposing player they were facing after 30s.
- Usage: `/leave`

/toss
- Start the tip-off vote between captains. Must be done pre-game. Captains choose `high` or `low`. Bot randomly picks `high` or `low`.
- Usage: `/toss`

/ctn
- Change team name (pre-game only).
- Usage: `/ctn <team> <new_name>`

/livescore
- Show current lineups and the score. Works in-lobby and in-game.
- Usage: `/livescore`

/swap
- Captains swap players by slot number. Allowed at game start and halftime only.
- Usage: `/swap <team> <slot1> <slot2>`

/sub
- Substitute a player into a position. Captains initiate a substitution by specifying the player to sub out and the player to sub in; the incoming player will be presented a dropdown with `Accept` / `Decline` and has 15 seconds to respond. If the incoming player accepts, the substitution completes; if they decline or time out the substitution is cancelled. Captains may use `/sub` to replace a player marked AFK during an active match.
- Usage: `/sub <team> <position> <@player>`

/start
- Start the match. Only the game host may run `/start`. Requires `/toss` resolution and both teams filled.
- Usage: `/start`

/yeet
- End the current game immediately.
- Usage: `/yeet`

 - All player choices within plays must be responded to within 30 seconds:
	 - If the attacking player does not choose within 30s they are marked AFK and possession turns over to the opposing team (the team who would guess; opposing PG gains possession).
	 - If the defender (guesser) does not choose within 30s the guess is treated as incorrect: the attacking move plays out and the CE still receives the normal one-save attempt on the resulting shot.
- Input order: the attacking player chooses their action first, then the defender (usually the CE) makes their guess.

UI & interactions
- Player decision options are presented using dropdown lists (select menus) listing all valid choices for that decision. When the attacker selects an option the bot will ping the defending player to request a guess; the defending player then has 30s to respond.

Defensive guessing
- The Centre (CE) during defensive prompts may guess `3-pointer`, `dribble`, `sidepass`, or specific shot types (e.g., `layup`, `dunk`, `halfcourt`, `fullcourt`, `jump shot`, `bank shot`, `hook shot`).
- If the CE's guess matches the attacker's chosen action exactly, the defensive outcome is applied immediately; if incorrect, the attacker proceeds and the CE gets one save attempt on the shot as described in `DESIGN.md`.
