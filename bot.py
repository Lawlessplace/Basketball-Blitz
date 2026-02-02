import os
import asyncio
import logging
from dotenv import load_dotenv
import discord
from discord import app_commands
from discord.ext import commands
from game_core import GameState
from typing import Dict, Optional
import random
from persistence import init_db, save_game, load_game, delete_game, list_games

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

logging.basicConfig(level=logging.INFO)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# single game per guild
games: Dict[int, GameState] = {}

def match_guess(att_choice: str, guess: str) -> bool:
    if not att_choice:
        return False
    a = att_choice.lower()
    g = guess.lower()
    if '3' in a or 'halfcourt' in a or 'fullcourt' in a:
        return g in ('3-pointer', '3 pointer', 'halfcourt', 'fullcourt', '3')
    if 'dribble' in a:
        return g in ('dribble',)
    # suffix match: 'pg_dribble_layup' matches 'layup'
    if a.endswith(g.replace(' ', '_')) or a == g:
        return True
    return False


class SubAcceptView(discord.ui.View):
    def __init__(self, gs: GameState, target_user_id: int):
        super().__init__(timeout=15)
        self.gs = gs
        self.target_user_id = target_user_id

    @discord.ui.select(placeholder='Accept sub?', min_values=1, max_values=1, options=[
        discord.SelectOption(label='Accept', value='accept'),
        discord.SelectOption(label='Decline', value='decline')
    ])
    async def select_callback(self, select: discord.ui.Select, interaction: discord.Interaction):
        if interaction.user.id != self.target_user_id:
            await interaction.response.send_message('This prompt is not for you.', ephemeral=True)
            return
        choice = select.values[0]
        accepted = choice == 'accept'
        result = self.gs.complete_sub(interaction.user.id, accepted)
        if accepted and result:
            await interaction.response.edit_message(content='Sub accepted and completed.', view=None)
        else:
            await interaction.response.edit_message(content='Sub declined or failed.', view=None)


class AttackerChoiceView(discord.ui.View):
    def __init__(self, gs: GameState, attacker_id: int, team: int, pos: str):
        super().__init__(timeout=30)
        self.gs = gs
        self.attacker_id = attacker_id
        self.team = team
        self.pos = pos

    @discord.ui.select(placeholder='Choose action', min_values=1, max_values=1, options=[])
    async def select_callback(self, select: discord.ui.Select, interaction: discord.Interaction):
        if interaction.user.id != self.attacker_id:
            await interaction.response.send_message('Not your action to take.', ephemeral=True)
            return
        choice = select.values[0]
        await interaction.response.edit_message(content=f'You chose: {choice}', view=None)
        opp = self.gs.opponent_team(self.team)
        ce = self.gs.get_slot(opp, 'ce')
        if not ce:
            pts = 3 if '3' in choice else 2
            self.gs.score_points(self.team, pts)
            self.gs.increment_move()
            await interaction.followup.send(f'No defender present — scored {pts} points.')
            return
        self.gs._last_att_choice = choice
        view = DefenderGuessView(self.gs, ce.user_id, self.team, choice)
        await interaction.followup.send(f'<@{ce.user_id}>, attacker chose an action — make your guess.', view=view)

    async def on_timeout(self):
        self.gs.mark_afk(self.attacker_id)
        self.gs.set_possession(self.gs.opponent_team(self.team))

    @classmethod
    def create_for(cls, gs: GameState, attacker_id: int, team: int, pos: str):
        view = cls(gs, attacker_id, team, pos)
        options = []
        if pos == 'pg':
            options = [
                discord.SelectOption(label='Side-pass to SG', value='sidepass'),
                discord.SelectOption(label='Dribble → Layup', value='pg_dribble_layup'),
                discord.SelectOption(label='Dribble → Jump shot', value='pg_dribble_jump'),
                discord.SelectOption(label='Halfcourt shot (PG)', value='pg_half'),
                discord.SelectOption(label='Fullcourt shot (PG)', value='pg_full'),
                discord.SelectOption(label='Hold (bounce pass)', value='hold'),
                discord.SelectOption(label='Play back', value='play_back')
            ]
        elif pos == 'sg':
            options = [
                discord.SelectOption(label='Dribble → Layup', value='sg_dribble_layup'),
                discord.SelectOption(label='Dribble → Dunk', value='sg_dribble_dunk'),
                discord.SelectOption(label='3-pointer Halfcourt', value='sg_3_half'),
                discord.SelectOption(label='3-pointer Fullcourt', value='sg_3_full')
            ]
        else:
            options = [discord.SelectOption(label='Action', value='action')]
        sel = None
        for child in view.children:
            if isinstance(child, discord.ui.Select):
                sel = child
                break
        if sel:
            sel.options = options
        return view


