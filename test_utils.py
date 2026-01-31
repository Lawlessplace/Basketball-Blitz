"""
Test utilities for Basketball Blitz.
Add these as debug/test commands during development.
"""

def create_test_commands(bot, games):
    """Create test commands as a cog."""
    from discord.ext import commands
    from game_core import GameState
    from persistence import save_game, delete_game
    import discord
    
    class TestCommands(commands.Cog):
        def __init__(self, bot):
            self.bot = bot
        
        @commands.command(name='test_reset')
        @commands.is_owner()
        async def test_reset(self, ctx):
            """Reset all games (owner-only, for testing)."""
            gid = ctx.guild.id
            if gid in games:
                games.pop(gid)
                delete_game(gid)
            await ctx.send('✅ Game reset.')
        
        @commands.command(name='test_state')
        @commands.is_owner()
        async def test_state(self, ctx):
            """Display current game state (owner-only)."""
            gid = ctx.guild.id
            if gid not in games:
                await ctx.send('No game.')
                return
            gs = games[gid]
            msg = f"**Game State**\n"
            msg += f"Active: {gs.active}\n"
            msg += f"Move: {gs.move_count}/36\n"
            msg += f"Possession: Team {gs.current_possession_team} at {gs.current_attacker_pos}\n"
            msg += f"Toss Active: {gs.toss_active}\n"
            for tid, team in gs.teams.items():
                msg += f"\nTeam {tid}: {team.score}\n"
                for pos, slot in team.slots.items():
                    name = slot.name if slot else "EMPTY"
                    afk = " (AFK)" if slot and slot.afk else ""
                    msg += f"  {pos.upper()}: {name}{afk}\n"
            await ctx.send(msg)
        
        @commands.command(name='test_advance')
        @commands.is_owner()
        async def test_advance(self, ctx, moves: int = 1):
            """Advance move counter (owner-only)."""
            gid = ctx.guild.id
            if gid not in games:
                await ctx.send('No game.')
                return
            gs = games[gid]
            gs.move_count += moves
            save_game(gid, gs)
            await ctx.send(f'✅ Advanced {moves} moves. Now at {gs.move_count}.')
        
        @commands.command(name='test_score')
        @commands.is_owner()
        async def test_score(self, ctx, team: int, points: int):
            """Award points to a team (owner-only)."""
            gid = ctx.guild.id
            if gid not in games:
                await ctx.send('No game.')
                return
            gs = games[gid]
            if team not in gs.teams:
                await ctx.send('Invalid team.')
                return
            gs.score_points(team, points)
            save_game(gid, gs)
            await ctx.send(f'✅ Team {team} scored {points}. Total: {gs.teams[team].score}')
        
        @commands.command(name='test_possession')
        @commands.is_owner()
        async def test_possession(self, ctx, team: int, pos: str):
            """Set possession (owner-only)."""
            gid = ctx.guild.id
            if gid not in games:
                await ctx.send('No game.')
                return
            gs = games[gid]
            if team not in (1, 2) or pos not in ('pg', 'sg', 'ce'):
                await ctx.send('Invalid team/pos.')
                return
            gs.set_possession(team, pos)
            save_game(gid, gs)
            await ctx.send(f'✅ Possession: Team {team} {pos.upper()}')
    
    return TestCommands(bot)
