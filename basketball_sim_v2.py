#!/usr/bin/env python3
"""
Classic NBA Text Basketball Simulation
A nostalgic recreation of text-based basketball games
"""

import random
import time
import csv
import sys
import tty
import termios
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.layout import Layout
from rich import box
from rich.prompt import Prompt

console = Console()


def getch():
    """Get a single character from user input without requiring ENTER"""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

@dataclass
class Player:
    """Represents a basketball player with stats"""
    name: str
    fg_pct: float  # Field goal percentage (0-100)
    ft_pct: float  # Free throw percentage (0-100)
    rpg: float     # Rebounds per game
    apg: float     # Assists per game
    position: str  # Position
    two_pt_pct: float = 0.0  # Two-point percentage (0-100)
    three_pt_pct: float = 0.0  # Three-point percentage (0-100)
    minutes_pg: float = 24.0  # Minutes per game
    ppg: float = 5.0  # Points per game (for shot selection weighting)
    fta_pg: float = 2.0  # Free throw attempts per game (for foul probability weighting)
    usage_rate: float = 20.0  # Usage rate - % of team possessions used when player is on floor

    # Game stats (will be updated during simulation)
    points: int = 0
    rebounds: int = 0
    assists: int = 0
    fga: int = 0  # Field goal attempts
    fgm: int = 0  # Field goals made
    ftm: int = 0  # Free throws made
    fta: int = 0  # Free throw attempts
    fouls: int = 0  # Personal fouls (0-6, foul out at 6)
    steals: int = 0  # Steals (defensive stat)
    blocks: int = 0  # Blocks (defensive stat)
    turnovers: int = 0  # Turnovers (offensive stat)
    minutes_played: float = 0.0  # Minutes played in current game
    game_target_minutes: float = 0.0  # Target minutes for this specific game (sampled from distribution)
    
    def attempt_shot(self, def_rating: float = 1.0) -> bool:
        """Attempt a two-point field goal based on player's shooting percentage"""
        self.fga += 1
        effective_pct = self.two_pt_pct * def_rating
        made = random.random() * 100 < effective_pct
        if made:
            self.fgm += 1
            self.points += 2
        return made

    def attempt_three(self, def_rating: float = 1.0) -> bool:
        """Attempt a three-pointer based on player's three-point percentage"""
        self.fga += 1
        effective_pct = self.three_pt_pct * def_rating
        made = random.random() * 100 < effective_pct
        if made:
            self.fgm += 1
            self.points += 3
        return made
    
    def attempt_free_throw(self) -> bool:
        """Attempt a free throw"""
        self.fta += 1
        made = random.random() * 100 < self.ft_pct
        if made:
            self.ftm += 1
            self.points += 1
        return made
    
    def get_rebound(self):
        """Record a rebound"""
        self.rebounds += 1
    
    def get_assist(self):
        """Record an assist"""
        self.assists += 1

    def reset_stats(self):
        """Reset all game stats (for new game)"""
        self.points = 0
        self.rebounds = 0
        self.assists = 0
        self.fga = 0
        self.fgm = 0
        self.ftm = 0
        self.fta = 0
        self.fouls = 0
        self.steals = 0
        self.blocks = 0
        self.turnovers = 0
        self.minutes_played = 0.0


@dataclass
class Team:
    """Represents a basketball team"""
    name: str
    players: List[Player]
    pace_rating: float = 1.0
    three_pt_rate: float = 0.25
    def_rating: float = 1.0
    year: int = 2000
    score: int = 0
    team_fouls: int = 0  # Team fouls in current quarter (resets each quarter)
    on_court_indices: List[int] = None

    def __post_init__(self):
        """Initialize on-court players - select top 5 by PPG as starters"""
        if self.on_court_indices is None:
            # Select starting 5: Top 5 players by PPG
            player_indices = [(i, p.ppg) for i, p in enumerate(self.players)]
            player_indices.sort(key=lambda x: -x[1])  # Sort by PPG descending
            self.on_court_indices = [idx for idx, _ in player_indices[:5]]

    def get_minutes_std_dev(self, minutes_pg: float) -> float:
        """Calculate standard deviation for minutes distribution based on player tier"""
        if minutes_pg >= 35:
            return 1.5  # Superstars: very consistent (e.g., Jordan 36-40 min)
        elif minutes_pg >= 20:
            return 2.5  # Starters & elite 6th men: consistent (e.g., starter/Manu 20-33 min)
        elif minutes_pg >= 12:
            return 3.5  # Role players: variable (matchup dependent)
        else:
            return 2.5  # Deep bench: capped variance (prevent 10 MPG players from playing 20+)

    def reset_for_new_game(self):
        """Reset all stats and lineup for a new game"""
        # Reset all player stats
        for player in self.players:
            player.reset_stats()
            # Sample game-specific target minutes from normal distribution
            std_dev = self.get_minutes_std_dev(player.minutes_pg)
            # Sample from N(minutes_pg, std_dev), clamped to reasonable bounds
            sampled_minutes = random.gauss(player.minutes_pg, std_dev)
            # Clamp between 0 and 48 minutes
            player.game_target_minutes = max(0, min(48, sampled_minutes))
        # Reset to starting lineup (top 5 by PPG)
        player_indices = [(i, p.ppg) for i, p in enumerate(self.players)]
        player_indices.sort(key=lambda x: -x[1])  # Sort by PPG descending
        self.on_court_indices = [idx for idx, _ in player_indices[:5]]
        # Reset team score and fouls
        self.score = 0
        self.team_fouls = 0

    def reset_quarter_fouls(self):
        """Reset team fouls at the start of each quarter"""
        self.team_fouls = 0

    def get_team_totals(self) -> dict:
        """Calculate team aggregate statistics"""
        totals = {
            'fgm': 0,
            'fga': 0,
            'ftm': 0,
            'fta': 0,
            'reb': 0,
            'ast': 0,
            'stl': 0,
            'blk': 0,
            'to': 0
        }

        for player in self.players:
            totals['fgm'] += player.fgm
            totals['fga'] += player.fga
            totals['ftm'] += player.ftm
            totals['fta'] += player.fta
            totals['reb'] += player.rebounds
            totals['ast'] += player.assists
            totals['stl'] += player.steals
            totals['blk'] += player.blocks
            totals['to'] += player.turnovers

        # Calculate percentages
        totals['fg_pct'] = (totals['fgm'] / totals['fga'] * 100) if totals['fga'] > 0 else 0.0
        totals['ft_pct'] = (totals['ftm'] / totals['fta'] * 100) if totals['fta'] > 0 else 0.0

        return totals

    def check_foul_outs(self):
        """Check if any on-court players have fouled out and substitute them"""
        for i, player_idx in enumerate(self.on_court_indices):
            player = self.players[player_idx]

            # If player has 6+ fouls, they must be substituted
            if player.fouls >= 6:
                # Find a substitute who hasn't fouled out
                best_sub_idx = None
                for bench_idx, bench_player in enumerate(self.players):
                    if bench_idx not in self.on_court_indices and bench_player.fouls < 6:
                        best_sub_idx = bench_idx
                        break  # Take first available non-fouled-out player

                # Make the substitution (or leave them if no subs available)
                if best_sub_idx is not None:
                    self.on_court_indices[i] = best_sub_idx

    def get_position_compatible(self, position: str) -> List[str]:
        """
        Get list of compatible positions for substitutions (in order of preference)

        Position flexibility:
        - PG: Prefers PG, can use SG
        - SG: Prefers SG, can use PG or SF
        - SF: Prefers SF, can use SG or PF (versatile wing/forward)
        - PF: Prefers PF, can use SF or C
        - C: Prefers C, can use PF
        """
        position_map = {
            'PG': ['PG', 'SG'],
            'SG': ['SG', 'PG', 'SF'],
            'SF': ['SF', 'SG', 'PF'],
            'PF': ['PF', 'SF', 'C'],
            'C': ['C', 'PF']
        }
        return position_map.get(position, [position])

    def get_on_court(self) -> List[Player]:
        """Get the 5 players currently on the court (excluding fouled-out players)"""
        # Filter out fouled-out players (6+ fouls)
        return [self.players[i] for i in self.on_court_indices if self.players[i].fouls < 6]

    def substitute_fouled_out_player(self, fouled_out_player: Player) -> Optional[Player]:
        """
        Immediately substitute a fouled-out player (position-aware)
        Returns the substitute player, or None if no substitutes available
        """
        # Find the index of the fouled-out player
        fouled_out_idx = None
        for i, idx in enumerate(self.on_court_indices):
            if self.players[idx] == fouled_out_player:
                fouled_out_idx = i
                break

        if fouled_out_idx is None:
            return None  # Player not found on court

        # Get position-compatible options (in order of preference)
        compatible_positions = self.get_position_compatible(fouled_out_player.position)

        # Try to find position-compatible substitute first
        for position in compatible_positions:
            for bench_idx, bench_player in enumerate(self.players):
                if (bench_idx not in self.on_court_indices and
                    bench_player.fouls < 6 and
                    bench_player.position == position):
                    # Make the substitution
                    self.on_court_indices[fouled_out_idx] = bench_idx
                    return bench_player

        # If no position match found, just take any available player
        for bench_idx, bench_player in enumerate(self.players):
            if bench_idx not in self.on_court_indices and bench_player.fouls < 6:
                # Make the substitution
                self.on_court_indices[fouled_out_idx] = bench_idx
                return bench_player

        # No substitute available - team plays short-handed
        # (This shouldn't happen with 12+ players, but handle gracefully)
        return None

    def get_top_players(self, num_players: int = 5, avoid_foul_trouble: bool = True) -> List[int]:
        """
        Get indices of top players by PPG for clutch time

        Args:
            num_players: Number of top players to return (5 for closing, 7-8 for crunch)
            avoid_foul_trouble: Prefer players without 5+ fouls if possible

        Returns: List of player indices sorted by PPG (descending)
        """
        # Create list of (index, player, ppg, fouls)
        player_list = [(i, p, p.ppg, p.fouls) for i, p in enumerate(self.players)]

        # Sort by: foul trouble (if avoiding), then PPG descending
        if avoid_foul_trouble:
            # Prefer players without 5+ fouls, then by PPG
            player_list.sort(key=lambda x: (x[3] >= 5, -x[2]))
        else:
            # Just sort by PPG
            player_list.sort(key=lambda x: -x[2])

        # Return top N player indices (excluding fouled out players)
        top_indices = []
        for idx, player, ppg, fouls in player_list:
            if fouls < 6:  # Can't play fouled out players
                top_indices.append(idx)
                if len(top_indices) >= num_players:
                    break

        return top_indices

    def update_minutes(self, seconds_played: float):
        """Update minutes played for players on court"""
        minutes = seconds_played / 60.0
        for idx in self.on_court_indices:
            self.players[idx].minutes_played += minutes

    def time_based_substitutions(self, game_minutes_elapsed: float, restrict_to_top: int = None):
        """Perform substitutions based on game flow and player usage

        Strategy:
        - At 6:00 and 3:00 marks each quarter, evaluate all on-court players
        - Sub out players who are ahead of their minute pace
        - Bring in players who are behind their minute pace
        - This creates natural rotation waves like real NBA games

        Args:
            game_minutes_elapsed: Total game time elapsed
            restrict_to_top: If set, only substitute within top N players by PPG (for crunch time)
        """
        # Calculate expected usage at this point in the game (0.0 to 1.0)
        # 48-minute game, so at 12 minutes elapsed = 25% through game
        game_progress = game_minutes_elapsed / 48.0

        # Get restricted player pool if in crunch time
        if restrict_to_top:
            allowed_indices = set(self.get_top_players(restrict_to_top, avoid_foul_trouble=True))
        else:
            allowed_indices = set(range(len(self.players)))

        # Find players to sub out (on court and ahead of pace)
        players_to_sub_out = []
        for i, player_idx in enumerate(self.on_court_indices):
            player = self.players[player_idx]
            if player.game_target_minutes == 0:
                continue

            # How much of their target minutes should they have played by now?
            expected_minutes = player.game_target_minutes * game_progress

            # Are they ahead of pace? Use smaller buffer early in game (0.5 min) to encourage rotation
            # Increase buffer later in game to lock in key players (1.5 min in 4th quarter)
            if game_progress < 0.75:  # First 3 quarters
                buffer = 0.5
            else:  # 4th quarter - tighter rotation
                buffer = 1.5

            if player.minutes_played > expected_minutes + buffer:
                players_to_sub_out.append((i, player_idx, player.minutes_played - expected_minutes))

        # Sort by how far ahead they are (most ahead gets subbed first)
        players_to_sub_out.sort(key=lambda x: x[2], reverse=True)

        # Sub out up to 2-3 players per window (realistic rotation wave)
        max_subs = min(3, len(players_to_sub_out))

        for i in range(max_subs):
            lineup_pos, player_idx, _ = players_to_sub_out[i]

            # Find best substitute: player most behind their minute pace (position-aware)
            player_being_subbed = self.players[player_idx]
            compatible_positions = self.get_position_compatible(player_being_subbed.position)

            best_sub_idx = None
            best_deficit = -999

            # First try: Find position-compatible substitute
            for position in compatible_positions:
                for bench_idx, bench_player in enumerate(self.players):
                    # Skip if not in allowed pool or already on court or wrong position
                    if (bench_idx not in allowed_indices or
                        bench_idx in self.on_court_indices or
                        bench_player.position != position):
                        continue

                    if bench_player.game_target_minutes == 0:
                        continue

                    expected_minutes = bench_player.game_target_minutes * game_progress
                    deficit = expected_minutes - bench_player.minutes_played

                    # Only sub in players who are behind pace (deficit > 0)
                    # and haven't already hit their target
                    if deficit > 0 and bench_player.minutes_played < bench_player.game_target_minutes * 0.99:
                        if deficit > best_deficit:
                            best_sub_idx = bench_idx
                            best_deficit = deficit

                # If we found a substitute at this position level, use it
                if best_sub_idx is not None:
                    break

            # Second try: If no position match, just take best available
            if best_sub_idx is None:
                for bench_idx, bench_player in enumerate(self.players):
                    if bench_idx not in allowed_indices or bench_idx in self.on_court_indices:
                        continue

                    if bench_player.game_target_minutes == 0:
                        continue

                    expected_minutes = bench_player.game_target_minutes * game_progress
                    deficit = expected_minutes - bench_player.minutes_played

                    if deficit > 0 and bench_player.minutes_played < bench_player.game_target_minutes * 0.99:
                        if deficit > best_deficit:
                            best_sub_idx = bench_idx
                            best_deficit = deficit

            # Make the substitution
            if best_sub_idx is not None:
                self.on_court_indices[lineup_pos] = best_sub_idx

    def check_substitutions(self):
        """Emergency substitution check - only subs players who are way over their minutes
        This is a fallback; main rotations should happen via time_based_substitutions()
        """
        for i, player_idx in enumerate(self.on_court_indices):
            player = self.players[player_idx]

            # Calculate how much of their game-specific target minutes they've used
            usage_ratio = player.minutes_played / player.game_target_minutes if player.game_target_minutes > 0 else 0

            # Emergency sub only if player has hit their full target
            if usage_ratio >= 1.0:
                # Find the best substitute: player with lowest usage ratio who isn't on court (position-aware)
                compatible_positions = self.get_position_compatible(player.position)
                best_sub_idx = None
                lowest_usage = 999

                # First try: Find position-compatible substitute
                for position in compatible_positions:
                    for bench_idx, bench_player in enumerate(self.players):
                        if bench_idx not in self.on_court_indices and bench_player.position == position:
                            bench_usage = bench_player.minutes_played / bench_player.game_target_minutes if bench_player.game_target_minutes > 0 else 0
                            if bench_usage < lowest_usage and bench_usage < 0.99:
                                best_sub_idx = bench_idx
                                lowest_usage = bench_usage
                    # If we found a substitute at this position level, use it
                    if best_sub_idx is not None:
                        break

                # Second try: If no position match, just take best available
                if best_sub_idx is None:
                    for bench_idx, bench_player in enumerate(self.players):
                        if bench_idx not in self.on_court_indices:
                            bench_usage = bench_player.minutes_played / bench_player.game_target_minutes if bench_player.game_target_minutes > 0 else 0
                            if bench_usage < lowest_usage and bench_usage < 0.99:
                                best_sub_idx = bench_idx
                                lowest_usage = bench_usage

                # Make the substitution (or leave them if no subs available)
                if best_sub_idx is not None:
                    self.on_court_indices[i] = best_sub_idx
    
    def select_shooter(self) -> Player:
        """Select a player to take the shot (weighted by their scoring volume)"""
        on_court = self.get_on_court()
        # Square PPG to heavily favor high scorers (Jordan, Kobe, etc.)
        # This ensures volume scorers get appropriate shot attempts
        weights = [(p.ppg + 1) ** 2 for p in on_court]
        return random.choices(on_court, weights=weights)[0]
    
    def select_passer(self, exclude: Player = None) -> Player:
        """Select a player to pass (weighted by assists)"""
        on_court = [p for p in self.get_on_court() if p != exclude]
        # Square the APG to heavily favor high-assist players (Magic, etc.)
        weights = [(p.apg + 1) ** 2 for p in on_court]
        return random.choices(on_court, weights=weights)[0]
    
    def select_rebounder(self) -> Player:
        """Select a player to get the rebound"""
        on_court = self.get_on_court()
        weights = [p.rpg + 1 for p in on_court]
        return random.choices(on_court, weights=weights)[0]