class DefenderGuessView(discord.ui.View):
    def __init__(self, gs: GameState, defender_id: int, attacking_team: int, att_choice: str):
        super().__init__(timeout=30)
        self.gs = gs
        self.defender_id = defender_id
        self.attacking_team = attacking_team
        self.att_choice = att_choice

    @discord.ui.select(placeholder='Make your guess', min_values=1, max_values=1, options=[
        discord.SelectOption(label='3-pointer', value='3-pointer'),
        discord.SelectOption(label='dribble', value='dribble'),
        discord.SelectOption(label='sidepass', value='sidepass'),
        discord.SelectOption(label='layup', value='layup'),
        discord.SelectOption(label='dunk', value='dunk'),
        discord.SelectOption(label='halfcourt', value='halfcourt'),
        discord.SelectOption(label='fullcourt', value='fullcourt'),
        discord.SelectOption(label='jump shot', value='jump shot'),
    ])
    async def select_callback(self, select: discord.ui.Select, interaction: discord.Interaction):
        if interaction.user.id != self.defender_id:
            await interaction.response.send_message('This prompt is not for you.', ephemeral=True)
            return
        guess = select.values[0]
        await interaction.response.edit_message(content=f'You guessed: {guess}', view=None)
        if match_guess(self.att_choice, guess):
            self.gs.set_possession(self.gs.opponent_team(self.attacking_team), 'ce')
            self.gs.increment_move()
            await interaction.followup.send('Defence guessed correctly — possession to defence (CE).')
            return
        # incorrect
        if self.att_choice == 'sidepass':
            sg = self.gs.get_slot(self.attacking_team, 'sg')
            if not sg:
                pts = 2
                self.gs.score_points(self.attacking_team, pts)
                self.gs.increment_move()
                await interaction.followup.send('SG not present; automatic score for attacker.')
                return
            sg_view = SGChoiceView.create_for(self.gs, sg.user_id, self.attacking_team)
            await interaction.followup.send(f'<@{sg.user_id}>, you received a sidepass — choose your shot.', view=sg_view)
            return
        save_view = SaveAttemptView(self.gs, self.gs.opponent_team(self.attacking_team), self.attacking_team, self.att_choice)
        await interaction.followup.send('Incorrect guess — centre attempt a save.', view=save_view)

    async def on_timeout(self):
        # treat as incorrect guess
        if self.att_choice == 'sidepass':
            sg = self.gs.get_slot(self.attacking_team, 'sg')
            if sg:
                sg_view = SGChoiceView.create_for(self.gs, sg.user_id, self.attacking_team)
                # best-effort channel send
                return
            else:
                pts = 2
                self.gs.score_points(self.attacking_team, pts)
                self.gs.increment_move()
                return
        save_view = SaveAttemptView(self.gs, self.gs.opponent_team(self.attacking_team), self.attacking_team, self.att_choice)


