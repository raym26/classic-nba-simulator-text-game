# Classic NBA Text Basketball Simulator

A nostalgic text-based basketball simulation game featuring cross-era matchups!

## What's Included

- **basketball_sim_v2.py** - The main game program
- **teams.csv** - Database of 23 legendary NBA teams
- **players.csv** - 360+ player rosters with historical statistics

## Teams Available (23 Championship Teams)

### Pre-3PT Era (1965-1979)
- 1965 Boston Celtics (Bill Russell dynasty)
- 1970 New York Knicks (Clyde & The Captain)
- 1971 Milwaukee Bucks (Kareem's first ring)
- 1972 Los Angeles Lakers (33-game win streak)

### Early 3PT Era (1980-1999)
- 1983 Philadelphia 76ers (Moses Malone)
- 1985 Chicago Bulls (Rookie Michael Jordan)
- 1986 Boston Celtics (Bird, McHale, Parish)
- 1987 Los Angeles Lakers (Showtime - Magic & Kareem)
- 1989 Detroit Pistons (Bad Boys)
- 1993 Chicago Bulls (First three-peat)
- 1994 Houston Rockets (Hakeem's Dream)
- 1996 Chicago Bulls (72-10 season!)
- 1998 Utah Jazz (Stockton & Malone)

### Slow Pace Era (2000-2016)
- 2000 Los Angeles Lakers (Shaq & Kobe dynasty begins)
- 2009 Los Angeles Lakers (Kobe's 4th ring)
- 2011 Dallas Mavericks (Dirk's revenge)
- 2013 Miami Heat (LeBron's 2nd title)
- 2014 San Antonio Spurs (Beautiful game)
- 2016 Cleveland Cavaliers (The Block, The Shot)

### Modern Era (2017-2024)
- 2017 Golden State Warriors (Durant joins the dynasty)
- 2023 Denver Nuggets (Jokic's masterpiece)
- 2024 Boston Celtics (Banner 18)
- 2024 Oklahoma City Thunder (Best record in West)

## How to Run

1. Make sure you have Python 3 installed
2. Install the required library:
   ```
   pip install rich
   ```
3. Put all files in the same folder
4. Run:
   ```
   python basketball_sim_v2.py
   ```

## Features

### Core Gameplay
✅ **23 legendary teams** spanning 6 decades of NBA history
✅ **360+ players** with authentic historical statistics
✅ **Full 4-quarter games** with live play-by-play commentary
✅ **Season mode** - Play or simulate full 22-game seasons
✅ **Instant simulation** - Fast-forward through seasons
✅ **5 speed settings** - From Cinema (3.5s) to Instant (0.05s)

### Advanced Simulation
✅ **Cross-era matchup system** - Balanced adjustments for fair competition across eras
✅ **Usage rate distribution** - Star players get appropriate shot attempts
✅ **Intelligent rotations** - Minutes managed based on player tier and game flow
✅ **Foul tracking** - Personal fouls, team fouls, bonus situations, foul outs
✅ **Defensive stats** - Steals, blocks, turnovers tracked
✅ **Team aggregate stats** - Full box scores with team totals
✅ **Point differential tiebreaker** - Standings sorted by Win%, then +/-

### Cross-Era Balance System
The simulator implements sophisticated cross-era adjustments to ensure fair competition:

**Era-Based Defense Adjustments:**
- **Early 3PT Era (1980-1999):** -0.05 bonus (hand-checking + sophisticated schemes = best defense)
- **Slow Pace Era (2000-2016):** +0.00 baseline (modern schemes, still physical)
- **Modern Era (2017-2024):** +0.05 penalty (offensive-friendly rules)
- **Pre-3PT Era (1965-1979):** +0.08 penalty (primitive schemes despite physicality)

**Shooting Penalties:**
- Older teams face small shooting penalties vs newer opponents (0.5% per decade, max 3.5%)
- Accounts for athletic evolution and rule changes

**Shot Distribution Fix:**
- Players with 0% 3PT shooting (Wilt, Kareem, Duncan, etc.) no longer forced to take 3-pointers
- Ensures old-school big men perform at their true efficiency

## Game Modes

### 1. Interactive Mode (User vs Computer) ⭐ NEW!
- **You control the action** - Choose your team and face off against CPU
- **Select starting lineup** - Pick your best 5 before tip-off
- **Make every decision** - Pass, shoot 2PT/3PT, substitutions
- **Real basketball rules** - Shot clock, fouls, free throws, crunch time
- **Halftime stats** - Review team and player performance at the half
- **Complete box scores** - Full game stats at the end
- Available for both single games and season mode

### 2. Single Game (Simulation)
- Choose any two teams for a head-to-head matchup
- Full play-by-play or instant simulation
- Detailed box scores and player stats
- 5 speed settings from Cinema (3.5s) to Instant (0.05s)

### 3. Season Mode
- Select your team and compete in a 22-game season
- Play your games live or simulate
- Season standings with Win%, PPG, OPP, point differential
- Track player season averages

## How to Add Your Own Teams

Edit the CSV files to add custom teams and players:

**teams.csv format:**
```csv
team_id,team_name,year,display_name,pace_rating,three_pt_rate,def_rating
bulls_96,Bulls,1996,1996 Bulls,0.92,0.18,0.85
```

**players.csv format:**
```csv
team_id,player_name,fg_pct,ft_pct,rpg,apg,position,two_pt_pct,three_pt_pct,minutes_pg,ppg,fta_pg,usage_rate
bulls_96,Michael Jordan,49.5,83.4,6.6,4.3,SG,51.5,42.7,37.7,30.4,7.4,33.1
```

You can add as many teams and players as you want!

## Technical Notes

### Usage Rate Adjustments
**Note:** Usage rates represent the % of team possessions a player uses when on the floor. Manual adjustments were made for certain stars to ensure proper shot distribution:

**2000 Lakers:**
- Shaquille O'Neal: Boosted to 35% (co-star with Kobe)
- Kobe Bryant: Boosted to 32% (co-star with Shaq)

**2011 Mavericks:**
- Dirk Nowitzki: Boosted to 30% (primary star)

**2014 Spurs:**
- Tony Parker: Boosted to 25% (floor general)
- Tim Duncan: Boosted to 23% (low-post anchor)
- Manu Ginobili: Boosted to 21% (HOF sixth man)
- Kawhi Leonard: Kept at 14.1% (rising star)

These adjustments ensure championship teams with balanced scoring (no 30+ PPG scorer) still have appropriate offensive hierarchy.

### Rotation System
The simulator uses intelligent minute management:
- **Superstars (35+ MPG):** Very consistent minutes (±1.5 min variance)
- **Starters & Elite 6th Men (20-34 MPG):** Consistent minutes (±2.5 min variance)
- **Role Players (12-19 MPG):** Matchup-dependent (±4.0 min variance)
- **Deep Bench (<12 MPG):** High variance (±5.0 min variance)

Starting lineups are determined by PPG, ensuring top scorers get priority regardless of CSV order.

## Recent Improvements

### v2.2 (Latest - MVP Release)
✅ **Interactive Mode (User vs Computer)** - Full gameplay with manual control
  - Choose your team and opponent
  - Select starting lineup
  - Make play-by-play decisions (pass, shoot 2PT/3PT)
  - Substitutions between quarters
  - Halftime stats review
  - Complete box scores
✅ **UX Polish** - Single keypress input, clean screen transitions
✅ **Play-by-Play Display** - Reduced to 3 most recent plays for clarity
✅ **Shot Clock System** - 24-second enforcement with 14-second reset on offensive rebounds
✅ **Complete Foul System** - Free throws, bonus, foul outs, crunch time logic

### v2.1
✅ Fixed critical bug where non-3PT shooters were taking 3-pointers
✅ Implemented cross-era balance system (shooting + defense adjustments)
✅ Added point differential tiebreaker to standings
✅ Improved rotation consistency for elite 6th men
✅ UI enhancement: Play-by-play now displays under score line
✅ Cinema mode speed increased to 3.5s for better readability
✅ Starting lineups now based on PPG instead of CSV order

## Roadmap - Future Enhancements

### High Priority
- **Timeout system** - Strategic timeout calls with play diagrams
- **Varied play descriptions** - "Jordan slams it home!", "Pippen with the floater!"
- **Season mode integration** - Play your team's games interactively in a full season
- **Save/replay games** - Export game logs and season results
- **Defensive play calling** - User controls defensive strategy

### Medium Priority
- **Playoff bracket mode** - 8-team tournament simulation
- **Advanced stats** - PER, TS%, +/-, Win Shares
- **Custom sliders** - User-adjustable balance settings
- **Head-to-head records** - Track matchup history
- **Coaching AI difficulty levels** - Easy/Medium/Hard CPU opponents

### Lower Priority
- **Advanced play-calling** - Pick & roll, isolation, zone defense
- **Injury system** - Optional injury simulation
- **Trade/roster management** - Build custom rosters
- **AI game analysis** - LLM-powered game recaps
- **Multiplayer** - Local hot-seat or online matchups

## Potential Monetization Strategies

**Note:** These are future considerations, not current implementation plans.

### 1. Freemium Model
**Free tier:**
- Simulate games with all teams
- Basic stats display
- Play-by-play action

**Premium tier ($4.99 one-time or $0.99/month):**
- Playoff bracket simulation
- Save/replay games
- Create custom teams & players
- Advanced analytics dashboard
- Interactive mode (User vs CPU)
- AI-generated post-game analysis

### 2. Retro Gaming Nostalgia Bundle
- One-time purchase: **$2.99**
- Market to: 90s NBA fans, retro gaming community, basketball stats enthusiasts, streamers
- "Relive the greatest NBA matchups in history"
- Premium retro experience with modern features

### 3. Web App + Ad Revenue
- Completely free to play
- Hosted web version (no installation)
- Google Ads between quarters/games
- Low barrier to entry, viral potential

### Cost Analysis
**Compute cost per game: ~$0.0000002** (essentially free)
**Hosting:** Thousands of concurrent games on $5-10/month server
**Value proposition:** Nostalgia + accuracy + fun, not compute resources

## Credits

Developed with passion for basketball history and simulation accuracy. All player statistics sourced from Basketball Reference.

Enjoy the greatest matchups that never happened!