class GameSimulation:
    """Simulates a basketball game"""

    def __init__(self, team1: Team, team2: Team, game_speed: float = 0.5):
        self.team1 = team1
        self.team2 = team2
        self.quarter = 1
        self.time_remaining = 720  # 12 minutes in seconds
        self.possession = team1
        self.play_by_play: List[str] = []
        self.game_speed = game_speed  # Seconds between plays
        self.quarter_scores = {
            'team1': [],  # Will store score at end of each quarter
            'team2': []
        }
        self.game_minutes_elapsed = 0.0  # Track total game time for substitution logic
        self.manual_control_team = None  # If set, this team won't get auto-rotations

    def get_era_possession_time(self, year: int) -> Tuple[int, int]:
        """Get base possession time range based on team's era
        Calibrated to produce realistic possession counts:
        - 1960s-70s: ~115 possessions per team
        - 1980s: ~102 possessions per team
        - 1990s-2000s: ~92 possessions per team (slowest)
        - 2010s+: ~100 possessions per team
        """
        if year < 1980:
            # 1960s-70s: Fast pace, run and gun (~230 total possessions)
            return (10, 15)
        elif year < 1990:
            # 1980s: Fast era - Showtime Lakers, Pistons '89 (106.6 PPG) (~204 total)
            return (12, 16)
        elif year < 2010:
            # 1990s-2000s: SLOWEST ERA - defensive grind, ISO-heavy (~184 total)
            return (14, 18)
        else:
            # 2010s+: Modern pace and space (~200 total possessions)
            return (13, 17)

    def is_clutch_time(self) -> Tuple[bool, str]:
        """
        Check if we're in clutch time (close game in Q4/OT)

        Returns: (is_clutch, phase)
        - is_clutch: True if in clutch time
        - phase: "crunch" (8:00-3:00), "closing" (3:00-0:00), or "none"
        """
        # Must be Q4 or OT
        if not (self.quarter == 4 or isinstance(self.quarter, str)):
            return False, "none"

        # Must be within 10 points
        score_diff = abs(self.team1.score - self.team2.score)
        if score_diff > 10:
            return False, "none"

        # Check time remaining
        if self.time_remaining <= 180:  # 3:00 or less
            return True, "closing"
        elif self.time_remaining <= 480:  # 8:00 or less (but more than 3:00)
            return True, "crunch"
        else:
            return False, "none"

    def is_foul_trouble(self, player: Player) -> bool:
        """
        Check if a player is in foul trouble based on current quarter

        Foul trouble thresholds:
        - Q1: 2 fouls (need to preserve for rest of game)
        - Q2: 3 fouls (can't risk more before halftime)
        - Q3: 4 fouls (getting dangerous)
        - Q4: 5 fouls (only sub at 5, unless blowout)
        - Q4 Crunch Time: Stars stay in even with 5 fouls
        - OT: 5 fouls (same as Q4)
        """
        quarter = self.quarter if isinstance(self.quarter, int) else 4  # Treat OT as Q4

        if quarter == 1:
            return player.fouls >= 2
        elif quarter == 2:
            return player.fouls >= 3
        elif quarter == 3:
            return player.fouls >= 4
        else:  # Q4 or OT
            # Q4 Crunch Time: Keep stars in even with 5 fouls
            is_crunch_time = self.time_remaining <= 300  # Last 5 minutes
            is_star = player.minutes_pg >= 32  # Stars play 32+ MPG
            if is_crunch_time and is_star:
                return False  # Never bench stars in crunch time

            # Q4 strategy: Only sub at 5 fouls (one away from fouling out)
            # Exception: In blowouts (>15 pt diff), could sub at 4 to rest starters
            score_diff = abs(self.team1.score - self.team2.score)
            if score_diff > 15:
                return player.fouls >= 4
            else:
                return player.fouls >= 5

    def commit_foul(self, fouling_team: Team, fouled_player: Player) -> Tuple[Player, bool]:
        """
        Commit a foul by the defensive team

        Returns: (fouling_player, fouled_out)
        - fouling_player: The defender who committed the foul
        - fouled_out: True if the fouling player just fouled out (6 fouls)
        """
        # Select random defender from on-court players
        fouling_player = random.choice(fouling_team.get_on_court())

        # Increment personal and team fouls
        fouling_player.fouls += 1
        fouling_team.team_fouls += 1

        # Check if player fouled out (6 fouls)
        fouled_out = fouling_player.fouls >= 6

        return fouling_player, fouled_out
        
    def simulate_possession(self) -> Tuple[str, bool]:
        """
        Simulate a single possession
        Returns: (play description, scored)
        """
        plays = []
        scored = False

        # Random number of passes (0-3)
        num_passes = random.choices([0, 1, 2, 3], weights=[20, 40, 30, 10])[0]

        current_player = None
        last_passer = None  # Track who made the last pass
        for i in range(num_passes):
            passer = self.possession.select_passer(exclude=current_player)
            receiver = self.possession.select_passer(exclude=passer)
            plays.append(f"{passer.name} passes to {receiver.name}")
            last_passer = passer  # Remember who passed
            current_player = receiver

        # Get defending team
        defending_team = self.team2 if self.possession == self.team1 else self.team1

        # Check for turnover (~10% of possessions)
        if random.random() < 0.10:
            ball_handler = self.possession.select_shooter() if current_player is None else current_player

            # 60% of turnovers are steals (defensive player gets credit)
            # 40% are unforced errors (bad pass, traveling, etc.)
            if random.random() < 0.60:
                # STEAL - Credit defensive player
                defender = random.choice(defending_team.get_on_court())
                defender.steals += 1
                ball_handler.turnovers += 1
                plays.append(f"Turnover! {ball_handler.name} loses ball → Steal: {defender.name}")
            else:
                # UNFORCED ERROR
                ball_handler.turnovers += 1
                turnover_types = ["Bad pass", "Traveling", "Offensive foul", "Lost ball"]
                error_type = random.choice(turnover_types)
                plays.append(f"Turnover! {ball_handler.name} - {error_type}")

            return " → ".join(plays), scored

        # Check for non-shooting foul (before shot attempt)
        # 10% chance of non-shooting foul during possession
        if random.random() < 0.10:
            offensive_player = self.possession.select_shooter() if current_player is None else current_player
            fouling_player, fouled_out = self.commit_foul(defending_team, offensive_player)

            plays.append(f"Foul on {fouling_player.name}! (PF{fouling_player.fouls})")

            # Check if player fouled out
            if fouled_out:
                plays.append(f"[bold red]{fouling_player.name} FOULS OUT! (6 fouls)[/bold red]")
                # Immediately substitute the fouled-out player
                substitute = defending_team.substitute_fouled_out_player(fouling_player)
                if substitute:
                    plays.append(f"{substitute.name} enters the game")
            # Check if player is in foul trouble (needs to sit)
            elif self.is_foul_trouble(fouling_player):
                plays.append(f"[yellow]Foul trouble! {fouling_player.name} heads to the bench[/yellow]")
                substitute = defending_team.substitute_fouled_out_player(fouling_player)
                if substitute:
                    plays.append(f"{substitute.name} enters the game")

            # Check bonus situation (5+ team fouls = 2 FTs)
            if defending_team.team_fouls >= 5:
                plays.append(f"Bonus! {offensive_player.name} shoots 2 free throws...")
                ft_results = []
                for i in range(2):
                    ft_made = offensive_player.attempt_free_throw()
                    if ft_made:
                        self.possession.score += 1
                        scored = True
                    ft_results.append('✓' if ft_made else 'X')
                plays.append(f"Free throws: {' '.join(ft_results)}")
            else:
                plays.append(f"Non-shooting foul. {self.possession.name} retains possession.")

            return " → ".join(plays), scored

        # Someone takes a shot
        shooter = self.possession.select_shooter() if current_player is None else current_player
        def_rating = defending_team.def_rating

        # Decide shot type (use team-specific three-point rate)
        three_rate = self.possession.three_pt_rate
        two_rate = 1.0 - three_rate
        shot_type = random.choices(['two', 'three'], weights=[two_rate, three_rate])[0]

        if shot_type == 'three':
            plays.append(f"{shooter.name} shoots a three-pointer...")

            # Check for block (rare on 3PT shots, ~2%)
            blocked = random.random() < 0.02
            if blocked:
                blocker = random.choice(defending_team.get_on_court())
                blocker.blocks += 1
                shooter.fga += 1  # FGA counts even if blocked
                plays.append(f"BLOCKED by {blocker.name}!")
                made = False
                fouled = False  # Can't foul on a clean block
            else:
                made = shooter.attempt_three(def_rating)

                # Check for foul (weighted by FTA per game)
                foul_probability = min(0.3, shooter.fta_pg * 0.02)
                fouled = random.random() < foul_probability

            if made:
                self.possession.score += 3
                scored = True
                plays.append(f"GOOD! Three-pointer!")

                # Possible assist (on three-pointers too!)
                if num_passes > 0 and last_passer and random.random() < 0.7:
                    # Credit the actual last passer
                    last_passer.get_assist()
                    plays.append(f"(Assist: {last_passer.name})")

                # And-1 opportunity if fouled
                if fouled:
                    fouling_player, fouled_out = self.commit_foul(defending_team, shooter)
                    plays.append(f"Fouled by {fouling_player.name}! (PF{fouling_player.fouls}) And-1 opportunity...")
                    if fouled_out:
                        plays.append(f"[bold red]{fouling_player.name} FOULS OUT![/bold red]")
                        # Immediately substitute the fouled-out player
                        substitute = defending_team.substitute_fouled_out_player(fouling_player)
                        if substitute:
                            plays.append(f"{substitute.name} enters the game")
                    elif self.is_foul_trouble(fouling_player):
                        plays.append(f"[yellow]Foul trouble! {fouling_player.name} heads to the bench[/yellow]")
                        substitute = defending_team.substitute_fouled_out_player(fouling_player)
                        if substitute:
                            plays.append(f"{substitute.name} enters the game")
                    ft_made = shooter.attempt_free_throw()
                    if ft_made:
                        self.possession.score += 1
                        plays.append(f"Free throw: GOOD")
                    else:
                        plays.append(f"Free throw: Missed")
            else:
                plays.append("No good!")

                # Shooting foul = 3 free throws
                if fouled:
                    fouling_player, fouled_out = self.commit_foul(defending_team, shooter)
                    plays.append(f"Fouled by {fouling_player.name}! (PF{fouling_player.fouls}) 3 free throws...")
                    if fouled_out:
                        plays.append(f"[bold red]{fouling_player.name} FOULS OUT![/bold red]")
                        # Immediately substitute the fouled-out player
                        substitute = defending_team.substitute_fouled_out_player(fouling_player)
                        if substitute:
                            plays.append(f"{substitute.name} enters the game")
                    elif self.is_foul_trouble(fouling_player):
                        plays.append(f"[yellow]Foul trouble! {fouling_player.name} heads to the bench[/yellow]")
                        substitute = defending_team.substitute_fouled_out_player(fouling_player)
                        if substitute:
                            plays.append(f"{substitute.name} enters the game")
                    ft_results = []
                    for i in range(3):
                        ft_made = shooter.attempt_free_throw()
                        if ft_made:
                            self.possession.score += 1
                        ft_results.append('✓' if ft_made else 'X')
                    plays.append(f"Free throws: {' '.join(ft_results)}")
        else:
            plays.append(f"{shooter.name} shoots...")

            # Check for block (more common on 2PT shots, ~5%)
            blocked = random.random() < 0.05
            if blocked:
                blocker = random.choice(defending_team.get_on_court())
                blocker.blocks += 1
                shooter.fga += 1  # FGA counts even if blocked
                plays.append(f"BLOCKED by {blocker.name}!")
                made = False
                fouled = False  # Can't foul on a clean block
            else:
                made = shooter.attempt_shot(def_rating)

                # Check for foul (weighted by FTA per game)
                foul_probability = min(0.3, shooter.fta_pg * 0.02)
                fouled = random.random() < foul_probability

            if made:
                self.possession.score += 2
                scored = True
                plays.append(f"GOOD!")

                # Possible assist
                if num_passes > 0 and last_passer and random.random() < 0.7:
                    # Credit the actual last passer
                    last_passer.get_assist()
                    plays.append(f"(Assist: {last_passer.name})")

                # And-1 opportunity if fouled
                if fouled:
                    fouling_player, fouled_out = self.commit_foul(defending_team, shooter)
                    plays.append(f"Fouled by {fouling_player.name}! (PF{fouling_player.fouls}) And-1 opportunity...")
                    if fouled_out:
                        plays.append(f"[bold red]{fouling_player.name} FOULS OUT![/bold red]")
                        # Immediately substitute the fouled-out player
                        substitute = defending_team.substitute_fouled_out_player(fouling_player)
                        if substitute:
                            plays.append(f"{substitute.name} enters the game")
                    elif self.is_foul_trouble(fouling_player):
                        plays.append(f"[yellow]Foul trouble! {fouling_player.name} heads to the bench[/yellow]")
                        substitute = defending_team.substitute_fouled_out_player(fouling_player)
                        if substitute:
                            plays.append(f"{substitute.name} enters the game")
                    ft_made = shooter.attempt_free_throw()
                    if ft_made:
                        self.possession.score += 1
                        plays.append(f"Free throw: GOOD")
                    else:
                        plays.append(f"Free throw: Missed")
            else:
                plays.append("Misses!")

                # Shooting foul = 2 free throws
                if fouled:
                    fouling_player, fouled_out = self.commit_foul(defending_team, shooter)
                    plays.append(f"Fouled by {fouling_player.name}! (PF{fouling_player.fouls}) 2 free throws...")
                    if fouled_out:
                        plays.append(f"[bold red]{fouling_player.name} FOULS OUT![/bold red]")
                        # Immediately substitute the fouled-out player
                        substitute = defending_team.substitute_fouled_out_player(fouling_player)
                        if substitute:
                            plays.append(f"{substitute.name} enters the game")
                    elif self.is_foul_trouble(fouling_player):
                        plays.append(f"[yellow]Foul trouble! {fouling_player.name} heads to the bench[/yellow]")
                        substitute = defending_team.substitute_fouled_out_player(fouling_player)
                        if substitute:
                            plays.append(f"{substitute.name} enters the game")
                    ft_results = []
                    for i in range(2):
                        ft_made = shooter.attempt_free_throw()
                        if ft_made:
                            self.possession.score += 1
                        ft_results.append('✓' if ft_made else 'X')
                    plays.append(f"Free throws: {' '.join(ft_results)}")
        
        # Rebound on miss (only if not fouled)
        if not made and not fouled:
            # 70% chance defensive rebound, 30% offensive
            if random.random() < 0.7:
                rebounder = defending_team.select_rebounder()
                plays.append(f"Rebound: {rebounder.name}")
                rebounder.get_rebound()
            else:
                rebounder = self.possession.select_rebounder()
                plays.append(f"Offensive rebound: {rebounder.name}")
                rebounder.get_rebound()
                # They might score on putback
                if random.random() < 0.4:
                    made = rebounder.attempt_shot(def_rating)
                    if made:
                        self.possession.score += 2
                        scored = True
                        plays.append(f"{rebounder.name} puts it back in!")
        
        return " → ".join(plays), scored
    
    def create_display(self) -> Layout:
        """Create the rich layout for the game display"""
        layout = Layout()
        
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="plays", size=10),
            Layout(name="court", size=16)
        )
        
        # Header with score
        score_text = f"[bold cyan]{self.team1.name} (Home)[/] [bold white]{self.team1.score} - {self.team2.score}[/bold white] [bold yellow]{self.team2.name} (Away)[/]"
        mins = self.time_remaining // 60
        secs = self.time_remaining % 60
        time_text = f"Q{self.quarter}  {mins}:{secs:02d}"

        # Team fouls (highlight if in bonus)
        team1_fouls = f"[bold red]{self.team1.team_fouls}[/bold red]" if self.team1.team_fouls >= 5 else str(self.team1.team_fouls)
        team2_fouls = f"[bold red]{self.team2.team_fouls}[/bold red]" if self.team2.team_fouls >= 5 else str(self.team2.team_fouls)
        foul_text = f"Fouls: {team1_fouls} - {team2_fouls}"

        header_table = Table.grid(expand=True)
        header_table.add_column(justify="center")
        header_table.add_row(f"{score_text}     {time_text}     {foul_text}")
        layout["header"].update(Panel(header_table, style="bold white on blue"))
        
        # Players on court
        court_table = Table(box=box.ROUNDED, expand=True)
        court_table.add_column("Team", style="cyan", no_wrap=True)
        court_table.add_column("Player", style="green")
        court_table.add_column("POS", justify="center", style="yellow")  # Position
        court_table.add_column("PTS", justify="right")
        court_table.add_column("REB", justify="right")
        court_table.add_column("AST", justify="right")
        court_table.add_column("STL", justify="right")  # Steals
        court_table.add_column("BLK", justify="right")  # Blocks
        court_table.add_column("TO", justify="right")   # Turnovers
        court_table.add_column("PF", justify="right")   # Personal fouls

        for player in self.team1.get_on_court():
            # Highlight players in foul trouble (5 fouls)
            foul_str = f"[bold red]{player.fouls}[/bold red]" if player.fouls >= 5 else str(player.fouls)
            court_table.add_row(
                self.team1.name[:12],
                player.name,
                player.position,
                str(player.points),
                str(player.rebounds),
                str(player.assists),
                str(player.steals),
                str(player.blocks),
                str(player.turnovers),
                foul_str
            )

        court_table.add_row("", "", "", "", "", "", "", "", "", "")  # Spacer

        for player in self.team2.get_on_court():
            # Highlight players in foul trouble (5 fouls)
            foul_str = f"[bold red]{player.fouls}[/bold red]" if player.fouls >= 5 else str(player.fouls)
            court_table.add_row(
                self.team2.name[:12],
                player.name,
                player.position,
                str(player.points),
                str(player.rebounds),
                str(player.assists),
                str(player.steals),
                str(player.blocks),
                str(player.turnovers),
                foul_str
            )
        
        layout["court"].update(Panel(court_table, title="On Court", border_style="green"))
        
        # Play by play (most recent first, like original 80s game)
        recent_plays = self.play_by_play[-3:][::-1]  # Reverse: newest first (show last 3)
        if recent_plays:
            # Dim the old plays (keep most recent bright)
            for i in range(1, len(recent_plays)):
                recent_plays[i] = f"[dim]{recent_plays[i]}[/dim]"
        play_text = "\n".join(recent_plays) if recent_plays else ""
        layout["plays"].update(
            Panel(play_text, title="Play-by-Play (Most Recent First)", border_style="yellow", padding=(1, 2))
        )
        
        return layout
    
    def simulate_quarter(self):
        """Simulate one quarter of basketball"""
        console.print(f"\n[bold]Quarter {self.quarter}[/bold]")
        time.sleep(1)

        # Reset team fouls at start of each quarter
        self.team1.reset_quarter_fouls()
        self.team2.reset_quarter_fouls()

        # Bring starters back at start of Q3 (after halftime)
        if self.quarter == 3:
            # Use PPG-based starting lineup (same logic as game start)
            team1_starters = [(i, p.ppg) for i, p in enumerate(self.team1.players)]
            team1_starters.sort(key=lambda x: -x[1])
            self.team1.on_court_indices = [idx for idx, _ in team1_starters[:5]]

            team2_starters = [(i, p.ppg) for i, p in enumerate(self.team2.players)]
            team2_starters.sort(key=lambda x: -x[1])
            self.team2.on_court_indices = [idx for idx, _ in team2_starters[:5]]

        # Track substitution windows to avoid duplicate subs
        # Windows at 6:00 (360 sec) and 3:00 (180 sec)
        sub_windows_hit = set()

        possession_count = 0
        closing_lineup_set = False  # Track if we've locked in closing lineup

        with Live(self.create_display(), refresh_per_second=4) as live:
            while self.time_remaining > 0:
                # Check for clutch time
                is_clutch, phase = self.is_clutch_time()

                if is_clutch and phase == "closing":
                    # CLOSING LINEUP (3:00 or less) - Best 5 locked in
                    if not closing_lineup_set:
                        # Put best 5 on court (avoiding foul trouble)
                        if self.team1 != self.manual_control_team:
                            self.team1.on_court_indices = self.team1.get_top_players(5, avoid_foul_trouble=True)[:5]
                        if self.team2 != self.manual_control_team:
                            self.team2.on_court_indices = self.team2.get_top_players(5, avoid_foul_trouble=True)[:5]
                        closing_lineup_set = True
                    # Skip all normal substitution logic (closing 5 stay in)

                elif is_clutch and phase == "crunch":
                    # CRUNCH TIME (8:00-3:00) - Tighter rotation (top 7-8 only)
                    # Allow time-based subs but restrict pool to top 7-8 players
                    if self.time_remaining <= 360 and 360 not in sub_windows_hit:
                        sub_windows_hit.add(360)
                        # Restricted substitution using top 8 players
                        if self.team1 != self.manual_control_team:
                            self.team1.time_based_substitutions(self.game_minutes_elapsed, restrict_to_top=8)
                        if self.team2 != self.manual_control_team:
                            self.team2.time_based_substitutions(self.game_minutes_elapsed, restrict_to_top=8)

                    # No 3:00 sub window in crunch time (handled by closing lineup above)

                else:
                    # NORMAL TIME - Regular substitution windows
                    if self.time_remaining <= 360 and 360 not in sub_windows_hit:
                        # 6:00 mark - first substitution wave
                        sub_windows_hit.add(360)
                        if self.team1 != self.manual_control_team:
                            self.team1.time_based_substitutions(self.game_minutes_elapsed)
                        if self.team2 != self.manual_control_team:
                            self.team2.time_based_substitutions(self.game_minutes_elapsed)

                    if self.time_remaining <= 180 and 180 not in sub_windows_hit:
                        # 3:00 mark - second substitution wave
                        sub_windows_hit.add(180)
                        if self.team1 != self.manual_control_team:
                            self.team1.time_based_substitutions(self.game_minutes_elapsed)
                        if self.team2 != self.manual_control_team:
                            self.team2.time_based_substitutions(self.game_minutes_elapsed)

                # Simulate possession (era-specific base time, adjusted by team pace rating)
                min_time, max_time = self.get_era_possession_time(self.possession.year)
                base_time = random.randint(min_time, max_time)
                possession_time = int(base_time / self.possession.pace_rating)

                play_desc, scored = self.simulate_possession()
                # Add score inline for slow watching (makes play-by-play self-explanatory)
                if scored and self.game_speed >= 1.0:  # Only at slower speeds
                    play_desc_with_score = f"{play_desc} [{self.team1.score}-{self.team2.score}]"
                    self.play_by_play.append(play_desc_with_score)
                else:
                    self.play_by_play.append(play_desc)

                # Update minutes played for both teams
                self.team1.update_minutes(possession_time)
                self.team2.update_minutes(possession_time)
                self.game_minutes_elapsed += possession_time / 60.0

                # Check for foul outs (must substitute immediately)
                self.team1.check_foul_outs()
                self.team2.check_foul_outs()

                # Emergency substitution check (only if player hit their full minutes)
                # Skip during closing lineup (best 5 locked in)
                if phase != "closing":
                    possession_count += 1
                    if possession_count % 5 == 0:  # Less frequent than before
                        self.team1.check_substitutions()
                        self.team2.check_substitutions()

                # Switch possession (unless offensive rebound or retained possession)
                if "Offensive rebound" not in play_desc and "retains possession" not in play_desc:
                    self.possession = self.team2 if self.possession == self.team1 else self.team1

                # Update time
                self.time_remaining = max(0, self.time_remaining - possession_time)

                # Update display
                live.update(self.create_display())
                time.sleep(self.game_speed)

        # Record scores at end of quarter
        self.quarter_scores['team1'].append(self.team1.score)
        self.quarter_scores['team2'].append(self.team2.score)

        # Clear screen before showing quarter summary
        console.clear()
        console.print(f"[bold green]End of Quarter {self.quarter}[/bold green]")
        console.print(f"Score: {self.team1.name} {self.team1.score} - {self.team2.name} {self.team2.score}\n")
    
    def simulate_game(self):
        """Simulate a full 4-quarter game with overtime if needed"""
        for q in range(1, 5):
            self.quarter = q
            self.time_remaining = 720
            self.simulate_quarter()

            if q < 4:
                time.sleep(2)  # Brief pause between quarters

        # Check for overtime
        ot_count = 0
        while self.team1.score == self.team2.score:
            ot_count += 1
            console.print(f"\n[bold yellow]OVERTIME {ot_count}![/bold yellow]")
            console.print(f"Score tied at {self.team1.score}-{self.team2.score}\n")
            time.sleep(2)

            self.quarter = f"OT{ot_count}"
            self.time_remaining = 300  # 5 minutes for OT
            self.simulate_quarter()
            time.sleep(2)

        # Final score
        console.print("\n" + "="*60)
        if ot_count > 0:
            console.print(f"[bold magenta]FINAL SCORE ({ot_count} OT)[/bold magenta]")
        else:
            console.print("[bold magenta]FINAL SCORE[/bold magenta]")
        console.print("="*60)

        if self.team1.score > self.team2.score:
            console.print(f"[bold green]{self.team1.name} defeats {self.team2.name}![/bold green]")
        else:
            console.print(f"[bold green]{self.team2.name} defeats {self.team1.name}![/bold green]")

        console.print(f"\n[cyan]{self.team1.name}: {self.team1.score}[/cyan]")
        console.print(f"[yellow]{self.team2.name}: {self.team2.score}[/yellow]\n")

        # Show combined box score
        self.show_box_score()

    def show_box_score(self):
        """Display combined box score with quarter scores, team totals, and player stats"""

        # Quarter scores and team totals
        console.print("[bold]BOX SCORE[/bold]\n")

        # Build quarter score table
        num_quarters = len(self.quarter_scores['team1'])

        # Calculate quarter points (not cumulative)
        team1_quarter_pts = []
        team2_quarter_pts = []
        for i in range(num_quarters):
            if i == 0:
                team1_quarter_pts.append(self.quarter_scores['team1'][i])
                team2_quarter_pts.append(self.quarter_scores['team2'][i])
            else:
                team1_quarter_pts.append(self.quarter_scores['team1'][i] - self.quarter_scores['team1'][i-1])
                team2_quarter_pts.append(self.quarter_scores['team2'][i] - self.quarter_scores['team2'][i-1])

        # Get team totals
        team1_totals = self.team1.get_team_totals()
        team2_totals = self.team2.get_team_totals()

        # Summary table with quarter scores and team totals
        summary_table = Table(box=box.ROUNDED, title="Game Summary")
        summary_table.add_column("Team", style="cyan")

        # Add quarter columns
        for i in range(num_quarters):
            if i < 4:
                summary_table.add_column(f"Q{i+1}", justify="right")
            else:
                summary_table.add_column(f"OT{i-3}", justify="right", style="yellow")

        summary_table.add_column("Final", justify="right", style="bold green")
        summary_table.add_column("FG", justify="right")
        summary_table.add_column("FG%", justify="right")
        summary_table.add_column("FT", justify="right")
        summary_table.add_column("FT%", justify="right")
        summary_table.add_column("REB", justify="right")
        summary_table.add_column("AST", justify="right")
        summary_table.add_column("STL", justify="right")
        summary_table.add_column("BLK", justify="right")
        summary_table.add_column("TO", justify="right")

        # Team 1 row
        team1_row = [self.team1.name] + [str(pts) for pts in team1_quarter_pts] + [
            str(self.team1.score),
            f"{team1_totals['fgm']}/{team1_totals['fga']}",
            f"{team1_totals['fg_pct']:.1f}",
            f"{team1_totals['ftm']}/{team1_totals['fta']}",
            f"{team1_totals['ft_pct']:.1f}",
            str(team1_totals['reb']),
            str(team1_totals['ast']),
            str(team1_totals['stl']),
            str(team1_totals['blk']),
            str(team1_totals['to'])
        ]

        # Team 2 row
        team2_row = [self.team2.name] + [str(pts) for pts in team2_quarter_pts] + [
            str(self.team2.score),
            f"{team2_totals['fgm']}/{team2_totals['fga']}",
            f"{team2_totals['fg_pct']:.1f}",
            f"{team2_totals['ftm']}/{team2_totals['fta']}",
            f"{team2_totals['ft_pct']:.1f}",
            str(team2_totals['reb']),
            str(team2_totals['ast']),
            str(team2_totals['stl']),
            str(team2_totals['blk']),
            str(team2_totals['to'])
        ]

        summary_table.add_row(*team1_row)
        summary_table.add_row(*team2_row)

        console.print(summary_table)
        console.print()

        # Individual player stats
        self.show_team_stats(self.team1)
        self.show_team_stats(self.team2)

    def show_quarter_scores(self):
        """Display quarter-by-quarter scoring breakdown"""
        console.print("[bold]Scoring by Quarter[/bold]\n")

        # Create table
        score_table = Table(box=box.ROUNDED)
        score_table.add_column("Team", style="cyan")

        # Add columns for each quarter
        num_quarters = len(self.quarter_scores['team1'])
        for i in range(num_quarters):
            if i < 4:
                score_table.add_column(f"Q{i+1}", justify="right", style="white")
            else:
                # Overtime periods
                score_table.add_column(f"OT{i-3}", justify="right", style="yellow")

        # Add Total column
        score_table.add_column("Total", justify="right", style="bold green")

        # Calculate quarter points (points scored in each quarter, not cumulative)
        team1_quarter_pts = []
        team2_quarter_pts = []

        for i in range(num_quarters):
            if i == 0:
                team1_quarter_pts.append(self.quarter_scores['team1'][i])
                team2_quarter_pts.append(self.quarter_scores['team2'][i])
            else:
                team1_quarter_pts.append(self.quarter_scores['team1'][i] - self.quarter_scores['team1'][i-1])
                team2_quarter_pts.append(self.quarter_scores['team2'][i] - self.quarter_scores['team2'][i-1])

        # Add rows for each team
        team1_row = [self.team1.name] + [str(pts) for pts in team1_quarter_pts] + [str(self.team1.score)]
        team2_row = [self.team2.name] + [str(pts) for pts in team2_quarter_pts] + [str(self.team2.score)]

        score_table.add_row(*team1_row)
        score_table.add_row(*team2_row)

        console.print(score_table)
        console.print()

    def show_team_stats(self, team: Team):
        """Display final statistics for a team"""
        console.print(f"\n[bold]{team.name} - Final Stats[/bold]")

        stats_table = Table(box=box.SIMPLE)
        stats_table.add_column("Player", style="cyan")
        stats_table.add_column("MIN", justify="right")
        stats_table.add_column("PTS", justify="right")
        stats_table.add_column("REB", justify="right")
        stats_table.add_column("AST", justify="right")
        stats_table.add_column("STL", justify="right")
        stats_table.add_column("BLK", justify="right")
        stats_table.add_column("TO", justify="right")
        stats_table.add_column("FG", justify="right")
        stats_table.add_column("FG%", justify="right")
        stats_table.add_column("PF", justify="right")

        for player in team.players:  # Show all players
            fg_pct = f"{(player.fgm / player.fga * 100):.1f}" if player.fga > 0 else "0.0"
            mins = f"{int(player.minutes_played)}"
            # Highlight fouled out players
            foul_str = f"[bold red]{player.fouls}[/bold red]" if player.fouls >= 6 else str(player.fouls)
            stats_table.add_row(
                player.name,
                mins,
                str(player.points),
                str(player.rebounds),
                str(player.assists),
                str(player.steals),
                str(player.blocks),
                str(player.turnovers),
                f"{player.fgm}/{player.fga}",
                fg_pct,
                foul_str
            )

        console.print(stats_table)