class SGChoiceView(discord.ui.View):
    def __init__(self, gs: GameState, sg_id: int, team: int):
        super().__init__(timeout=30)
        self.gs = gs
        self.sg_id = sg_id
        self.team = team

    @discord.ui.select(placeholder='Choose SG shot', min_values=1, max_values=1, options=[])
    async def select_callback(self, select: discord.ui.Select, interaction: discord.Interaction):
        if interaction.user.id != self.sg_id:
            await interaction.response.send_message('This prompt is not for you.', ephemeral=True)
            return
        choice = select.values[0]
        await interaction.response.edit_message(content=f'SG chose: {choice}', view=None)
        ce = self.gs.get_slot(self.gs.opponent_team(self.team), 'ce')
        if not ce:
            pts = 3 if '3' in choice else 2
            self.gs.score_points(self.team, pts)
            self.gs.increment_move()
            return
        save_view = SaveAttemptView(self.gs, ce.user_id, self.team, choice)
        await interaction.followup.send('Centre, attempt a save on the SG shot.', view=save_view)

    @classmethod
    def create_for(cls, gs: GameState, sg_id: int, team: int):
        view = cls(gs, sg_id, team)
        options = [
            discord.SelectOption(label='Dribble → Layup', value='sg_dribble_layup'),
            discord.SelectOption(label='Dribble → Dunk', value='sg_dribble_dunk'),
            discord.SelectOption(label='3-pointer Halfcourt', value='sg_3_half'),
            discord.SelectOption(label='3-pointer Fullcourt', value='sg_3_full')
        ]
        sel = None
        for child in view.children:
            if isinstance(child, discord.ui.Select):
                sel = child
                break
        if sel:
            sel.options = options
        return view


class SaveAttemptView(discord.ui.View):
    def __init__(self, gs: GameState, ce_id: int, attacking_team: int, att_choice: str):
        super().__init__(timeout=30)
        self.gs = gs
        self.ce_id = ce_id
        self.attacking_team = attacking_team
        self.att_choice = att_choice

    @discord.ui.select(placeholder='Attempt save (guess shot type)', min_values=1, max_values=1, options=[
        discord.SelectOption(label='3-pointer', value='3-pointer'),
        discord.SelectOption(label='layup', value='layup'),
        discord.SelectOption(label='dunk', value='dunk'),
        discord.SelectOption(label='dribble', value='dribble')
    ])
    async def select_callback(self, select: discord.ui.Select, interaction: discord.Interaction):
        if interaction.user.id != self.ce_id:
            await interaction.response.send_message('This prompt is not for you.', ephemeral=True)
            return
        guess = select.values[0]
        await interaction.response.edit_message(content=f'You attempted save: {guess}', view=None)
        if match_guess(self.att_choice, guess):
            self.gs.set_possession(self.gs.opponent_team(self.attacking_team), 'ce')
            self.gs.increment_move()
            await interaction.followup.send('Save successful — CE gains possession.')
            return
        pts = 3 if '3' in self.att_choice else 2
        self.gs.score_points(self.attacking_team, pts)
        self.gs.increment_move()
        self.gs.set_possession(self.gs.opponent_team(self.attacking_team), 'pg')
        await interaction.followup.send(f'Shot scored for {pts} points. Possession to opposing PG.')

    async def on_timeout(self):
        pts = 3 if '3' in self.att_choice else 2
        self.gs.score_points(self.attacking_team, pts)
        self.gs.increment_move()
        self.gs.set_possession(self.gs.opponent_team(self.attacking_team), 'pg')


