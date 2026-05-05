# Classic Basketball Simulator — Free Edition (Mac)

A nostalgic text-based basketball simulation featuring cross-era matchups with legendary teams!

## What's Included

- `Basketball-Sim-Free` — the game (Mac binary)
- `teams_free.csv` — team database (24 legendary rosters)
- `players.csv` — 370+ players with historical statistics

## How to Run (Mac)

1. Unzip all three files into the same folder
2. Open **Terminal** and navigate to that folder:
   ```
   cd ~/Downloads/Basketball-Sim-Free
   ```
3. Make the file executable (first time only):
   ```
   chmod +x Basketball-Sim-Free
   ```
4. Run the game:
   ```
   ./Basketball-Sim-Free
   ```

## Teams Available (24 Championship Rosters)

### Pre-3PT Era (1965–1979)
- 1965 Boston (Russell Dynasty)
- 1970 New York (Clyde & The Captain)
- 1971 Milwaukee (Kareem's First Ring)
- 1972 Los Angeles (33-Game Streak)

### Early 3PT Era (1980–1999)
- 1983 Philadelphia (Moses Malone)
- 1986 Boston (Bird, McHale, Parish)
- 1987 Los Angeles (Showtime)
- 1989 Detroit (Bad Boys)
- 1993 Chicago (First Three-Peat)
- 1994 Houston (Hakeem's Dream)
- 1996 Chicago (72-10 Season)
- 1998 Utah (Stockton & Malone)

### Slow Pace Era (2000–2016)
- 2000 Los Angeles (Shaq & Kobe)
- 2009 Los Angeles (Kobe's 4th Ring)
- 2011 Dallas (Dirk's Revenge)
- 2013 Miami (LeBron's 2nd Title)
- 2014 San Antonio (Beautiful Game)
- 2016 Cleveland (The Block, The Shot)

### Modern Era (2017–2024)
- 2017 Golden State (Durant Joins)
- 2021 Milwaukee (Giannis's Title Run)
- 2023 Denver (Jokic's Masterpiece)
- 2024 Boston (Banner 18)
- 2024 Oklahoma City (Best Record in West)

## Game Modes

### Interactive Mode (User vs Computer)
- Choose your team and face off against CPU
- Select your starting lineup
- Make every decision — pass, shoot 2PT/3PT, substitutions
- Real basketball rules — shot clock, fouls, free throws, crunch time
- Halftime stats and full box scores

### Single Game (Simulation)
- Pick any two teams for a head-to-head matchup
- Live play-by-play with 5 speed settings (Cinema to Instant)
- Detailed box scores and player stats

## Customize Teams & Players

The CSV files are fully editable — open them in Excel or any text editor.

**teams_free.csv format:**
```csv
team_id,team_name,year,display_name,pace_rating,three_pt_rate,def_rating
bulls_96,Chicago,1996,1996 Chicago (72-10 Season),0.92,0.18,0.85
```

**players.csv format:**
```csv
team_id,player_name,fg_pct,ft_pct,rpg,apg,position,two_pt_pct,three_pt_pct,minutes_pg,ppg,fta_pg,usage_rate
bulls_96,Michael Jordan,49.5,83.4,6.6,4.3,SG,51.5,42.7,37.7,30.4,7.4,33.1
```

Add as many teams and players as you want!

## Cross-Era Balance System

The simulator applies adjustments so matchups across eras are competitive and fair:

- **Era-based defense ratings** — hand-checking era (1980s–90s) vs modern freedom of movement
- **Shooting penalties** — older teams face a small FG% dip vs much newer opponents (0.5% per decade, max 3.5%)
- **Shot distribution** — players with 0% 3PT shooting (Wilt, Kareem, etc.) never attempt threes

## Recent Changes

### v2.3.0
- **Instant sim engine overhaul** — replaced mathematical formula with silent live sim (same possession logic as live game, just no UI); fixes era imbalance in repeated simulations
- **Playmaker value system** — high-assist players boost teammate shooting (Magic Johnson: +3.5%, Stockton: +3.2%)
- **Starting lineup fix** — lineups now based on minutes per game, not PPG
- **Bug fixes** — possession switching after putbacks, pass chain repetition, crash on unhashable player in pass tracking

## Credits

All player statistics sourced from Basketball Reference. Developed with passion for basketball history.

Enjoy the greatest matchups that never happened!
