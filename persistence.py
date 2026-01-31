import sqlite3
import json
from typing import Dict, Optional, List
from game_core import GameState, Team, PlayerSlot

DB_PATH = 'basketball_blitz.db'


def init_db():
    """Initialize database schema."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Games table
    c.execute('''
        CREATE TABLE IF NOT EXISTS games (
            guild_id INTEGER PRIMARY KEY,
            host_id INTEGER,
            active INTEGER,
            move_count INTEGER,
            current_possession_team INTEGER,
            current_attacker_pos TEXT,
            toss_active INTEGER,
            toss_choices TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Teams table
    c.execute('''
        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER,
            team_id INTEGER,
            name TEXT,
            captain_id INTEGER,
            score INTEGER,
            FOREIGN KEY (guild_id) REFERENCES games(guild_id),
            UNIQUE(guild_id, team_id)
        )
    ''')
    
    # Player slots table
    c.execute('''
        CREATE TABLE IF NOT EXISTS player_slots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER,
            team_id INTEGER,
            position TEXT,
            user_id INTEGER,
            name TEXT,
            afk INTEGER,
            FOREIGN KEY (guild_id) REFERENCES games(guild_id),
            UNIQUE(guild_id, team_id, position)
        )
    ''')
    
    # Sub requests table
    c.execute('''
        CREATE TABLE IF NOT EXISTS sub_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER,
            team_id INTEGER,
            out_pos TEXT,
            in_user_id INTEGER,
            in_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (guild_id) REFERENCES games(guild_id)
        )
    ''')
    
    conn.commit()
    conn.close()


def save_game(guild_id: int, gs: GameState):
    """Save game state to database."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Save game
    c.execute('''
        INSERT OR REPLACE INTO games 
        (guild_id, host_id, active, move_count, current_possession_team, current_attacker_pos, toss_active, toss_choices)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        guild_id,
        gs.host_id,
        1 if gs.active else 0,
        gs.move_count,
        gs.current_possession_team,
        gs.current_attacker_pos,
        1 if gs.toss_active else 0,
        json.dumps(gs.toss_choices)
    ))
    
    # Save teams and slots
    for team_id, team in gs.teams.items():
        c.execute('''
            INSERT OR REPLACE INTO teams
            (guild_id, team_id, name, captain_id, score)
            VALUES (?, ?, ?, ?, ?)
        ''', (guild_id, team_id, team.name, team.captain_id, team.score))
        
        for pos, slot in team.slots.items():
            if slot:
                c.execute('''
                    INSERT OR REPLACE INTO player_slots
                    (guild_id, team_id, position, user_id, name, afk)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (guild_id, team_id, pos, slot.user_id, slot.name, 1 if slot.afk else 0))
            else:
                # Clear empty slot
                c.execute('DELETE FROM player_slots WHERE guild_id=? AND team_id=? AND position=?',
                         (guild_id, team_id, pos))
    
    # Save sub requests
    c.execute('DELETE FROM sub_requests WHERE guild_id=?', (guild_id,))
    for in_user_id, req in gs.sub_requests.items():
        c.execute('''
            INSERT INTO sub_requests
            (guild_id, team_id, out_pos, in_user_id, in_name)
            VALUES (?, ?, ?, ?, ?)
        ''', (guild_id, req.team, req.out_pos, req.in_user_id, req.in_name))
    
    conn.commit()
    conn.close()


def load_game(guild_id: int) -> Optional[GameState]:
    """Load game state from database."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Load game
    c.execute('SELECT * FROM games WHERE guild_id=?', (guild_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return None
    
    host_id, active, move_count, curr_team, curr_pos, toss_active, toss_choices = row[1:8]
    
    gs = GameState(host_id)
    gs.active = bool(active)
    gs.move_count = move_count
    gs.current_possession_team = curr_team
    gs.current_attacker_pos = curr_pos
    gs.toss_active = bool(toss_active)
    gs.toss_choices = json.loads(toss_choices) if toss_choices else {}
    
    # Load teams
    c.execute('SELECT team_id, name, captain_id, score FROM teams WHERE guild_id=?', (guild_id,))
    for team_id, name, captain_id, score in c.fetchall():
        if team_id in gs.teams:
            gs.teams[team_id].name = name
            gs.teams[team_id].captain_id = captain_id
            gs.teams[team_id].score = score
    
    # Load player slots
    c.execute('SELECT team_id, position, user_id, name, afk FROM player_slots WHERE guild_id=?', (guild_id,))
    for team_id, pos, user_id, name, afk in c.fetchall():
        if team_id in gs.teams:
            gs.teams[team_id].slots[pos] = PlayerSlot(
                user_id=user_id,
                name=name,
                position=pos,
                afk=bool(afk)
            )
    
    # Load sub requests
    c.execute('SELECT team_id, out_pos, in_user_id, in_name FROM sub_requests WHERE guild_id=?', (guild_id,))
    for team_id, out_pos, in_user_id, in_name in c.fetchall():
        from game_core import SubRequest
        req = SubRequest(team=team_id, out_pos=out_pos, in_user_id=in_user_id, in_name=in_name)
        gs.sub_requests[in_user_id] = req
    
    conn.close()
    return gs


def delete_game(guild_id: int):
    """Delete game from database."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM games WHERE guild_id=?', (guild_id,))
    c.execute('DELETE FROM teams WHERE guild_id=?', (guild_id,))
    c.execute('DELETE FROM player_slots WHERE guild_id=?', (guild_id,))
    c.execute('DELETE FROM sub_requests WHERE guild_id=?', (guild_id,))
    conn.commit()
    conn.close()


def list_games() -> List[int]:
    """Get all guild IDs with active games."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT guild_id FROM games WHERE active=1')
    result = [row[0] for row in c.fetchall()]
    conn.close()
    return result