class MyBot(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name='newgame')
    async def newgame(self, interaction: discord.Interaction):
        gid = interaction.guild_id or 0
        if gid in games and games[gid].active:
            await interaction.response.send_message('A game is already active in this server.', ephemeral=True)
            return
        gs = GameState(interaction.user.id)
        games[gid] = gs
        # auto-join the host as first player
        res = gs.join_player(interaction.user.id, interaction.user.display_name)
        save_game(gid, gs)
        if res:
            await interaction.response.send_message(f'Lobby created. Host joined as {res}. Players may now `/join`.')
        else:
            await interaction.response.send_message('Lobby created. (Host could not auto-join.) Players may now `/join`.')

    @app_commands.command(name='join')
    async def join(self, interaction: discord.Interaction):
        gid = interaction.guild_id or 0
        if gid not in games:
            await interaction.response.send_message('No lobby. Use `/newgame` to create one.', ephemeral=True)
            return
        gs = games[gid]
        res = gs.join_player(interaction.user.id, interaction.user.display_name)
        if not res:
            await interaction.response.send_message('Could not join — maybe already joined, or lobby full/locked.', ephemeral=True)
            return
        save_game(gid, gs)
        await interaction.response.send_message(f'Joined as {res}.')

    @app_commands.command(name='leave')
    async def leave(self, interaction: discord.Interaction):
        gid = interaction.guild_id or 0
        if gid not in games:
            await interaction.response.send_message('No lobby.', ephemeral=True)
            return
        gs = games[gid]
        ok = gs.leave_player(interaction.user.id)
        if ok:
            save_game(gid, gs)
            await interaction.response.send_message('You left the lobby.')
        else:
            await interaction.response.send_message('Could not leave (game active or not in lobby).', ephemeral=True)

    @app_commands.command(name='livescore')
    async def livescore(self, interaction: discord.Interaction):
        gid = interaction.guild_id or 0
        if gid not in games:
            await interaction.response.send_message('No game/lobby.', ephemeral=True)
            return
        gs = games[gid]
        data = gs.get_livescore()
        msg = f"Move: {data['move']}\n"
        for tid, t in data['teams'].items():
            cap = t.get('captain_name') or 'None'
            msg += f"Team {tid} ({t['name']}) — Captain: {cap} — Score: {t['score']} — PG: {t['slots']['pg']}, SG: {t['slots']['sg']}, CE: {t['slots']['ce']}\n"
        await interaction.response.send_message(msg)

    @app_commands.command(name='cc')
    @app_commands.describe(new_captain='Member to transfer captaincy to')
    async def cc(self, interaction: discord.Interaction, new_captain: discord.Member):
        """Transfer your team captaincy to another team member."""
        gid = interaction.guild_id or 0
        if gid not in games:
            await interaction.response.send_message('No lobby/game.', ephemeral=True)
            return
        gs = games[gid]
        caller_team = None
        for tid, team in gs.teams.items():
            if team.captain_id == interaction.user.id:
                caller_team = tid
                break
        if caller_team is None:
            await interaction.response.send_message('You are not a captain on any team.', ephemeral=True)
            return
        # ensure target is on the same team
        if gs.find_team_of_user(new_captain.id) != caller_team:
            await interaction.response.send_message('Target user is not on your team.', ephemeral=True)
            return
        gs.teams[caller_team].captain_id = new_captain.id
        save_game(gid, gs)
        await interaction.response.send_message(f'{new_captain.display_name} is now captain of Team {caller_team}.')

    @app_commands.command(name='start')
    async def start(self, interaction: discord.Interaction):
        """Start the game (host only). Teams must be full."""
        gid = interaction.guild_id or 0
        if gid not in games:
            await interaction.response.send_message('No lobby.', ephemeral=True)
            return
        gs = games[gid]
        ok = gs.start_game(interaction.user.id)
        if not ok:
            await interaction.response.send_message('Only host can start or teams not filled.', ephemeral=True)
            return
        save_game(gid, gs)
        await interaction.response.send_message('Game started! Use `/toss` to begin coin toss.')

    @app_commands.command(name='toss')
    async def toss(self, interaction: discord.Interaction):
        """Start the coin toss for possession."""
        gid = interaction.guild_id or 0
        if gid not in games or not games[gid].active:
            await interaction.response.send_message('No active game.', ephemeral=True)
            return
        gs = games[gid]
        gs.start_toss()
        save_game(gid, gs)
        await interaction.response.send_message('**Coin Toss Started:** Both teams, choose HIGH or LOW. Use `/tosschoose`.')

    @app_commands.command(name='tosschoose')
    @app_commands.describe(team='Your team number (1 or 2)', choice='HIGH or LOW')
    async def tosschoose(self, interaction: discord.Interaction, team: int, choice: str):
        """Team captains choose high or low for toss."""
        gid = interaction.guild_id or 0
        if gid not in games or not games[gid].active:
            await interaction.response.send_message('No active game.', ephemeral=True)
            return
        gs = games[gid]
        team_obj = gs.teams.get(team)
        if not team_obj or team_obj.captain_id != interaction.user.id:
            await interaction.response.send_message('Only team captain can choose.', ephemeral=True)
            return
        c = choice.lower()
        if c not in ('high', 'low'):
            await interaction.response.send_message('Choose HIGH or LOW.', ephemeral=True)
            return
        ok = gs.set_toss_choice(team, c)
        if not ok:
            await interaction.response.send_message('Toss not active or invalid team.', ephemeral=True)
            return
        await interaction.response.send_message(f'Team {team} chose {c.upper()}.')
        # Check if both teams have chosen
        if len(gs.toss_choices) == 2:
            pick = random.choice(['high', 'low'])
            winner = gs.resolve_toss(pick)
            if winner:
                gs.set_possession(winner, 'pg')
            else:
                winner = random.choice([1, 2])
                gs.set_possession(winner, 'pg')
            save_game(gid, gs)
            await interaction.channel.send(f'**Toss Result: {pick.upper()}** → Team {winner} gets possession at PG. Use `/ctn` to start play.')

    @app_commands.command(name='ctn')
    async def ctn(self, interaction: discord.Interaction):
        """Continue to next attacker's turn."""
        gid = interaction.guild_id or 0
        if gid not in games or not games[gid].active:
            await interaction.response.send_message('No active game.', ephemeral=True)
            return
        gs = games[gid]
        team = gs.current_possession_team
        pos = gs.current_attacker_pos
        if not team or not pos:
            await interaction.response.send_message('No active possession.', ephemeral=True)
            return
        # Check halftime
        if gs.is_halftime():
            await interaction.channel.send('**HALFTIME** — Score update:')
            data = gs.get_livescore()
            for tid, t in data['teams'].items():
                await interaction.channel.send(f"Team {tid}: {t['score']}")
            await interaction.channel.send('Use `/ctn` to resume second half.')
            await interaction.response.defer()
            return
        # Check end of game
        if not gs.active:
            data = gs.get_livescore()
            await interaction.channel.send('**GAME OVER**')
            for tid, t in data['teams'].items():
                await interaction.channel.send(f"Team {tid} final score: {t['score']}")
            if gs.check_overtime_needed():
                await interaction.channel.send('**SUDDEN DEATH OVERTIME** — Continue with next possession!')
                gs.move_count = 36  # reset for OT
                gs.active = True
                save_game(gid, gs)
            await interaction.response.defer()
            return
        attacker = gs.get_slot(team, pos)
        if not attacker:
            await interaction.response.send_message(f'{pos.upper()} not present on Team {team}.', ephemeral=True)
            return
        view = AttackerChoiceView.create_for(gs, attacker.user_id, team, pos)
        await interaction.channel.send(f'<@{attacker.user_id}>, you are attacking as {pos.upper()}. Choose your action.', view=view)
        await interaction.response.defer()

    @app_commands.command(name='sub')
    @app_commands.describe(team='Team number (1 or 2)', position='Position to replace: pg/sg/ce', player='User to sub in')
    async def sub(self, interaction: discord.Interaction, team: int, position: str, player: discord.Member):
        gid = interaction.guild_id or 0
        if gid not in games:
            await interaction.response.send_message('No lobby/game.', ephemeral=True)
            return
        gs = games[gid]
        team_obj = gs.teams.get(team)
        if not team_obj or team_obj.captain_id != interaction.user.id:
            await interaction.response.send_message('Only the team captain can initiate subs.', ephemeral=True)
            return
        gs.make_sub_request(team, position, player.id, player.display_name)
        save_game(gid, gs)
        view = SubAcceptView(gs, player.id)
        await interaction.response.send_message(f'{player.mention}, you have a sub request to join {team} as {position}. Accept?', view=view)

    @app_commands.command(name='yeet')
    async def yeet(self, interaction: discord.Interaction):
        gid = interaction.guild_id or 0
        if gid not in games:
            await interaction.response.send_message('No game.', ephemeral=True)
            return
        gs = games.pop(gid)
        gs.end_game()
        await interaction.response.send_message('Game ended.')