def load_teams_from_csv() -> Dict[str, Dict]:
    """Load teams and players from CSV files"""
    teams_data = {}
    
    # Load teams
    with open('teams.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            teams_data[row['team_id']] = {
                'name': row['display_name'],
                'full_name': row['team_name'],
                'year': int(row['year']),
                'pace_rating': float(row['pace_rating']),
                'three_pt_rate': float(row['three_pt_rate']),
                'def_rating': float(row['def_rating']),
                'players': []
            }
    
    # Load players
    with open('players.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            team_id = row['team_id']
            if team_id in teams_data:
                player = Player(
                    name=row['player_name'],
                    fg_pct=float(row['fg_pct']),
                    ft_pct=float(row['ft_pct']),
                    rpg=float(row['rpg']),
                    apg=float(row['apg']),
                    position=row['position'],
                    two_pt_pct=float(row['two_pt_pct']),
                    three_pt_pct=float(row['three_pt_pct']),
                    minutes_pg=float(row['minutes_pg']),
                    ppg=float(row['ppg']),
                    fta_pg=float(row['fta_pg']),
                    usage_rate=float(row['usage_rate'])
                )
                teams_data[team_id]['players'].append(player)
    
    return teams_data


def select_team(teams_data: Dict, team_number: int) -> Team:
    """Interactive team selection"""
    team_label = "Home Team" if team_number == 1 else "Away Team"
    console.print(f"\n[bold cyan]Select {team_label}:[/bold cyan]\n")
    
    # Create a sorted list of teams
    team_list = []
    for team_id, data in sorted(teams_data.items()):
        team_list.append((team_id, data))
    
    # Display teams in a nice table
    table = Table(box=box.ROUNDED)
    table.add_column("#", style="cyan", justify="right")
    table.add_column("Team", style="green")
    table.add_column("Year", style="yellow")
    
    for idx, (team_id, data) in enumerate(team_list, 1):
        table.add_row(str(idx), data['full_name'], str(data['year']))
    
    console.print(table)
    
    # Get user selection
    while True:
        choice = Prompt.ask("\nEnter team number", default="1")
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(team_list):
                team_id, data = team_list[idx]
                return Team(data['name'], data['players'], data['pace_rating'], data['three_pt_rate'], data['def_rating'], data['year'])
            else:
                console.print("[red]Invalid team number. Try again.[/red]")
        except ValueError:
            console.print("[red]Please enter a valid number.[/red]")


class InteractiveGame(GameSimulation):
    """Interactive game where user controls one team's decisions"""

    def __init__(self, user_team: Team, cpu_team: Team, game_speed: float = 0.6):
        """
        Initialize interactive game
        user_team: The team controlled by the user
        cpu_team: The CPU-controlled opponent
        """
        super().__init__(user_team, cpu_team, game_speed)
        self.manual_control_team = user_team  # Mark user team for manual control (skip auto-rotations)
        self.user_team = user_team  # team1 is user
        self.cpu_team = cpu_team    # team2 is CPU
        self.shot_clock = 24
        self.user_timeouts = 7
        self.cpu_timeouts = 7

    def create_display_interactive(self, ball_handler: Player = None):
        """Create display with player numbers for interactive mode - returns renderable panels"""
        panels = []

        # === HEADER ===
        score_text = f"[bold cyan]{self.team1.name} (YOU)[/] [bold white]{self.team1.score} - {self.team2.score}[/bold white] [bold yellow]{self.team2.name} (CPU)[/]"
        mins = self.time_remaining // 60
        secs = self.time_remaining % 60
        time_text = f"Q{self.quarter}  {mins}:{secs:02d}"

        team1_fouls = f"[bold red]{self.team1.team_fouls}[/bold red]" if self.team1.team_fouls >= 5 else str(self.team1.team_fouls)
        team2_fouls = f"[bold red]{self.team2.team_fouls}[/bold red]" if self.team2.team_fouls >= 5 else str(self.team2.team_fouls)
        foul_text = f"Fouls: {team1_fouls} - {team2_fouls}"

        shot_clock_text = ""
        if self.possession == self.user_team:
            if self.shot_clock <= 5:
                shot_clock_text = f"  |  [bold red]Shot Clock: {self.shot_clock} sec - HURRY![/bold red]"
            else:
                shot_clock_text = f"  |  Shot Clock: {self.shot_clock} sec"

        header_text = f"{score_text}  |  {time_text}  |  {foul_text}{shot_clock_text}"
        panels.append(Panel(header_text, style="bold white on blue"))

        # Players on court with numbers
        court_table = Table(box=box.ROUNDED, expand=True)
        court_table.add_column("Team", style="cyan", no_wrap=True)
        court_table.add_column("#", justify="center", style="magenta", no_wrap=True)
        court_table.add_column("Player", style="green")
        court_table.add_column("POS", justify="center", style="yellow")
        court_table.add_column("PTS", justify="right")
        court_table.add_column("REB", justify="right")
        court_table.add_column("AST", justify="right")
        court_table.add_column("STL", justify="right")
        court_table.add_column("BLK", justify="right")
        court_table.add_column("TO", justify="right")
        court_table.add_column("PF", justify="right")

        # User team players (with numbers 1-5)
        for idx, player_idx in enumerate(self.team1.on_court_indices, 1):
            player = self.team1.players[player_idx]
            foul_str = f"[bold red]{player.fouls}[/bold red]" if player.fouls >= 5 else str(player.fouls)

            # Mark ball handler
            player_name = player.name
            if ball_handler and player == ball_handler:
                player_name = f"[bold]{player.name} ← BALL[/bold]"

            # Add separator after last user team player
            is_last = (idx == len(self.team1.on_court_indices))
            court_table.add_row(
                self.team1.name[:12],
                f"[{idx}]",
                player_name,
                player.position,
                str(player.points),
                str(player.rebounds),
                str(player.assists),
                str(player.steals),
                str(player.blocks),
                str(player.turnovers),
                foul_str,
                end_section=is_last
            )

        # CPU team players (no numbers)
        for player in self.team2.get_on_court():
            foul_str = f"[bold red]{player.fouls}[/bold red]" if player.fouls >= 5 else str(player.fouls)
            court_table.add_row(
                self.team2.name[:12],
                "",
                player.name,
                player.position,
                str(player.points),
                str(player.rebounds),
                str(player.assists),
                str(player.steals),
                str(player.blocks),
                str(player.turnovers),
                foul_str
            )

        # === PLAY-BY-PLAY ===
        if self.play_by_play:
            # Mirror season mode: most recent first, dim older plays
            recent_plays = self.play_by_play[-3:][::-1]  # Reverse: newest first (show last 3)
            if recent_plays:
                # Dim the old plays (keep most recent bright)
                for i in range(1, len(recent_plays)):
                    recent_plays[i] = f"[dim]{recent_plays[i]}[/dim]"
            play_text = "\n".join(recent_plays)
            panels.append(Panel(play_text, title="[yellow]Recent Plays (Most Recent First)[/yellow]", border_style="yellow"))

        # === ON COURT ===
        panels.append(Panel(court_table, title="[green]On Court[/green]", border_style="green"))

        return panels

    def substitution_menu(self):
        """Allow user to make substitutions"""
        console.print("\n[bold cyan]═══ SUBSTITUTIONS ═══[/bold cyan]\n")

        while True:
            # Show current lineup
            console.print("[bold green]Current Lineup (on court):[/bold green]")
            for idx, player_idx in enumerate(self.user_team.on_court_indices, 1):
                player = self.user_team.players[player_idx]
                console.print(f"  [{idx}] {player.name:25s} {player.position:3s}  {player.minutes_played:.0f} min  {player.points} PTS  {player.fouls} PF")

            console.print("\n[bold yellow]Bench:[/bold yellow]")
            bench_players = [(i, p) for i, p in enumerate(self.user_team.players) if i not in self.user_team.on_court_indices]
            if bench_players:
                for bench_num, (player_idx, player) in enumerate(bench_players, 1):
                    console.print(f"  [{bench_num+5}] {player.name:25s} {player.position:3s}  {player.minutes_played:.0f} min  {player.points} PTS  {player.fouls} PF")
            else:
                console.print("  (No bench players available)")

            console.print("\n[cyan]Enter two numbers to swap (e.g., '1 6' to swap position 1 with bench player 1)[/cyan]")
            console.print("[cyan]Or press ENTER to continue playing[/cyan]")

            choice = console.input("\n[bold]Substitution: [/bold]").strip()

            if not choice:
                break

            try:
                nums = [int(x) for x in choice.split()]
                if len(nums) != 2:
                    console.print("[red]Please enter exactly 2 numbers[/red]\n")
                    continue

                court_num, bench_num = nums

                # Validate court position (1-5)
                if court_num < 1 or court_num > 5:
                    console.print("[red]First number must be 1-5 (on-court position)[/red]\n")
                    continue

                # Validate bench position (6+)
                if bench_num < 6 or bench_num > 5 + len(bench_players):
                    console.print(f"[red]Second number must be 6-{5 + len(bench_players)} (bench player)[/red]\n")
                    continue

                # Get actual player indices
                court_player_idx = self.user_team.on_court_indices[court_num - 1]
                bench_player_idx = bench_players[bench_num - 6][0]

                # Make the swap
                self.user_team.on_court_indices[court_num - 1] = bench_player_idx

                court_player = self.user_team.players[court_player_idx]
                bench_player = self.user_team.players[bench_player_idx]

                console.print(f"[green]✓ Subbed out {court_player.name}, subbed in {bench_player.name}[/green]\n")

            except ValueError:
                console.print("[red]Invalid input. Use format: 1 6[/red]\n")
                continue

        console.print("[green]Resuming play...[/green]\n")

    def get_user_action(self, ball_handler: Player, on_court_players: List[Player]) -> tuple:
        """
        Display action menu and get user's choice
        Returns: (action_type, target_player_or_None)
        """
        console.print("\n[bold cyan]Actions:[/bold cyan]")

        # Build action menu
        actions = []
        for idx, player_idx in enumerate(self.user_team.on_court_indices, 1):
            player = self.user_team.players[player_idx]
            if player != ball_handler:
                actions.append(f"[{idx}] Pass to {player.name}")
            else:
                actions.append(f"[{idx}] Keep dribbling")

        # Add shooting options with percentages
        two_pt_pct = ball_handler.two_pt_pct if ball_handler.two_pt_pct > 0 else ball_handler.fg_pct
        three_pt_pct = ball_handler.three_pt_pct
        actions.append(f"[S] Shoot 2PT ({two_pt_pct:.1f}%)")
        if three_pt_pct > 0:
            actions.append(f"[T] Shoot 3PT ({three_pt_pct:.1f}%)")
        actions.append(f"[X] Timeout ({self.user_timeouts} remaining)")

        # Display actions
        for action in actions:
            console.print(f"  {action}")

        # Get input (single keypress - no ENTER needed)
        console.print("\n[bold]Your choice: [/bold]", end='')
        while True:
            choice = getch().upper()
            console.print(choice)  # Echo the character

            # Parse choice
            if choice in ['S', 'T', 'X']:
                return (choice, None)
            elif choice.isdigit():
                num = int(choice)
                if 1 <= num <= 5:
                    target_idx = self.user_team.on_court_indices[num - 1]
                    target_player = self.user_team.players[target_idx]
                    return (num, target_player)

            console.print("[red]Invalid choice. Try again.[/red]")
            console.print("\n[bold]Your choice: [/bold]", end='')

    def interactive_possession(self, ball_handler: Player = None, after_opponent_score: bool = False) -> tuple:
        """
        Handle one user-controlled possession with shot clock
        Returns: (play_description, scored, final_ball_handler_for_next_possession)
        """
        if ball_handler is None:
            # Pick a guard to inbound if possible
            guards = [p for p in self.user_team.get_on_court() if p.position in ['PG', 'SG']]
            ball_handler = guards[0] if guards else self.user_team.select_shooter()

        self.shot_clock = 24
        plays = []
        last_passer = None  # Track who passed most recently for assist credit

        # If after opponent scored, show inbound pass
        if after_opponent_score:
            plays.append(f"{ball_handler.name} inbounds the ball")
        else:
            plays.append(f"{ball_handler.name} has the ball")

        while self.shot_clock > 0:
            # Display court and get user action (print panels directly)
            console.clear()
            panels = self.create_display_interactive(ball_handler)
            for panel in panels:
                console.print(panel)

            action_type, target = self.get_user_action(ball_handler, self.user_team.get_on_court())

            if action_type == 'X':
                # Timeout
                if self.user_timeouts > 0:
                    self.user_timeouts -= 1
                    plays.append(f"Timeout called ({self.user_timeouts} remaining)")
                    console.print(f"\n[bold yellow]TIMEOUT! ({self.user_timeouts} timeouts left)[/bold yellow]\n")
                    time.sleep(1)

                    # Substitution menu
                    self.substitution_menu()

                    # Continue possession with same ball handler
                    continue
                else:
                    console.print("[red]No timeouts remaining![/red]")
                    continue

            elif action_type in [1, 2, 3, 4, 5]:
                # Pass or dribble
                if target == ball_handler:
                    # Dribbling - clears potential assist
                    plays.append(f"{ball_handler.name} dribbles...")
                    time_used = random.randint(6, 10)
                    self.shot_clock = max(0, self.shot_clock - time_used)
                    last_passer = None  # Dribbling clears assist opportunity

                    # Small chance of turnover while dribbling
                    if random.random() < 0.03:
                        stealer = random.choice(self.cpu_team.get_on_court())
                        stealer.steals += 1
                        ball_handler.turnovers += 1
                        plays.append(f"STEAL by {stealer.name}!")
                        return " → ".join(plays), False, stealer  # CPU gets ball
                else:
                    # Pass - sets up potential assist
                    plays.append(f"{ball_handler.name} passes to {target.name}")
                    time_used = random.randint(3, 6)
                    self.shot_clock = max(0, self.shot_clock - time_used)

                    # Small chance of steal on pass
                    if random.random() < 0.05:
                        stealer = random.choice(self.cpu_team.get_on_court())
                        stealer.steals += 1
                        ball_handler.turnovers += 1
                        plays.append(f"INTERCEPTED by {stealer.name}!")
                        return " → ".join(plays), False, None

                    last_passer = ball_handler  # Track passer for potential assist
                    ball_handler = target

                # Show updated play-by-play with delay
                self.play_by_play.append(" → ".join(plays))
                if self.game_speed >= 0.05:
                    console.print(f"\n{plays[-1]}")
                    time.sleep(min(self.game_speed, 1.0))

            elif action_type == 'S':
                # Shoot 2-pointer
                plays.append(f"{ball_handler.name} shoots...")
                self.shot_clock = 0

                # Check for block
                if random.random() < 0.05:
                    blocker = random.choice(self.cpu_team.get_on_court())
                    blocker.blocks += 1
                    ball_handler.fga += 1
                    plays.append(f"BLOCKED by {blocker.name}!")
                    made = False
                    fouled = False  # Can't foul on clean block
                else:
                    made = ball_handler.attempt_shot(self.cpu_team.def_rating)

                    # Check for foul (weighted by FTA per game)
                    foul_probability = min(0.3, ball_handler.fta_pg * 0.02)
                    fouled = random.random() < foul_probability

                if made:
                    self.user_team.score += 2
                    plays.append(f"GOOD!")

                    # Credit assist if shot came after a pass (70% chance)
                    if last_passer and random.random() < 0.7:
                        last_passer.get_assist()
                        plays.append(f"(Assist: {last_passer.name})")

                    # And-1 opportunity if fouled
                    if fouled:
                        fouling_player, fouled_out = self.commit_foul(self.cpu_team, ball_handler)
                        plays.append(f"Fouled by {fouling_player.name}! (PF{fouling_player.fouls}) And-1 opportunity...")
                        if fouled_out:
                            plays.append(f"[bold red]{fouling_player.name} FOULS OUT![/bold red]")
                            substitute = self.cpu_team.substitute_fouled_out_player(fouling_player)
                            if substitute:
                                plays.append(f"{substitute.name} enters the game")
                        elif self.is_foul_trouble(fouling_player):
                            plays.append(f"[yellow]Foul trouble! {fouling_player.name} heads to the bench[/yellow]")
                            substitute = self.cpu_team.substitute_fouled_out_player(fouling_player)
                            if substitute:
                                plays.append(f"{substitute.name} enters the game")
                        ft_made = ball_handler.attempt_free_throw()
                        if ft_made:
                            self.user_team.score += 1
                            plays.append(f"Free throw: GOOD")
                        else:
                            plays.append(f"Free throw: Missed")

                    return " → ".join(plays), True, None
                else:
                    plays.append("Misses!")

                    # Shooting foul = 2 free throws
                    if fouled:
                        fouling_player, fouled_out = self.commit_foul(self.cpu_team, ball_handler)
                        plays.append(f"Fouled by {fouling_player.name}! (PF{fouling_player.fouls}) 2 free throws...")
                        if fouled_out:
                            plays.append(f"[bold red]{fouling_player.name} FOULS OUT![/bold red]")
                            substitute = self.cpu_team.substitute_fouled_out_player(fouling_player)
                            if substitute:
                                plays.append(f"{substitute.name} enters the game")
                        elif self.is_foul_trouble(fouling_player):
                            plays.append(f"[yellow]Foul trouble! {fouling_player.name} heads to the bench[/yellow]")
                            substitute = self.cpu_team.substitute_fouled_out_player(fouling_player)
                            if substitute:
                                plays.append(f"{substitute.name} enters the game")
                        ft_results = []
                        for i in range(2):
                            ft_made = ball_handler.attempt_free_throw()
                            if ft_made:
                                self.user_team.score += 1
                            ft_results.append('✓' if ft_made else 'X')
                        plays.append(f"Free throws: {' '.join(ft_results)}")
                        return " → ".join(plays), True, None  # FTs end possession regardless
                    # Handle rebound
                    if random.random() < 0.7:
                        # CPU defensive rebound - ends possession
                        rebounder = self.cpu_team.select_rebounder()
                        plays.append(f"Rebound: {rebounder.name}")
                        rebounder.get_rebound()
                        return " → ".join(plays), False, None
                    else:
                        # Offensive rebound - CPU auto-resolves putback 70% of the time
                        rebounder = self.user_team.select_rebounder()
                        rebounder.get_rebound()

                        if random.random() < 0.7:
                            # CPU auto-resolves putback (possession will end)
                            if random.random() < 0.45:
                                made = rebounder.attempt_shot(self.cpu_team.def_rating)
                                if made:
                                    self.user_team.score += 2
                                    plays.append(f"{rebounder.name} gets the board and tips it in!")
                                    return " → ".join(plays), True, None
                                else:
                                    plays.append(f"{rebounder.name} gets the board, follow-up... no good!")
                                    # CPU gets defensive rebound
                                    cpu_rebounder = self.cpu_team.select_rebounder()
                                    cpu_rebounder.get_rebound()
                                    plays.append(f"Rebound: {cpu_rebounder.name}")
                                    return " → ".join(plays), False, None
                            else:
                                # No putback attempt - CPU recovers
                                cpu_rebounder = self.cpu_team.select_rebounder()
                                cpu_rebounder.get_rebound()
                                plays.append(f"Loose ball, {cpu_rebounder.name} recovers it")
                                return " → ".join(plays), False, None
                        # If not auto-resolved, user continues possession
                        plays.append(f"Offensive rebound: {rebounder.name}")
                        ball_handler = rebounder
                        self.shot_clock = 14  # Reset shot clock after offensive rebound (NBA rule)

            elif action_type == 'T':
                # Shoot 3-pointer
                plays.append(f"{ball_handler.name} shoots a three-pointer...")
                self.shot_clock = 0

                # Check for block (rare on 3PT)
                if random.random() < 0.02:
                    blocker = random.choice(self.cpu_team.get_on_court())
                    blocker.blocks += 1
                    ball_handler.fga += 1
                    plays.append(f"BLOCKED by {blocker.name}!")
                    made = False
                    fouled = False  # Can't foul on clean block
                else:
                    made = ball_handler.attempt_three(self.cpu_team.def_rating)

                    # Check for foul (weighted by FTA per game, rarer on 3PT)
                    foul_probability = min(0.2, ball_handler.fta_pg * 0.015)
                    fouled = random.random() < foul_probability

                if made:
                    self.user_team.score += 3
                    plays.append(f"GOOD! Three-pointer!")

                    # Credit assist if shot came after a pass (70% chance)
                    if last_passer and random.random() < 0.7:
                        last_passer.get_assist()
                        plays.append(f"(Assist: {last_passer.name})")

                    # And-1 opportunity if fouled (4-point play!)
                    if fouled:
                        fouling_player, fouled_out = self.commit_foul(self.cpu_team, ball_handler)
                        plays.append(f"Fouled by {fouling_player.name}! (PF{fouling_player.fouls}) 4-point play opportunity!")
                        if fouled_out:
                            plays.append(f"[bold red]{fouling_player.name} FOULS OUT![/bold red]")
                            substitute = self.cpu_team.substitute_fouled_out_player(fouling_player)
                            if substitute:
                                plays.append(f"{substitute.name} enters the game")
                        elif self.is_foul_trouble(fouling_player):
                            plays.append(f"[yellow]Foul trouble! {fouling_player.name} heads to the bench[/yellow]")
                            substitute = self.cpu_team.substitute_fouled_out_player(fouling_player)
                            if substitute:
                                plays.append(f"{substitute.name} enters the game")
                        ft_made = ball_handler.attempt_free_throw()
                        if ft_made:
                            self.user_team.score += 1
                            plays.append(f"Free throw: GOOD")
                        else:
                            plays.append(f"Free throw: Missed")

                    return " → ".join(plays), True, None
                else:
                    plays.append("No good!")

                    # Shooting foul = 3 free throws
                    if fouled:
                        fouling_player, fouled_out = self.commit_foul(self.cpu_team, ball_handler)
                        plays.append(f"Fouled by {fouling_player.name}! (PF{fouling_player.fouls}) 3 free throws...")
                        if fouled_out:
                            plays.append(f"[bold red]{fouling_player.name} FOULS OUT![/bold red]")
                            substitute = self.cpu_team.substitute_fouled_out_player(fouling_player)
                            if substitute:
                                plays.append(f"{substitute.name} enters the game")
                        elif self.is_foul_trouble(fouling_player):
                            plays.append(f"[yellow]Foul trouble! {fouling_player.name} heads to the bench[/yellow]")
                            substitute = self.cpu_team.substitute_fouled_out_player(fouling_player)
                            if substitute:
                                plays.append(f"{substitute.name} enters the game")
                        ft_results = []
                        for i in range(3):
                            ft_made = ball_handler.attempt_free_throw()
                            if ft_made:
                                self.user_team.score += 1
                            ft_results.append('✓' if ft_made else 'X')
                        plays.append(f"Free throws: {' '.join(ft_results)}")
                        return " → ".join(plays), True, None  # FTs end possession regardless
                    # Handle rebound
                    if random.random() < 0.7:
                        # CPU defensive rebound - ends possession
                        rebounder = self.cpu_team.select_rebounder()
                        plays.append(f"Rebound: {rebounder.name}")
                        rebounder.get_rebound()
                        return " → ".join(plays), False, None
                    else:
                        # Offensive rebound - CPU auto-resolves putback 70% of the time
                        rebounder = self.user_team.select_rebounder()
                        rebounder.get_rebound()

                        if random.random() < 0.7:
                            # CPU auto-resolves putback (possession will end)
                            if random.random() < 0.35:  # Lower chance for 3PT putbacks
                                made = rebounder.attempt_shot(self.cpu_team.def_rating)
                                if made:
                                    self.user_team.score += 2
                                    plays.append(f"{rebounder.name} gets the board and puts it back!")
                                    return " → ".join(plays), True, None
                                else:
                                    plays.append(f"{rebounder.name} gets the board, follow-up... misses!")
                                    # CPU gets defensive rebound
                                    cpu_rebounder = self.cpu_team.select_rebounder()
                                    cpu_rebounder.get_rebound()
                                    plays.append(f"Rebound: {cpu_rebounder.name}")
                                    return " → ".join(plays), False, None
                            else:
                                # No putback attempt - CPU recovers
                                cpu_rebounder = self.cpu_team.select_rebounder()
                                cpu_rebounder.get_rebound()
                                plays.append(f"Loose ball, {cpu_rebounder.name} recovers it")
                                return " → ".join(plays), False, None
                        # If not auto-resolved, user continues possession
                        plays.append(f"Offensive rebound: {rebounder.name}")
                        ball_handler = rebounder
                        self.shot_clock = 14  # Reset shot clock after offensive rebound (NBA rule)

        # Shot clock violation
        ball_handler.turnovers += 1
        plays.append("SHOT CLOCK VIOLATION!")
        return " → ".join(plays), False, None

    def simulate_quarter(self):
        """Override to handle interactive user possessions"""
        console.print(f"\n[bold]Quarter {self.quarter}[/bold]")
        time.sleep(1)

        # Tipoff at start of game
        if self.quarter == 1:
            console.print("\n[bold yellow]Tip-off![/bold yellow]")
            # Random tipoff winner
            if random.random() < 0.5:
                self.possession = self.team1
                console.print(f"[cyan]{self.team1.name}[/cyan] wins the tip!")
            else:
                self.possession = self.team2
                console.print(f"[yellow]{self.team2.name}[/yellow] wins the tip!")
            time.sleep(1.5)

        # Reset team fouls
        self.team1.reset_quarter_fouls()
        self.team2.reset_quarter_fouls()

        # Q3 reset (use PPG-based starters)
        if self.quarter == 3:
            team1_starters = [(i, p.ppg) for i, p in enumerate(self.team1.players)]
            team1_starters.sort(key=lambda x: -x[1])
            # PRESERVE user's manual starting lineup selection
            # (Don't override with PPG - they chose their lineup intentionally)

            team2_starters = [(i, p.ppg) for i, p in enumerate(self.team2.players)]
            team2_starters.sort(key=lambda x: -x[1])
            self.team2.on_court_indices = [idx for idx, _ in team2_starters[:5]]

        possession_count = 0
        next_ball_handler = None  # Track who should have ball next possession
        cpu_just_scored = False  # Track if CPU scored on last possession
        last_possession_was_user = False  # Track possession changes for pacing

        # Track substitution windows to avoid duplicate subs
        sub_windows_hit = set()
        closing_lineup_set = False

        while self.time_remaining > 0:
            # Check for clutch time (for CPU substitutions)
            is_clutch, phase = self.is_clutch_time()

            # CPU TEAM SUBSTITUTIONS (user team is manual only)
            if is_clutch and phase == "closing":
                # CLOSING LINEUP (3:00 or less) - Best 5 locked in for CPU
                if not closing_lineup_set:
                    self.cpu_team.on_court_indices = self.cpu_team.get_top_players(5, avoid_foul_trouble=True)[:5]
                    closing_lineup_set = True
            elif is_clutch and phase == "crunch":
                # CRUNCH TIME (8:00-3:00) - Tighter rotation for CPU
                if self.time_remaining <= 360 and 360 not in sub_windows_hit:
                    sub_windows_hit.add(360)
                    self.cpu_team.time_based_substitutions(self.game_minutes_elapsed, restrict_to_top=8)
            else:
                # NORMAL TIME - Regular substitution windows for CPU
                if self.time_remaining <= 360 and 360 not in sub_windows_hit:
                    sub_windows_hit.add(360)
                    self.cpu_team.time_based_substitutions(self.game_minutes_elapsed)

                if self.time_remaining <= 180 and 180 not in sub_windows_hit:
                    sub_windows_hit.add(180)
                    self.cpu_team.time_based_substitutions(self.game_minutes_elapsed)
            # Determine possession time
            min_time, max_time = self.get_era_possession_time(self.possession.year)
            base_time = random.randint(min_time, max_time)
            possession_time = int(base_time / self.possession.pace_rating)

            # Execute possession (user or CPU)
            if self.possession == self.user_team:
                # USER POSSESSION - Interactive
                play_desc, scored, new_ball_handler = self.interactive_possession(next_ball_handler, after_opponent_score=cpu_just_scored)
                next_ball_handler = new_ball_handler
                cpu_just_scored = False  # Reset flag
                last_possession_was_user = True  # Mark for next possession

                # Show user's result immediately (before CPU possession)
                self.play_by_play.append(play_desc)
                score_display = f"[bold white]{self.team1.score}-{self.team2.score}[/bold white]"
                console.print(f"\n[cyan]{play_desc}[/cyan] {score_display}")
                time.sleep(0.8)  # Brief pause to let user see result
            else:
                # CPU POSSESSION - Auto-simulated
                play_desc, scored = self.simulate_possession()
                cpu_just_scored = scored  # Track if CPU scored

                # Extract rebounder from play_desc if possession switches
                if "Rebound:" in play_desc and self.user_team in [self.team1, self.team2]:
                    # Try to parse rebounder name
                    import re
                    match = re.search(r'Rebound: ([^→\n]+)', play_desc)
                    if match:
                        rebounder_name = match.group(1).strip()
                        # Find player by name
                        for player in self.user_team.players:
                            if player.name == rebounder_name:
                                next_ball_handler = player
                                break
                else:
                    next_ball_handler = None

                self.play_by_play.append(play_desc)

                # If possession just switched from user to CPU, pause to let user see what happened
                if last_possession_was_user:
                    score_display = f"[bold white]{self.team1.score}-{self.team2.score}[/bold white]"
                    console.print(f"\n[yellow]{play_desc}[/yellow] {score_display}")
                    console.print("\n[dim]Press ENTER to continue...[/dim]")
                    input()
                    last_possession_was_user = False

            # Update minutes
            self.team1.update_minutes(possession_time)
            self.team2.update_minutes(possession_time)
            self.game_minutes_elapsed += possession_time / 60.0

            # Check foul outs (both teams - required by rules)
            self.team1.check_foul_outs()
            self.team2.check_foul_outs()

            # Emergency substitution check for CPU only (user controls their own subs)
            if phase != "closing":
                possession_count += 1
                if possession_count % 5 == 0:
                    self.cpu_team.check_substitutions()

            # Switch possession based on how the possession ENDED (not what happened during)
            has_turnover = any(turnover in play_desc for turnover in [
                "SHOT CLOCK VIOLATION", "STEAL", "INTERCEPTED", "loses the ball"
            ])

            # Check the LAST action in the play (after final →)
            last_action = play_desc.split("→")[-1].strip() if "→" in play_desc else play_desc

            # Possession continues only if last action is "Offensive rebound: {player}"
            continues_possession = "Offensive rebound:" in last_action or "retains possession" in last_action

            if has_turnover or not continues_possession:
                self.possession = self.team2 if self.possession == self.team1 else self.team1

            # Update time
            self.time_remaining = max(0, self.time_remaining - possession_time)

        # Record scores
        self.quarter_scores['team1'].append(self.team1.score)
        self.quarter_scores['team2'].append(self.team2.score)

        # Clear screen before showing quarter summary
        console.clear()
        console.print(f"[bold green]End of Quarter {self.quarter}[/bold green]")
        console.print(f"Score: {self.team1.name} {self.team1.score} - {self.team2.name} {self.team2.score}\n")

        # Allow substitutions between quarters (except after Q4 - might go to OT)
        if self.quarter < 4:
            time.sleep(2)
            console.print("[bold cyan]Make substitutions for next quarter?[/bold cyan]")
            sub_choice = Prompt.ask("Press ENTER to keep lineup, or type 'S' to substitute", default="", show_default=False)
            if sub_choice.upper() == 'S':
                self.substitution_menu()

    def show_halftime_stats(self):
        """Display halftime statistics for both teams"""
        console.print("\n" + "="*80)
        console.print("[bold yellow]HALFTIME STATS[/bold yellow]".center(80))
        console.print("="*80 + "\n")

        # Calculate quarter points
        team1_q1 = self.quarter_scores['team1'][0]
        team1_q2 = self.quarter_scores['team1'][1] - self.quarter_scores['team1'][0]
        team2_q1 = self.quarter_scores['team2'][0]
        team2_q2 = self.quarter_scores['team2'][1] - self.quarter_scores['team2'][0]

        # Get team totals
        team1_totals = self.team1.get_team_totals()
        team2_totals = self.team2.get_team_totals()

        # Summary table with quarter scores and team totals
        summary_table = Table(box=box.ROUNDED, title="Halftime Summary")
        summary_table.add_column("Team", style="cyan")
        summary_table.add_column("Q1", justify="right")
        summary_table.add_column("Q2", justify="right")
        summary_table.add_column("Half", justify="right", style="bold green")
        summary_table.add_column("FG", justify="right")
        summary_table.add_column("FG%", justify="right")
        summary_table.add_column("FT", justify="right")
        summary_table.add_column("FT%", justify="right")
        summary_table.add_column("REB", justify="right")
        summary_table.add_column("AST", justify="right")
        summary_table.add_column("STL", justify="right")
        summary_table.add_column("BLK", justify="right")
        summary_table.add_column("TO", justify="right")

        # Team 1 row
        team1_row = [
            self.team1.name,
            str(team1_q1),
            str(team1_q2),
            str(self.team1.score),
            f"{team1_totals['fgm']}/{team1_totals['fga']}",
            f"{team1_totals['fg_pct']:.1f}",
            f"{team1_totals['ftm']}/{team1_totals['fta']}",
            f"{team1_totals['ft_pct']:.1f}",
            str(team1_totals['reb']),
            str(team1_totals['ast']),
            str(team1_totals['stl']),
            str(team1_totals['blk']),
            str(team1_totals['to'])
        ]

        # Team 2 row
        team2_row = [
            self.team2.name,
            str(team2_q1),
            str(team2_q2),
            str(self.team2.score),
            f"{team2_totals['fgm']}/{team2_totals['fga']}",
            f"{team2_totals['fg_pct']:.1f}",
            f"{team2_totals['ftm']}/{team2_totals['fta']}",
            f"{team2_totals['ft_pct']:.1f}",
            str(team2_totals['reb']),
            str(team2_totals['ast']),
            str(team2_totals['stl']),
            str(team2_totals['blk']),
            str(team2_totals['to'])
        ]

        summary_table.add_row(*team1_row)
        summary_table.add_row(*team2_row)

        console.print(summary_table)
        console.print()

        # Individual player stats
        self.show_team_stats_halftime(self.team1)
        self.show_team_stats_halftime(self.team2)

        console.print("\n[dim]Press ENTER to continue to 2nd half...[/dim]")
        input()

    def show_team_stats_halftime(self, team: Team):
        """Display halftime statistics for a team"""
        console.print(f"\n[bold]{team.name} - Halftime Stats[/bold]")

        stats_table = Table(box=box.SIMPLE)
        stats_table.add_column("Player", style="cyan")
        stats_table.add_column("MIN", justify="right")
        stats_table.add_column("PTS", justify="right")
        stats_table.add_column("REB", justify="right")
        stats_table.add_column("AST", justify="right")
        stats_table.add_column("STL", justify="right")
        stats_table.add_column("BLK", justify="right")
        stats_table.add_column("TO", justify="right")
        stats_table.add_column("FG", justify="right")
        stats_table.add_column("FG%", justify="right")
        stats_table.add_column("PF", justify="right")

        for player in team.players:  # Show all players
            fg_pct = f"{(player.fgm / player.fga * 100):.1f}" if player.fga > 0 else "0.0"
            mins = f"{int(player.minutes_played)}"
            # Highlight players in foul trouble
            foul_str = f"[bold red]{player.fouls}[/bold red]" if player.fouls >= 3 else str(player.fouls)
            stats_table.add_row(
                player.name,
                mins,
                str(player.points),
                str(player.rebounds),
                str(player.assists),
                str(player.steals),
                str(player.blocks),
                str(player.turnovers),
                f"{player.fgm}/{player.fga}",
                fg_pct,
                foul_str
            )

        console.print(stats_table)

    def simulate_game(self):
        """Override to add halftime stats display after Q2"""
        for q in range(1, 5):
            self.quarter = q
            self.time_remaining = 720
            self.simulate_quarter()

            # Show halftime stats after Q2
            if q == 2:
                self.show_halftime_stats()

            if q < 4:
                time.sleep(2)  # Brief pause between quarters

        # Check for overtime
        ot_count = 0
        while self.team1.score == self.team2.score:
            ot_count += 1
            console.print(f"\n[bold yellow]OVERTIME {ot_count}![/bold yellow]")
            console.print(f"Score tied at {self.team1.score}-{self.team2.score}\n")
            time.sleep(2)

            self.quarter = f"OT{ot_count}"
            self.time_remaining = 300  # 5 minutes for OT
            self.simulate_quarter()
            time.sleep(2)

        # Final score
        console.print("\n" + "="*60)
        if ot_count > 0:
            console.print(f"[bold magenta]FINAL SCORE ({ot_count} OT)[/bold magenta]")
        else:
            console.print("[bold magenta]FINAL SCORE[/bold magenta]")
        console.print("="*60)

        if self.team1.score > self.team2.score:
            console.print(f"[bold green]{self.team1.name} defeats {self.team2.name}![/bold green]")
        else:
            console.print(f"[bold green]{self.team2.name} defeats {self.team1.name}![/bold green]")

        console.print(f"\n[cyan]{self.team1.name}: {self.team1.score}[/cyan]")
        console.print(f"[yellow]{self.team2.name}: {self.team2.score}[/yellow]\n")

        # Show combined box score
        self.show_box_score()


@dataclass
class Season:
    """Manages a full season with schedule, standings, and stats tracking"""
    teams: Dict[str, Team]  # team_id -> Team object
    user_team_id: str  # Which team the user is following
    schedule: List[Tuple[str, str]] = None  # List of (team1_id, team2_id) matchups
    current_game_index: int = 0  # Which game we're on in the schedule
    standings: Dict[str, Dict] = None  # team_id -> {wins, losses, pct, ppg, opp_ppg}
    player_season_stats: Dict[str, Dict] = None  # "Team|PlayerName" -> {total_pts, total_reb, games, ...}

    def __post_init__(self):
        """Initialize season - generate schedule and empty standings"""
        # Initialize standings for each team
        self.standings = {}
        for team_id in self.teams.keys():
            self.standings[team_id] = {
                'wins': 0,
                'losses': 0,
                'pct': 0.0,
                'total_points_for': 0,
                'total_points_against': 0,
                'ppg': 0.0,
                'opp_ppg': 0.0,
                'games_played': 0
            }

        # Initialize player season stats tracking
        self.player_season_stats = {}

        # Generate round-robin schedule if not provided
        if self.schedule is None:
            self.schedule = self.generate_round_robin_schedule()

    def generate_round_robin_schedule(self) -> List[Tuple[str, str]]:
        """
        Generate a realistic weekly schedule where each team plays once per week
        Similar to real sports leagues (e.g., Premier League, NBA)
        """
        team_ids = list(self.teams.keys())
        num_teams = len(team_ids)
        schedule = []

        # Create all possible matchups
        all_matchups = []
        for i, team1_id in enumerate(team_ids):
            for team2_id in team_ids[i+1:]:
                all_matchups.append((team1_id, team2_id))

        # Shuffle matchups for variety
        random.shuffle(all_matchups)

        # Convert to a list we can remove from
        remaining_matchups = all_matchups.copy()

        # Organize into weeks where each team plays EXACTLY once per week
        while remaining_matchups:
            used_teams_this_week = set()
            current_week = []

            # Try to fit as many games as possible into this week
            # Each team can only play once per week
            matchups_to_remove = []

            for matchup in remaining_matchups:
                team1_id, team2_id = matchup

                # Check if both teams are available this week
                if team1_id not in used_teams_this_week and team2_id not in used_teams_this_week:
                    # Add this game to the week
                    current_week.append(matchup)
                    used_teams_this_week.add(team1_id)
                    used_teams_this_week.add(team2_id)
                    matchups_to_remove.append(matchup)

            # Remove scheduled matchups from remaining pool
            for matchup in matchups_to_remove:
                remaining_matchups.remove(matchup)

            # Add this week's games to the schedule
            schedule.extend(current_week)

        return schedule

    def get_sorted_standings(self) -> List[Tuple[str, Dict]]:
        """Return standings sorted by win percentage (best to worst)"""
        standings_list = [(team_id, data) for team_id, data in self.standings.items()]
        # Sort by: 1) Win%, 2) Point differential (PPG - OPP)
        standings_list.sort(key=lambda x: (x[1]['pct'], x[1]['ppg'] - x[1]['opp_ppg']), reverse=True)
        return standings_list

    def update_standings(self, team1_id: str, team1_score: int, team2_id: str, team2_score: int):
        """Update standings after a game"""
        # Update games played
        self.standings[team1_id]['games_played'] += 1
        self.standings[team2_id]['games_played'] += 1

        # Update points
        self.standings[team1_id]['total_points_for'] += team1_score
        self.standings[team1_id]['total_points_against'] += team2_score
        self.standings[team2_id]['total_points_for'] += team2_score
        self.standings[team2_id]['total_points_against'] += team1_score

        # Update wins/losses
        if team1_score > team2_score:
            self.standings[team1_id]['wins'] += 1
            self.standings[team2_id]['losses'] += 1
        else:
            self.standings[team2_id]['wins'] += 1
            self.standings[team1_id]['losses'] += 1

        # Recalculate percentages and averages
        for team_id in [team1_id, team2_id]:
            total_games = self.standings[team_id]['games_played']
            wins = self.standings[team_id]['wins']
            self.standings[team_id]['pct'] = wins / total_games if total_games > 0 else 0.0
            self.standings[team_id]['ppg'] = self.standings[team_id]['total_points_for'] / total_games if total_games > 0 else 0.0
            self.standings[team_id]['opp_ppg'] = self.standings[team_id]['total_points_against'] / total_games if total_games > 0 else 0.0

    def aggregate_player_stats(self, team_id: str, team: Team):
        """Aggregate player stats from a game into season totals"""
        for player in team.players:
            key = f"{team_id}|{player.name}"

            if key not in self.player_season_stats:
                # Initialize player season stats
                self.player_season_stats[key] = {
                    'team_id': team_id,
                    'player_name': player.name,
                    'position': player.position,
                    'games': 0,
                    'total_pts': 0,
                    'total_reb': 0,
                    'total_ast': 0,
                    'total_stl': 0,
                    'total_blk': 0,
                    'total_to': 0,
                    'total_fouls': 0,
                    'total_fgm': 0,
                    'total_fga': 0,
                    'total_ftm': 0,
                    'total_fta': 0,
                    'total_minutes': 0.0,
                    # Calculated averages (updated below)
                    'ppg': 0.0,
                    'rpg': 0.0,
                    'apg': 0.0,
                    'mpg': 0.0,
                    'fg_pct': 0.0,
                    'ft_pct': 0.0
                }

            stats = self.player_season_stats[key]

            # Only count game if player actually played
            if player.minutes_played > 0:
                stats['games'] += 1

            # Add game stats to totals
            stats['total_pts'] += player.points
            stats['total_reb'] += player.rebounds
            stats['total_ast'] += player.assists
            stats['total_stl'] += player.steals
            stats['total_blk'] += player.blocks
            stats['total_to'] += player.turnovers
            stats['total_fouls'] += player.fouls
            stats['total_fgm'] += player.fgm
            stats['total_fga'] += player.fga
            stats['total_ftm'] += player.ftm
            stats['total_fta'] += player.fta
            stats['total_minutes'] += player.minutes_played

            # Recalculate averages
            games = stats['games'] if stats['games'] > 0 else 1
            stats['ppg'] = stats['total_pts'] / games
            stats['rpg'] = stats['total_reb'] / games
            stats['apg'] = stats['total_ast'] / games
            stats['mpg'] = stats['total_minutes'] / games
            stats['fg_pct'] = (stats['total_fgm'] / stats['total_fga'] * 100) if stats['total_fga'] > 0 else 0.0
            stats['ft_pct'] = (stats['total_ftm'] / stats['total_fta'] * 100) if stats['total_fta'] > 0 else 0.0

    def is_season_complete(self) -> bool:
        """Check if all scheduled games have been played"""
        return self.current_game_index >= len(self.schedule)


def instant_sim_game(team1: Team, team2: Team):
    """
    Instantly generate a realistic game result without running possession-by-possession
    Much faster for bulk simulation
    Now uses usage rates for realistic shot distribution!
    Includes era penalty for cross-era matchups (older teams get shooting penalty vs newer teams)
    """
    team1.reset_for_new_game()
    team2.reset_for_new_game()

    # Calculate ERA-BASED ADJUSTMENTS for cross-era matchups
    # SHOOTING PENALTY: Older teams shoot worse (0.5% per decade, max 3.5%)
    # DEFENSE BASELINE: Era-based absolute defensive ability (not era-relative)

    # Shooting penalty for older teams
    year_gap = abs(team1.year - team2.year)
    shooting_penalty_pct = min(year_gap * 0.05, 3.5)  # 0.5% per decade, capped at 3.5%

    if team1.year < team2.year:
        team1_shooting_penalty = shooting_penalty_pct / 100.0
        team2_shooting_penalty = 0.0
    elif team2.year < team1.year:
        team1_shooting_penalty = 0.0
        team2_shooting_penalty = shooting_penalty_pct / 100.0
    else:
        team1_shooting_penalty = 0.0
        team2_shooting_penalty = 0.0

    # Era-based defense baseline adjustments (cross-era absolute ratings)
    # Ranking: 1) Early 3PT (1980-1999) 2) Slow Pace (2000-2016) 3) Modern (2017+) 4) Pre-3PT (1965-1979)
    def get_era_defense_adjustment(year):
        if year < 1980:
            return 0.08  # Pre-3PT era: Worst (primitive schemes despite physicality)
        elif year < 2000:
            return -0.05  # Early 3PT era: Best (hand-checking + sophisticated schemes)
        elif year < 2017:
            return 0.00  # Slow Pace era: Baseline (modern schemes, still physical)
        else:
            return 0.05  # Modern era: Third (best schemes/athletes, but offensive rules)

    # Apply era adjustments to defense ratings
    team1_opponent_def = team2.def_rating + get_era_defense_adjustment(team2.year)
    team2_opponent_def = team1.def_rating + get_era_defense_adjustment(team1.year)

    # Calculate expected possessions - BALANCED PACE
    # Simple average - both teams influence pace equally
    actual_pace = (team1.pace_rating + team2.pace_rating) / 2.0

    base_possessions = 95  # Average NBA possessions per team
    total_possessions = int(base_possessions * actual_pace * random.uniform(0.95, 1.05))

    # Small possession advantage for better defensive teams (force turnovers)
    team1_possession_bonus = int((1.0 - team1.def_rating) * 2)  # Reduced from 3 to 2
    team2_possession_bonus = int((1.0 - team2.def_rating) * 2)

    team1_possessions = total_possessions + team1_possession_bonus
    team2_possessions = total_possessions + team2_possession_bonus

    # Distribute possessions and shots to players based on USAGE RATE
    def distribute_player_stats(team, opponent_def_rating, team_possessions, era_penalty=0.0):
        """Distribute stats to players based on usage rate and minutes
        era_penalty: shooting % reduction for older teams facing newer teams (0.0 to 0.10)
        """
        team_total_points = 0

        # First pass: calculate total weighted usage to normalize
        # This ensures ALL possessions get distributed, even for balanced teams
        total_weighted_usage = 0.0
        for player in team.players:
            if player.minutes_pg > 10:
                minutes_ratio = min(1.0, player.minutes_pg / 48.0)
                total_weighted_usage += (player.usage_rate / 100.0) * minutes_ratio

        # Normalize factor - if usage doesn't sum to 100%, boost everyone proportionally
        usage_normalizer = 1.0 if total_weighted_usage >= 0.95 else (1.0 / total_weighted_usage)

        for player in team.players:
            if player.minutes_pg > 10:  # Only players with significant minutes
                # Minutes played (with variance)
                player.minutes_played = min(48.0, player.minutes_pg * random.uniform(0.9, 1.1))
                minutes_ratio = player.minutes_played / 48.0

                # Shot attempts based on USAGE RATE (normalized to ensure 100% usage)
                # Usage rate = % of team possessions used when player is on floor
                normalized_usage = (player.usage_rate / 100.0) * usage_normalizer
                player_possessions = normalized_usage * team_possessions * minutes_ratio

                # Estimate shot attempts (not all possessions end in shots - some are assists, turnovers)
                # Roughly 95% of possessions end in a shot attempt (more aggressive)
                shot_attempts = int(player_possessions * 0.95 * random.uniform(0.95, 1.05))

                # Split between 2PT and 3PT based on team's three_pt_rate
                # BUT only if player can actually shoot 3s (three_pt_pct > 0)
                if player.three_pt_pct > 0:
                    three_pt_attempts = int(shot_attempts * team.three_pt_rate)
                    two_pt_attempts = shot_attempts - three_pt_attempts
                else:
                    # Player doesn't shoot 3s - all shots are 2-pointers
                    three_pt_attempts = 0
                    two_pt_attempts = shot_attempts

                # Apply defense rating to shooting percentages - VERY LIGHT TOUCH
                # def_rating impact reduced to 25% to prevent over-suppression of scoring
                base_multiplier = opponent_def_rating
                def_impact = (base_multiplier - 1.0) * 0.25  # Only 25% of the defensive effect
                def_multiplier = 1.0 + def_impact
                # Bulls (0.85): def_impact = (0.85-1.0)*0.25 = -0.0375, multiplier = 0.9625 (3.75% reduction)
                # Average (1.00): def_impact = 0, multiplier = 1.00 (no change)
                # Warriors (1.05): def_impact = 0.0125, multiplier = 1.0125 (1.25% easier)

                # Apply era penalty (older teams vs newer teams) and defense
                effective_2pt_pct = (player.two_pt_pct / 100.0) * def_multiplier * (1.0 - era_penalty)
                effective_3pt_pct = (player.three_pt_pct / 100.0) * def_multiplier * (1.0 - era_penalty)

                # Calculate makes
                two_pt_makes = sum(1 for _ in range(two_pt_attempts) if random.random() < effective_2pt_pct)
                three_pt_makes = sum(1 for _ in range(three_pt_attempts) if random.random() < effective_3pt_pct)

                player.fga = shot_attempts
                player.fgm = two_pt_makes + three_pt_makes

                # Free throws based on usage and aggression
                player.fta = int(player.fta_pg * minutes_ratio * random.uniform(0.8, 1.2))
                player.ftm = sum(1 for _ in range(player.fta) if random.random() < (player.ft_pct / 100.0))

                # Calculate points
                player.points = (two_pt_makes * 2) + (three_pt_makes * 3) + player.ftm
                team_total_points += player.points

                # Other stats (scaled by minutes and usage)
                usage_factor = (player.usage_rate / 20.0)  # Normalize around 20% usage
                player.rebounds = int(player.rpg * minutes_ratio * random.uniform(0.8, 1.2))
                player.assists = int(player.apg * minutes_ratio * random.uniform(0.8, 1.2))
                player.steals = int(random.randint(0, 3) if minutes_ratio > 0.5 else 0)
                player.blocks = int(random.randint(0, 2) if player.position in ['C', 'PF'] else 0)
                player.turnovers = int(player_possessions * 0.12 * random.uniform(0.8, 1.2))  # ~12% turnover rate
                player.fouls = int(minutes_ratio * random.randint(1, 4))

        return team_total_points

    # Distribute stats for both teams (with era penalties applied)
    # opponent_def includes defense penalty for newer teams vs older teams
    team1.score = distribute_player_stats(team1, team1_opponent_def, team1_possessions, team1_shooting_penalty)
    team2.score = distribute_player_stats(team2, team2_opponent_def, team2_possessions, team2_shooting_penalty)

    # Handle ties - add overtime points to one team
    if team1.score == team2.score:
        # Random overtime winner, add 3-8 points
        overtime_points = random.randint(3, 8)
        if random.random() < 0.5:
            team1.score += overtime_points
            team2.score += random.randint(1, overtime_points - 1)
        else:
            team2.score += overtime_points
            team1.score += random.randint(1, overtime_points - 1)


def play_season_game_day(season: Season, game_speed: float = 0.6):
    """
    Play the next user's game - will search through multiple weeks if needed
    Silently sims any intervening weeks where user's team has a bye
    Returns True if there are more games, False if season is complete
    """
    if season.is_season_complete():
        return False

    # Keep searching through weeks until we find user's next game
    all_other_games_results = []
    user_game_played = False

    while not user_game_played and not season.is_season_complete():
        # Collect this week's games (until we see a team that already played)
        teams_in_week = set()
        week_games = []
        user_game_in_week = None
        user_game_index = None

        for i in range(season.current_game_index, len(season.schedule)):
            team1_id, team2_id = season.schedule[i]

            # Stop if either team already played this week
            if team1_id in teams_in_week or team2_id in teams_in_week:
                break

            # Add this game to the week
            week_games.append((i, team1_id, team2_id))
            teams_in_week.add(team1_id)
            teams_in_week.add(team2_id)

            # Check if this is the user's game
            if team1_id == season.user_team_id or team2_id == season.user_team_id:
                user_game_in_week = (i, team1_id, team2_id)
                user_game_index = i

        # If user's team is in this week, PLAY THEIR GAME FIRST
        if user_game_in_week:
            i, team1_id, team2_id = user_game_in_week
            team1 = season.teams[team1_id]
            team2 = season.teams[team2_id]

            console.print(f"\n[bold cyan]{'='*60}[/bold cyan]")
            console.print(f"[bold]YOUR GAME: {team1.name} vs {team2.name}[/bold]")
            console.print(f"[bold cyan]{'='*60}[/bold cyan]\n")

            # Ask for game speed
            console.print("[bold cyan]Game Speed:[/bold cyan]")
            console.print("  1. Cinema (3.5s)  2. Slow (1.2s)  3. Normal (0.6s)  4. Fast (0.3s)  5. Simulate (0.05s)")
            speed_choice = Prompt.ask("Select speed", choices=["1", "2", "3", "4", "5"], default=str(int(game_speed * 2) if game_speed == 0.6 else "5"))
            speed_map = {"1": 3.5, "2": 1.2, "3": 0.6, "4": 0.3, "5": 0.05}
            selected_speed = speed_map[speed_choice]

            team1.reset_for_new_game()
            team2.reset_for_new_game()

            game = GameSimulation(team1, team2, game_speed=selected_speed)
            game.simulate_game()

            # Update standings
            season.update_standings(team1_id, team1.score, team2_id, team2.score)

            # Aggregate player stats
            season.aggregate_player_stats(team1_id, team1)
            season.aggregate_player_stats(team2_id, team2)

            season.current_game_index += 1
            user_game_played = True

        # NOW AUTO-SIM OTHER GAMES in this week (whether user played or not)
        # Collect games to simulate (all games in week, excluding user's game if they played)
        games_to_sim = [game for game in week_games if game[0] != user_game_index]

        if games_to_sim:
            # Silent background simulation (no output during sim)
            for game_idx, team1_id, team2_id in games_to_sim:
                team1 = season.teams[team1_id]
                team2 = season.teams[team2_id]

                # Use instant sim for speed
                instant_sim_game(team1, team2)

                # Update standings
                season.update_standings(team1_id, team1.score, team2_id, team2.score)

                # Aggregate player stats
                season.aggregate_player_stats(team1_id, team1)
                season.aggregate_player_stats(team2_id, team2)

                # Find top scorer from each team
                team1_top = max(team1.players, key=lambda p: p.points)
                team2_top = max(team2.players, key=lambda p: p.points)

                winner = team1.name if team1.score > team2.score else team2.name
                all_other_games_results.append({
                    'team1_name': team1.name,
                    'team1_score': team1.score,
                    'team1_top': f"{team1_top.name} {team1_top.points}pts",
                    'team2_name': team2.name,
                    'team2_score': team2.score,
                    'team2_top': f"{team2_top.name} {team2_top.points}pts",
                    'winner': winner
                })

                season.current_game_index += 1

    # Display all other game results in a nice table (including any from bye weeks)
    if all_other_games_results:
        console.print("\n[bold cyan]Other Games Results:[/bold cyan]\n")
        results_table = Table(box=box.ROUNDED)
        results_table.add_column("Matchup", style="green")
        results_table.add_column("Score", justify="center", style="yellow")
        results_table.add_column("Top Scorers", style="dim")

        for result in all_other_games_results:
            matchup = f"{result['team1_name']} vs {result['team2_name']}"
            score = f"{result['team1_score']} - {result['team2_score']}"
            scorers = f"{result['team1_top']} | {result['team2_top']}"
            results_table.add_row(matchup, score, scorers)

        console.print(results_table)

    return not season.is_season_complete()


def show_standings(season: Season):
    """Display current season standings"""
    console.print("\n[bold cyan]═══ SEASON STANDINGS ═══[/bold cyan]\n")

    standings = season.get_sorted_standings()

    table = Table(box=box.ROUNDED)
    table.add_column("Rank", justify="right", style="cyan")
    table.add_column("Team", style="green")
    table.add_column("W", justify="right")
    table.add_column("L", justify="right")
    table.add_column("PCT", justify="right", style="yellow")
    table.add_column("PPG", justify="right")
    table.add_column("OPP", justify="right")

    for rank, (team_id, data) in enumerate(standings, 1):
        team_name = season.teams[team_id].name
        # Highlight user's team
        if team_id == season.user_team_id:
            team_name = f"[bold]{team_name}[/bold]"

        table.add_row(
            str(rank),
            team_name,
            str(data['wins']),
            str(data['losses']),
            f"{data['pct']:.3f}",
            f"{data['ppg']:.1f}",
            f"{data['opp_ppg']:.1f}"
        )

    console.print(table)


def show_stats_leaders(season: Season, stat: str = 'ppg', limit: int = 10):
    """Display season stats leaders"""
    stat_names = {
        'ppg': 'Points Per Game',
        'rpg': 'Rebounds Per Game',
        'apg': 'Assists Per Game',
        'fg_pct': 'Field Goal %',
        'mpg': 'Minutes Per Game'
    }

    console.print(f"\n[bold cyan]═══ {stat_names.get(stat, stat.upper())} LEADERS ═══[/bold cyan]\n")

    # Filter players who have played at least 1 game
    players = [(k, v) for k, v in season.player_season_stats.items() if v['games'] > 0]

    # Sort by the requested stat
    players.sort(key=lambda x: x[1][stat], reverse=True)

    table = Table(box=box.ROUNDED)
    table.add_column("Rank", justify="right", style="cyan")
    table.add_column("Player", style="green")
    table.add_column("Team", style="yellow")
    table.add_column("GP", justify="right")
    table.add_column(stat.upper(), justify="right", style="bold")

    for rank, (key, stats) in enumerate(players[:limit], 1):
        team_name = season.teams[stats['team_id']].name
        table.add_row(
            str(rank),
            stats['player_name'],
            team_name,
            str(stats['games']),
            f"{stats[stat]:.1f}" if stat != 'fg_pct' else f"{stats[stat]:.1f}%"
        )

    console.print(table)


def show_my_team_stats(season: Season):
    """Display full season stats for user's team"""
    user_team_name = season.teams[season.user_team_id].name
    console.print(f"\n[bold cyan]═══ {user_team_name} SEASON STATS ═══[/bold cyan]\n")

    # Get all players from user's team who have played
    team_players = []
    for key, stats in season.player_season_stats.items():
        if stats['team_id'] == season.user_team_id and stats['games'] > 0:
            team_players.append(stats)

    # Sort by PPG
    team_players.sort(key=lambda x: x['ppg'], reverse=True)

    table = Table(box=box.ROUNDED)
    table.add_column("Player", style="green")
    table.add_column("POS", justify="center", style="yellow")
    table.add_column("GP", justify="right")
    table.add_column("MPG", justify="right")
    table.add_column("PPG", justify="right", style="bold")
    table.add_column("RPG", justify="right")
    table.add_column("APG", justify="right")
    table.add_column("FG%", justify="right")
    table.add_column("FT%", justify="right")
    table.add_column("STL", justify="right")
    table.add_column("BLK", justify="right")
    table.add_column("TO", justify="right")
    table.add_column("PF", justify="right")

    for stats in team_players:
        table.add_row(
            stats['player_name'],
            stats['position'],
            str(stats['games']),
            f"{stats['mpg']:.1f}",
            f"{stats['ppg']:.1f}",
            f"{stats['rpg']:.1f}",
            f"{stats['apg']:.1f}",
            f"{stats['fg_pct']:.1f}",
            f"{stats['ft_pct']:.1f}",
            f"{stats['total_stl'] / stats['games']:.1f}" if stats['games'] > 0 else "0.0",
            f"{stats['total_blk'] / stats['games']:.1f}" if stats['games'] > 0 else "0.0",
            f"{stats['total_to'] / stats['games']:.1f}" if stats['games'] > 0 else "0.0",
            f"{stats['total_fouls'] / stats['games']:.1f}" if stats['games'] > 0 else "0.0"
        )

    console.print(table)

    # Show team record
    team_standing = season.standings[season.user_team_id]
    console.print(f"\n[bold]Team Record:[/bold] {team_standing['wins']}-{team_standing['losses']} ({team_standing['pct']:.3f})")
    console.print(f"[bold]Team PPG:[/bold] {team_standing['ppg']:.1f}")
    console.print(f"[bold]Opp PPG:[/bold] {team_standing['opp_ppg']:.1f}")


def season_mode_menu(season: Season, game_speed: float):
    """Interactive menu for season mode"""
    while True:
        console.print("\n[bold cyan]═══ SEASON MODE MENU ═══[/bold cyan]")
        console.print(f"Games Played: {season.current_game_index}/{len(season.schedule)}")
        console.print(f"Your Team: [bold]{season.teams[season.user_team_id].name}[/bold]\n")

        console.print("  1. Play Next Game")
        console.print("  2. View Standings")
        console.print("  3. View My Team Stats")
        console.print("  4. Stats Leaders (PPG)")
        console.print("  5. Stats Leaders (RPG)")
        console.print("  6. Stats Leaders (APG)")
        console.print("  7. Simulate Rest of Season")
        console.print("  8. Exit Season Mode\n")

        choice = Prompt.ask("Select option", choices=["1", "2", "3", "4", "5", "6", "7", "8"], default="1")

        if choice == "1":
            # Play next game day
            has_more_games = play_season_game_day(season, game_speed)
            if not has_more_games:
                console.print("\n[bold green]SEASON COMPLETE![/bold green]")
                show_standings(season)
                console.print("\n[bold]Final season standings shown above.[/bold]")
                break
        elif choice == "2":
            show_standings(season)
        elif choice == "3":
            show_my_team_stats(season)
        elif choice == "4":
            show_stats_leaders(season, 'ppg')
        elif choice == "5":
            show_stats_leaders(season, 'rpg')
        elif choice == "6":
            show_stats_leaders(season, 'apg')
        elif choice == "7":
            # Sim rest of season (INSTANT - no display)
            console.print("\n[yellow]Simulating remaining games...[/yellow]")

            # Grab remaining games and instant sim them
            remaining_games = season.schedule[season.current_game_index:]
            games_simmed = len(remaining_games)

            for team1_id, team2_id in remaining_games:
                team1 = season.teams[team1_id]
                team2 = season.teams[team2_id]

                instant_sim_game(team1, team2)

                season.update_standings(team1_id, team1.score, team2_id, team2.score)
                season.aggregate_player_stats(team1_id, team1)
                season.aggregate_player_stats(team2_id, team2)

                season.current_game_index += 1

            console.print(f"\n[bold green]SEASON COMPLETE! ({games_simmed} games simulated)[/bold green]")
            show_standings(season)
            # DON'T break - return to menu so user can view stats
        elif choice == "8":
            break


def select_starting_lineup(team: Team) -> List[int]:
    """
    Allow user to manually select starting 5 players
    Returns list of 5 player indices
    """
    # Display full roster
    console.print(f"[bold]{team.name} Roster[/bold]\n")

    roster_table = Table(box=box.ROUNDED)
    roster_table.add_column("#", justify="right", style="cyan")
    roster_table.add_column("Player", style="green")
    roster_table.add_column("POS", justify="center", style="yellow")
    roster_table.add_column("PPG", justify="right")
    roster_table.add_column("RPG", justify="right")
    roster_table.add_column("APG", justify="right")
    roster_table.add_column("MPG", justify="right")

    for i, player in enumerate(team.players, 1):
        roster_table.add_row(
            str(i),
            player.name,
            player.position,
            f"{player.ppg:.1f}",
            f"{player.rpg:.1f}",
            f"{player.apg:.1f}",
            f"{player.minutes_pg:.1f}"
        )

    console.print(roster_table)
    console.print()

    # Get user selection
    while True:
        console.print("[bold cyan]Enter 5 numbers separated by spaces (e.g., 1 2 3 4 5):[/bold cyan]")
        selection = console.input("[bold]Your starting 5: [/bold]")

        try:
            # Parse input
            indices = [int(x) - 1 for x in selection.strip().split()]  # Convert to 0-indexed

            # Validate
            if len(indices) != 5:
                console.print(f"[red]Error: You selected {len(indices)} players. Please select exactly 5.[/red]\n")
                continue

            if any(i < 0 or i >= len(team.players) for i in indices):
                console.print(f"[red]Error: Invalid player number. Choose from 1-{len(team.players)}[/red]\n")
                continue

            if len(set(indices)) != 5:
                console.print("[red]Error: You selected the same player multiple times.[/red]\n")
                continue

            # Show selected lineup for confirmation
            console.print("\n[bold green]Your Starting 5:[/bold green]")
            for idx in indices:
                player = team.players[idx]
                console.print(f"  {player.position:3s} - {player.name} ({player.ppg:.1f} PPG)")

            # Check for position balance (warn but don't force)
            positions = [team.players[i].position for i in indices]
            position_counts = {pos: positions.count(pos) for pos in set(positions)}

            if any(count >= 3 for count in position_counts.values()):
                console.print("\n[yellow]Warning: You have 3+ players at the same position.[/yellow]")

            missing_positions = set(['PG', 'SG', 'SF', 'PF', 'C']) - set(positions)
            if missing_positions:
                console.print(f"[yellow]Note: No {', '.join(missing_positions)} in starting lineup[/yellow]")

            # Confirm
            confirm = Prompt.ask("\n[bold cyan]Confirm this lineup?[/bold cyan]", choices=["y", "n"], default="y")

            if confirm.lower() == "y":
                return indices
            else:
                console.print()  # Blank line before retry

        except ValueError:
            console.print("[red]Error: Invalid input. Please enter numbers only (e.g., 1 2 3 4 5)[/red]\n")
            continue


def main():
    """Main game loop"""
    console.print("[bold magenta]═══════════════════════════════════════════[/bold magenta]")
    console.print("[bold cyan]  CLASSIC NBA TEXT BASKETBALL SIMULATOR  [/bold cyan]")
    console.print("[bold magenta]═══════════════════════════════════════════[/bold magenta]\n")

    # Load teams once
    try:
        teams_data = load_teams_from_csv()
        console.print(f"[green]Loaded {len(teams_data)} teams from database[/green]\n")
    except FileNotFoundError:
        console.print("[red]Error: Could not find teams.csv or players.csv[/red]")
        console.print("[yellow]Make sure the CSV files are in the same directory as this script.[/yellow]")
        return

    # Main game loop
    while True:
        # Ask for game mode
        console.print("\n[bold cyan]Select Game Mode:[/bold cyan]")
        console.print("  1. Single Game - Watch two teams play")
        console.print("  2. Season Mode - Follow your team through a full season")
        console.print("  3. User vs Computer - YOU control a team!\n")

        mode_choice = Prompt.ask("Select mode", choices=["1", "2", "3"], default="1")

        if mode_choice == "2":
            # SEASON MODE
            console.print("\n[bold cyan]═══ SEASON MODE SETUP ═══[/bold cyan]\n")

            # Select user's team
            console.print("[bold]Select your team to manage:[/bold]")
            user_team = select_team(teams_data, 1)
            user_team_id = None

            # Find the team_id for the selected team
            for tid, tdata in teams_data.items():
                if tdata['name'] == user_team.name and tdata['year'] == user_team.year:
                    user_team_id = tid
                    break

            if user_team_id is None:
                console.print("[red]Error: Could not find team ID[/red]")
                continue

            # Create Team objects for all teams
            season_teams = {}
            for team_id, data in teams_data.items():
                season_teams[team_id] = Team(
                    data['name'],
                    data['players'],
                    data['pace_rating'],
                    data['three_pt_rate'],
                    data['def_rating'],
                    data['year']
                )

            # Create season
            season = Season(teams=season_teams, user_team_id=user_team_id)

            console.print(f"\n[green]Season created![/green]")
            console.print(f"Teams: {len(season.teams)}")
            console.print(f"Games: {len(season.schedule)}")
            console.print(f"Your Team: [bold]{season.teams[user_team_id].name}[/bold]\n")

            # Ask for game speed
            console.print("\n[bold cyan]Game Speed (for your team's games):[/bold cyan]")
            console.print("  1. Cinema (3.5s)")
            console.print("  2. Slow (1.2s)")
            console.print("  3. Normal (0.6s)")
            console.print("  4. Fast (0.3s)")
            console.print("  5. Simulate (0.05s)\n")

            speed_choice = Prompt.ask("Select speed", choices=["1", "2", "3", "4", "5"], default="3")
            speed_map = {"1": 3.5, "2": 1.2, "3": 0.6, "4": 0.3, "5": 0.05}
            game_speed = speed_map[speed_choice]

            # Enter season mode menu
            season_mode_menu(season, game_speed)

            # After season ends, ask if they want to play again
            play_again = Prompt.ask("\n[bold cyan]Return to main menu?[/bold cyan]", choices=["y", "n"], default="y")
            if play_again.lower() != "y":
                break

        elif mode_choice == "3":
            # USER VS COMPUTER MODE
            console.print("\n[bold cyan]═══ USER VS COMPUTER MODE ═══[/bold cyan]\n")

            # Select user's team
            console.print("[bold]Select YOUR team:[/bold]")
            user_team = select_team(teams_data, 1)

            # Select opponent
            console.print("\n[bold]Select your opponent:[/bold]")
            cpu_team = select_team(teams_data, 2)

            console.print(f"\n[bold green]YOU: {user_team.name}[/bold green] vs [bold yellow]CPU: {cpu_team.name}[/bold yellow]")

            # Manual starting lineup selection
            console.print("\n[bold cyan]═══ SELECT YOUR STARTING 5 ═══[/bold cyan]\n")
            starting_indices = select_starting_lineup(user_team)

            # Ask for game speed
            console.print("\n[bold cyan]Game Speed:[/bold cyan]")
            console.print("  1. Cinema (3.5s) - Watch every play unfold")
            console.print("  2. Slow (1.2s) - Comfortable viewing")
            console.print("  3. Normal (0.6s) - Balanced")
            console.print("  4. Fast (0.3s) - Quick game")
            console.print("  5. Simulate (0.05s) - Instant results (you still make all decisions)")

            speed_choice = Prompt.ask(
                "\nSelect speed",
                choices=["1", "2", "3", "4", "5"],
                default="3"
            )
            speed_map = {"1": 3.5, "2": 1.2, "3": 0.6, "4": 0.3, "5": 0.05}
            game_speed = speed_map[speed_choice]

            console.print("\n[green]Starting game...[/green]\n")
            time.sleep(2)

            # Reset all stats for both teams
            user_team.reset_for_new_game()
            cpu_team.reset_for_new_game()

            # Override user team's starting lineup with manual selection
            user_team.on_court_indices = starting_indices

            # Create interactive game
            game = InteractiveGame(user_team, cpu_team, game_speed=game_speed)

            try:
                game.simulate_game()
            except KeyboardInterrupt:
                console.print("\n[yellow]Game interrupted by user[/yellow]")

            # Ask if player wants to play again
            play_again = Prompt.ask(
                "\n[bold cyan]Play another game?[/bold cyan]",
                choices=["y", "n"],
                default="y"
            )

            if play_again.lower() != "y":
                break

            console.print("\n" + "="*60 + "\n")

        else:
            # SINGLE GAME MODE
            # Select teams
            team1 = select_team(teams_data, 1)
            team2 = select_team(teams_data, 2)

            console.print(f"\n[bold]{team1.name}[/bold] vs [bold]{team2.name}[/bold]")
            console.print("[dim]Press Ctrl+C to quit anytime[/dim]\n")

            # Ask for game speed
            console.print("\n[bold cyan]Game Speed:[/bold cyan]")
            console.print("  1. Cinema (3.5s) - Watch every play unfold")
            console.print("  2. Slow (1.2s) - Comfortable viewing")
            console.print("  3. Normal (0.6s) - Balanced")
            console.print("  4. Fast (0.3s) - Quick game")
            console.print("  5. Simulate (0.05s) - Instant results")

            speed_choice = Prompt.ask(
                "\nSelect speed",
                choices=["1", "2", "3", "4", "5"],
                default="3"
            )
            speed_map = {"1": 3.5, "2": 1.2, "3": 0.6, "4": 0.3, "5": 0.05}
            game_speed = speed_map[speed_choice]

            console.print("\n[green]Starting game...[/green]\n")
            time.sleep(2)

            # Reset all stats for both teams (important for play-again)
            team1.reset_for_new_game()
            team2.reset_for_new_game()

            game = GameSimulation(team1, team2, game_speed=game_speed)

            try:
                game.simulate_game()
            except KeyboardInterrupt:
                console.print("\n[yellow]Game interrupted by user[/yellow]")

            # Ask if player wants to play again
            play_again = Prompt.ask(
                "\n[bold cyan]Play another game?[/bold cyan]",
                choices=["y", "n"],
                default="y"
            )

            if play_again.lower() != "y":
                break

            console.print("\n" + "="*60 + "\n")

    console.print("\n[bold]Thanks for playing![/bold]")


if __name__ == "__main__":
    main()
