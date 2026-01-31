import asyncio
from dataclasses import dataclass, field
from typing import Dict, Optional, List

MAX_MOVES = 36
HALFTIME = 18
JOIN_LIMIT = 6

@dataclass
class PlayerSlot:
    user_id: int
    name: str
    position: str  # 'pg','sg','ce'
    afk: bool = False

@dataclass
class Team:
    name: str
    slots: Dict[str, Optional[PlayerSlot]] = field(default_factory=lambda: {'pg': None, 'sg': None, 'ce': None})
    captain_id: Optional[int] = None
    score: int = 0

@dataclass
class SubRequest:
    team: int
    out_pos: str
    in_user_id: int
    in_name: str
    task: Optional[asyncio.Task] = None

class GameState:
    def __init__(self, host_id: int):
        self.host_id = host_id
        self.teams: Dict[int, Team] = {1: Team(name='Team 1'), 2: Team(name='Team 2')}
        self.move_count = 0
        self.active = False
        self.current_possession_team: Optional[int] = None
        self.current_attacker_pos: Optional[str] = None
        self.sub_requests: Dict[int, SubRequest] = {}
        self.locked = False
        self.join_order: List[int] = []
        self.toss_active = False
        self.toss_choices: Dict[int, str] = {}

    def join_player(self, user_id: int, name: str) -> Optional[str]:
        if self.locked or len(self.join_order) >= JOIN_LIMIT:
            return None
        # prevent a user joining more than once / occupying multiple positions
        for t in self.teams.values():
            for s in t.slots.values():
                if s and s.user_id == user_id:
                    return None
        # assign to first available slot across teams
        for team_id in (1,2):
            team = self.teams[team_id]
            for pos in ('pg','sg','ce'):
                if team.slots[pos] is None:
                    slot = PlayerSlot(user_id=user_id, name=name, position=pos)
                    team.slots[pos] = slot
                    if team.captain_id is None:
                        team.captain_id = slot.user_id  # CE auto-assigned earlier, but simple fallback
                    self.join_order.append(user_id)
                    if len(self.join_order) >= JOIN_LIMIT:
                        self.locked = True
                    return f'{team_id}:{pos}'
        # if no empty slot
        return None

    def leave_player(self, user_id: int) -> bool:
        # only allow leave if not active
        if self.active:
            return False
        for t in self.teams.values():
            for p, slot in t.slots.items():
                if slot and slot.user_id == user_id:
                    t.slots[p] = None
                    if user_id in self.join_order:
                        self.join_order.remove(user_id)
                    self.locked = len(self.join_order) >= JOIN_LIMIT
                    return True
        return False

    def start_game(self, starter_id: int) -> bool:
        if starter_id != self.host_id:
            return False
        # require both teams full
        for t in self.teams.values():
            if any(s is None for s in t.slots.values()):
                return False
        self.active = True
        self.move_count = 0
        # default possession to team 1's PG
        self.current_possession_team = 1
        self.current_attacker_pos = 'pg'
        return True

    def start_toss(self):
        self.toss_active = True
        self.toss_choices = {}

    def set_toss_choice(self, team_id:int, choice:str):
        if not self.toss_active:
            return False
        if team_id not in (1,2):
            return False
        if choice not in ('high','low'):
            return False
        self.toss_choices[team_id] = choice
        return True

    def resolve_toss(self, pick:str) -> Optional[int]:
        # pick is 'high' or 'low'
        if not self.toss_active:
            return None
        self.toss_active = False
        # find a matching team
        winners = [tid for tid,ch in self.toss_choices.items() if ch == pick]
        if len(winners) == 1:
            return winners[0]
        # tie or none — pick random later by caller
        return None

    def end_game(self):
        self.active = False

    def make_sub_request(self, team_id: int, out_pos: str, in_user_id:int, in_name:str) -> SubRequest:
        req = SubRequest(team=team_id, out_pos=out_pos, in_user_id=in_user_id, in_name=in_name)
        self.sub_requests[in_user_id] = req
        return req

    def complete_sub(self, in_user_id:int, accept:bool) -> bool:
        req = self.sub_requests.pop(in_user_id, None)
        if not req:
            return False
        if not accept:
            return False
        # perform sub
        team = self.teams[req.team]
        team.slots[req.out_pos] = PlayerSlot(user_id=req.in_user_id, name=req.in_name, position=req.out_pos)
        return True

    def set_possession(self, team_id:int, attacker_pos:str='pg'):
        self.current_possession_team = team_id
        self.current_attacker_pos = attacker_pos

    def get_slot(self, team_id:int, pos:str) -> Optional[PlayerSlot]:
        return self.teams[team_id].slots.get(pos)

    def find_team_of_user(self, user_id:int) -> Optional[int]:
        for tid, t in self.teams.items():
            for p, s in t.slots.items():
                if s and s.user_id == user_id:
                    return tid
        return None

    def mark_afk(self, user_id:int):
        for t in self.teams.values():
            for s in t.slots.values():
                if s and s.user_id == user_id:
                    s.afk = True

    def clear_afk(self, user_id:int):
        for t in self.teams.values():
            for s in t.slots.values():
                if s and s.user_id == user_id:
                    s.afk = False

    def opponent_team(self, team_id:int) -> int:
        return 1 if team_id == 2 else 2

    def increment_move(self):
        self.move_count += 1
        # halftime handling can be done outside
        if self.move_count >= MAX_MOVES:
            self.active = False

    def is_halftime(self):
        return self.move_count == HALFTIME

    def check_overtime_needed(self):
        # called after MAX_MOVES
        return self.move_count >= MAX_MOVES and self.teams[1].score == self.teams[2].score

    def score_points(self, team_id:int, pts:int):
        self.teams[team_id].score += pts

    def get_livescore(self):
        data = {'move': self.move_count, 'teams':{}}
        for tid, t in self.teams.items():
            # determine captain name if present in slots
            cap_name = None
            if t.captain_id is not None:
                for s in t.slots.values():
                    if s and s.user_id == t.captain_id:
                        cap_name = s.name
                        break
            data['teams'][tid] = {
                'name': t.name,
                'score': t.score,
                'captain_id': t.captain_id,
                'captain_name': cap_name,
                'slots': {p:(s.name if s else None) for p,s in t.slots.items()}
            }
        return data