@bot.event
async def on_ready():
    print('Bot ready')
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} commands')
    except Exception as e:
        print('Sync failed', e)


async def setup():
    await bot.add_cog(MyBot(bot))


if __name__ == '__main__':
    async def main():
        # Ensure DB schema exists before commands run
        init_db()
        await setup()
        if not TOKEN:
            print('DISCORD_TOKEN not set. create a .env file or set env var DISCORD_TOKEN')
            return
        await bot.start(TOKEN)

    asyncio.run(main())
@commands.Cog.listener()
async def setup(self):
    pass

# Add these inside your MyBot class

@app_commands.command(name='kick')
@app_commands.describe(user='User to kick from the game')
async def kick(self, interaction: discord.Interaction, user: discord.Member):
    gid = interaction.guild_id or 0
    if gid not in games:
        await interaction.response.send_message('No game in progress.', ephemeral=True)
        return
    gs = games[gid]
    # Check if the interaction user is the host (creator)
    host_id = getattr(gs, 'host_id', None)
    if host_id != interaction.user.id:
        await interaction.response.send_message('Only the host can kick players.', ephemeral=True)
        return
    # Remove the user from game
    result = gs.leave_player(user.id)
    if result:
        save_game(gid, gs)
        await interaction.response.send_message(f'{user.display_name} has been kicked from the game.')
    else:
        await interaction.response.send_message('User not in game or cannot be kicked.', ephemeral=True)

@app_commands.command(name='cc')  # Transfer captaincy
@app_commands.describe(new_captain='Member to transfer captaincy to')
async def cc(self, interaction: discord.Interaction, new_captain: discord.Member):
    """Transfer your team captaincy to another team member."""
    gid = interaction.guild_id or 0
    if gid not in games:
        await interaction.response.send_message('No lobby/game.', ephemeral=True)
        return
    gs = games[gid]
    caller_team = None
    for tid, team in gs.teams.items():
        if team.captain_id == interaction.user.id:
            caller_team = tid
            break
    if caller_team is None:
        await interaction.response.send_message('You are not a captain on any team.', ephemeral=True)
        return
    # ensure target is on the same team
    if gs.find_team_of_user(new_captain.id) != caller_team:
        await interaction.response.send_message('Target user is not on your team.', ephemeral=True)
        return
    gs.teams[caller_team].captain_id = new_captain.id
    save_game(gid, gs)
    await interaction.response.send_message(f'{new_captain.display_name} is now captain of Team {caller_team}.')

@app_commands.command(name='start')
async def start(self, interaction: discord.Interaction):
    gid = interaction.guild_id or 0
    if gid not in games:
        await interaction.response.send_message('No lobby.', ephemeral=True)
        return
    gs = games[gid]
    ok = gs.start_game(interaction.user.id)
    if not ok:
        await interaction.response.send_message('Only host can start the game or teams are not filled.', ephemeral=True)
        return
    save_game(gid, gs)
    await interaction.response.send_message('Game started! Use `/toss` to begin coin toss.')

@app_commands.command(name='join')
async def join(self, interaction: discord.Interaction):
    gid = interaction.guild_id or 0
    if gid not in games:
        await interaction.response.send_message('No lobby created. Use `/newgame` to create one.', ephemeral=True)
        return
    gs = games[gid]
    # Check if the lobby already has 6 players
    if len(gs.players) >= 6:
        await interaction.response.send_message('Lobby is full .', ephemeral=True)
        return
    res = gs.join_player(interaction.user.id, interaction.user.display_name)
    if not res:
        await interaction.response.send_message('Could not join, maybe you have already joined, or the lobby is full.', ephemeral=True)
        return
    save_game(gid, gs)
    await interaction.response.send_message(f'Joined as {res}.')