# Classic NBA Text Basketball Simulator - Project Context

**Version:** 2.4.0 Free Edition
**Status:** LAUNCHED on itch.io
**Platforms:** macOS (live), Windows (uploading today)
**Last Updated:** 2025-01-29

---

## 🎯 Project Overview

A nostalgic text-based basketball simulation featuring cross-era matchups between 24 championship teams from 1965-2024. Built in Python with Rich library for terminal UI.

**Inspiration:** Loved text basketball sims from the 80s, wanted to settle cross-era debates (e.g., '96 Bulls vs '17 Warriors).

**Repository:** [Your GitHub URL - add when available]
**itch.io:** [Your itch.io URL]

---

## 📊 Current Status

### ✅ **Completed**
- Free Edition launched on itch.io (macOS live)
- Windows build completed at library (uploading today)
- First download achieved
- **First donation: $10** (after only 5 downloads!)
- 61 views, 5 downloads so far
- Trademark-safe team names for commercial distribution
- Cross-platform compatibility (Windows/macOS/Linux)

### 🚧 **In Progress**
- Uploading Windows version to itch.io
- Planning technical devlog about simulation engine

### 📝 **Pending Enhancements**
1. Fix small-man lineups still appearing (saw in Detroit)
2. Add home court advantage (~2-3% shooting boost)
3. More teams (60s Celtics years, additional 80s/90s teams)
4. Playoff bracket mode
5. Additional play description variations

---

## 🏗️ Technical Architecture

### **Core Files**

**Full Version:**
- `basketball_sim_v2.py` - Main game (all features, original team names)
- `teams.csv` - Original team names (e.g., "1996 Bulls")
- `players.csv` - 360+ players with real Basketball Reference stats

**Free Edition (Commercial):**
- `basketball_sim_free.py` - Single game modes only, trademark-safe
- `teams_free.csv` - Trademark-safe names (e.g., "1996 Chicago (72-10 Team)")
- `players.csv` - Same player data

**Distribution:**
- `dist/Basketball-Sim-Free-macOS.zip` (11 MB)
- `dist/Basketball-Sim-Free-Windows.zip` (15-25 MB)

### **Key Dependencies**
- Python 3.8+
- Rich library (terminal UI)
- PyInstaller (EXE builds)
- Standard library: csv, random, time, platform

---

## 🔧 Critical Technical Fixes

### **1. Cross-Platform Compatibility**

**Problem:** `termios` module only works on Mac/Linux, not Windows.

**Solution (lines 9-21 in basketball_sim_free.py):**
```python
import platform

# Platform-specific imports for keyboard input
if platform.system() != 'Windows':
    import tty
    import termios
else:
    import msvcrt
```

**getch() function (lines 34-49):**
```python
def getch():
    """Get a single character from user input without requiring ENTER (cross-platform)"""
    if platform.system() == 'Windows':
        # Windows
        ch = msvcrt.getch()
        return ch.decode('utf-8') if isinstance(ch, bytes) else ch
    else:
        # Mac/Linux
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch
```

### **2. CSV Encoding for Windows**

**Problem:** Windows can't read CSV files with UTF-8 characters (player names with accents).

**Solution:** Add `encoding='utf-8'` to ALL file opens:
```python
with open('teams_free.csv', 'r', encoding='utf-8') as f:
with open('players.csv', 'r', encoding='utf-8') as f:
```

**Locations to check:**
- Line ~1561: teams_free.csv load
- Line ~1575: players.csv load
- Any other file operations

### **3. Halftime Stats Display**

**Fixed:** Changed from old "="*80 banner to clean "[bold]HALFTIME BOX SCORE[/bold]" format to match end-game display.

**Location:** `show_halftime_stats()` method (line ~2339)

---

## 🎮 Game Features

### **Free Edition Includes:**
✅ Single Game Mode (Computer vs Computer)
✅ User vs Computer (Interactive gameplay)
✅ All 23 championship teams (1965-2024)
✅ 360+ players with authentic stats
✅ Cross-era balance system
✅ Playmaker value system
✅ 5 speed settings (Cinema to Instant)
✅ Complete box scores and stats
✅ Halftime stats review
✅ Shot clock system
✅ Foul system with bonus/foul outs

### **Paid Version Will Add:**
- Season Mode (22-game seasons)
- Season standings
- Player season averages
- Interactive season games
- Planned price: $4.99-7.99

---

## 🏀 Simulation Engine Details

### **Cross-Era Balance System**

**Era-Based Defense Adjustments:**
- Pre-3PT Era (1965-1979): +0.08 penalty (primitive schemes)
- Early 3PT Era (1980-1999): -0.05 bonus (hand-checking, sophisticated schemes)
- Slow Pace Era (2000-2016): +0.00 baseline
- Modern Era (2017-2024): +0.05 penalty (offensive-friendly rules)

**Shooting Penalties:**
- 0.5% per decade difference, max 3.5%
- Example: '72 Lakers vs '24 Celtics = ~2.5% FG% penalty for Lakers

**Shot Distribution:**
- Players with 0% 3PT never attempt threes
- Ensures old-school big men perform at true efficiency

### **Playmaker Value System**

**Formula:** +0.3% shooting boost per APG, capped at 3.5%

**Examples:**
- Magic Johnson (11.2 APG) → +3.5% boost to teammates
- John Stockton (10.5 APG) → +3.2% boost
- Jason Kidd (9.2 APG) → +2.8% boost
- Tony Parker (5.7 APG) → +1.7% boost

### **Rotation Management**

**Starting Lineup:** Based on MPG (minutes per game), not PPG
- Ensures rotation players start (e.g., Boris Diaw, Jason Kidd)

**Restricted Rotations (Top 10):**
- Comeback mode (down 8+ after halftime)
- Close games (Q4, within 6 points)
- Crunch time (Q4 last 8 minutes)

**Minute Variance by Tier:**
- Superstars (35+ MPG): ±1.5 min
- Starters/Elite 6th Men (20-34 MPG): ±2.5 min
- Role Players (12-19 MPG): ±4.0 min
- Deep Bench (<12 MPG): ±5.0 min

### **Major Bug Fixes**

**Putback Possession Bug (v2.3):**
- Fixed: Possession now switches after putback scores
- Previously possession stayed with same team

**Instant Sim Engine Overhaul (v2.3):**
- Replaced mathematical instant sim with silent live sim
- Fixed modern team dominance (Celtics went from 21-1, 135.8 PPG to 15-7, 107.3 PPG)
- Any championship team can now win different seasons

**Play Descriptions (v2.3):**
- Added 20+ varied shot descriptions
- Removed verbose pass chains
- Format: "Passer → Shooter [description]!" or just "Shooter [description]!"
- Examples: "Nowitzki → Kidd slams it home!", "Curry drains a deep three!"

---

## 🛠️ Build Process

### **macOS Build**
```bash
cd /Users/raymundozialcita/Documents/CODEDAMMIT/CBA
pyinstaller --onefile --name "Basketball-Sim-Free" basketball_sim_free.py
cp teams_free.csv dist/
cp players.csv dist/
cd dist
zip -r Basketball-Sim-Free-macOS.zip Basketball-Sim-Free teams_free.csv players.csv README.txt
```

### **Windows Build (On Windows PC)**

**Prerequisites:**
- Python 3.8+ installed
- "Add Python to PATH" checked during install

**Commands:**
```cmd
cd Desktop\basketball-build
python -m pip install --user rich
python -m pip install --user pyinstaller
python -m PyInstaller --onefile --name "Basketball-Sim-Free" basketball_sim_free.py
copy teams_free.csv dist\
copy players.csv dist\
cd dist
```

**Create ZIP:**
- Select all 3 files (EXE + 2 CSVs)
- Right-click → Send to → Compressed folder
- Rename to: Basketball-Sim-Free-Windows.zip

**Common Issues:**
- "No module named 'rich'" → `python -m pip install --user rich`
- UnicodeDecodeError → Add `encoding='utf-8'` to CSV file opens
- Permission denied → Run Command Prompt as Administrator
- "ModuleNotFoundError: termios" → Ensure platform detection code is present

### **Updating Versions**

**To release update:**
1. Update VERSION in code
2. Build new EXE
3. itch.io: Edit game → Uploads → Edit file → Replace file
4. Post devlog about update

---

## 📁 File Structure

```
CBA/
├── basketball_sim_v2.py          # Full version (personal use)
├── basketball_sim_free.py        # Free Edition (commercial)
├── teams.csv                     # Original team names
├── teams_free.csv                # Trademark-safe names
├── players.csv                   # Player data (360+ players)
├── CHANGELOG.md                  # Version history
├── README.md                     # Project documentation
├── DISTRIBUTION_GUIDE.md         # Launch strategy
├── ITCH_PAGE_DESCRIPTION.txt     # itch.io page content
├── ITCH_INSTALL_INSTRUCTIONS.txt # User install guide
├── build_windows_exe.bat         # Windows build script
├── dist/                         # Distribution builds
│   ├── Basketball-Sim-Free       # macOS executable
│   ├── Basketball-Sim-Free.exe   # Windows executable
│   ├── Basketball-Sim-Free-macOS.zip
│   └── Basketball-Sim-Free-Windows.zip
└── PROJECT_CONTEXT.md            # This file
```

---

## 🎯 Pending Enhancements

### **High Priority**
1. **Fix small-man lineups** (Issue observed with Detroit)
   - Sometimes lineup logic selects smaller players
   - Need to review starting lineup selection in `select_starting_five()`

2. **Home court advantage**
   - Add ~2-3% shooting boost for home team
   - Needs home/away designation in game setup

3. **Improve play-by-play readability**
   - Current issue: Lines too long/dense (e.g., "LeBron James shoots... → Kyrie Irving → LeBron James... Can't connect! → Rebound: Michael Jordan")
   - Hard to read even at Cinema mode (3.5s)
   - Solutions:
     - Increase Cinema mode to 5-6 seconds
     - Add character limit (60 chars) and break into multiple lines
     - Simplify complex sequences (hide pass-backs)
     - Add "Ultra Cinema" mode (6s) for narrative experience

### **Medium Priority**
3. **More teams**
   - Additional 60s Celtics championship years
   - More 80s/90s teams
   - Requests from users

4. **Playoff bracket mode**
   - 8-team tournament
   - Single elimination or best-of-7
   - User controls their team

5. **Advanced stats**
   - PER, TS%, +/-, Win Shares
   - Shooting charts
   - Advanced box scores

### **Low Priority**
6. **Timeout system**
   - Strategic timeout calls
   - Play diagrams

7. **Defensive play calling**
   - User controls defensive strategy
   - Man-to-man, zone, press options

8. **Injury system** (optional)
   - Random injuries
   - Player fatigue

---

## 📈 Version History

### **v2.4.0 (2025-01-29)**
- **24 teams:** Added 2008 Celtics (KG/Pierce/Allen Big 3)
- **Shot selection overhaul:** Changed from PPG² to usage_rate weighting
  - Ensures focal points like Duncan/Dirk get appropriate touches
  - More accurate to real NBA shot distribution
- **Scheduling fix:** Proper round-robin circle method for 24 teams
  - Each team plays exactly once per round (12 games/round)
  - No more same team appearing multiple times in consecutive games
- **Superstar rotation logic:** Players with usage_rate > 25 stay on court in close games
  - Close game (≤9 pts): Superstars don't get subbed out
  - Blowout (20+ pts): Superstars can rest
  - Foul trouble (4+ fouls before Q4): Superstars sit
- **Position fixes for realistic rotations:**
  - 2014 Spurs: Belinelli→SG, Manu→SF (fixes Manu getting benched)
  - 2017 Warriors: KD→SF, Draymond→C, Iguodala→PF, West→PF

### **v2.3.0 (2025-01-25)**
- Instant sim engine overhaul (silent live sim)
- Playmaker value system
- Starting lineup changed to MPG-based
- Rotation improvements (top 8 → top 10)
- Putback possession bug fix
- Play description variations

### **v2.2.0**
- Interactive Mode (User vs Computer)
- Shot clock system
- Complete foul system
- UX polish

### **v2.1.0**
- Cross-era balance system
- Fixed non-3PT shooters taking 3s
- Point differential tiebreaker
- Improved rotations

### **v2.0.0**
- Initial release
- 23 championship teams
- Basic simulation engine

---

## 💡 Known Issues

1. **Small-man lineups occasionally appear** (Detroit noted)
   - Lineup logic needs review
   - Not game-breaking but not realistic

2. **Windows build requires specific encoding**
   - Must include `encoding='utf-8'` for CSV reads
   - Build script should verify this

3. **Description formatting on itch.io**
   - Double-spacing between all lines
   - May need manual editing in itch.io editor

4. **Play-by-play lines can be too long**
   - Example: "LeBron James shoots... → Kyrie Irving → LeBron James... Can't connect! → Rebound: Michael Jordan"
   - Hard to parse even at slowest speed (3.5s Cinema mode)
   - Need character limits or line breaking for complex sequences

5. **Teams to observe for rotation/lineup issues** (from 10-sim analysis)
   - Watch for "unnatural" behavior like star benching, position crowding
   - [ ] 2017 Warriors (avg 12.5) - KD/Curry rotation okay?
   - [ ] 2016 Cavaliers (avg 19.0) - LeBron/Kyrie getting touches?
   - [ ] 2011 Mavericks (avg 18.9) - Dirk usage working?
   - [ ] 2000 Lakers (avg 14.2) - Shaq/Kobe balance?
   - [ ] 1971 Bucks (avg 19.2) - Kareem/Oscar rotation?
   - [ ] 1965 Celtics (avg 23.7) - Russell era penalties fair?

---

## 🚀 Launch & Marketing

### **Distribution Strategy**
- **Free Edition:** itch.io (single game modes)
- **Paid Version:** itch.io ($4.99-7.99, adds Season Mode)
- **Revenue so far:** $10 donation (after 5 downloads!)

### **Target Audience**
- Basketball fans (r/NBA, r/VintageNBA, r/nbadiscussion)
- Retro gaming enthusiasts
- Text-based sim fans
- Cross-era debate enthusiasts

### **Marketing Channels**
- itch.io organic discovery
- Reddit (basketball communities)
- Twitter/X (#NBATwitter, #RetroGaming)
- Basketball forums (RealGM, Basketball-Reference)

### **Performance Metrics**
- Views: 61
- Downloads: 5
- Conversion rate: 8.2% (very good!)
- Donation rate: 20% (1 of 5, INSANE!)
- Average donation: $10 (top tier!)

---

## 🎨 itch.io Page Details

### **Cover Image**
- Created in Canva (630x500px)
- Gameplay screenshot with text overlay
- Courier New font (retro terminal aesthetic)
- "CLASSIC NBA SIMULATOR" + "23 TEAMS • 1965-2024"

### **AI Disclosure**
- Marked as "AI-assisted"
- Transparent about code/text assistance
- Human-directed design and concept

### **Pricing**
- Free (Pay What You Want)
- Minimum: $0
- Collected by itch.io (easier for free edition)

---

## 🧠 Simulation Logic Deep Dive (Blog Material)

### **Shot Selection: Who Takes the Shot?**

**The Problem:** In early versions, shot selection used `(PPG + 1)²` weighting. This meant high scorers dominated, but "quiet superstars" like Tim Duncan and Dirk Nowitzki didn't get enough touches because their PPG was lower than flashier players.

**The Solution:** Switch to `usage_rate` weighting.
- Usage rate = % of team possessions a player uses (shots, FTs, turnovers)
- Measures shot *attempts*, not just makes
- Duncan (23.0 usage) now gets appropriate touches even if his PPG is lower than a teammate

```python
def select_shooter(self) -> Player:
    weights = [p.usage_rate for p in on_court]
    return random.choices(on_court, weights=weights)[0]
```

---

### **Rotation Logic: When Do Stars Sit?**

**The Problem:** Original logic treated all players equally - sub out anyone ahead of their minute pace. This led to superstars getting benched in close games.

**The Solution:** Superstar protection based on game state.

**Superstar Definition:** `usage_rate > 25`

| Game State | Superstar Behavior |
|------------|-------------------|
| Close game (≤9 pts) | Stay on court, no minute ceiling |
| Blowout (20+ pts) | Can rest |
| Foul trouble (4+ fouls before Q4) | Must sit |
| Normal game | Extra buffer before subbing |

**Why this works:** Real NBA coaches don't care about season averages in close games. LeBron plays 45 minutes if the game is tight. He rests when they're up 25.

---

### **Position Flexibility: The Hidden Complexity**

**The Problem:** Basketball Reference assigns one position per player, but NBA players are versatile. This causes:
- Position crowding (two SFs, no SG in starting 5)
- Key players getting benched (Manu with only 2 minutes!)
- Unrealistic lineups

**The Solution:** Adjust position designations to match how teams actually played.

**Case Study - 2014 Spurs:**
- Original: Manu (SG) competing with Danny Green (SG) and Belinelli (SF)
- Problem: Top 5 by MPG had no SG starter, Manu rarely subbed in
- Fix: Belinelli→SG (starts), Manu→SF (backs up Kawhi)
- Result: Manu gets proper 20+ minutes backing up two SF positions

**Case Study - 2017 Warriors:**
- Original: Durant (PF), Draymond (PF) - two PFs, no center
- Problem: No natural starting 5, Draymond outscoring Klay somehow
- Fix: KD→SF, Draymond→C, Iguodala→PF, West→PF
- Result: "Death Lineup" with Draymond at small-ball 5, all positions covered

**Key Insight:** Position designations are fluid - easier to adjust than changing real stats.

---

### **Starting Lineup: MPG vs Reality**

**Current Logic:** Top 5 players by minutes per game start.

**Why MPG?** Generally correlates with importance. Starters usually play more than bench players.

**The Edge Case:** High-minute bench players (6th men) can have more MPG than starters.
- Example: Manu Ginóbili (22.8 MPG bench) vs Danny Green (24.3 MPG starter)
- Green started all 82 games but played fewer minutes

**Possible Future Fix:** Add `is_starter` or `games_started` field to player data.

**Current Workaround:** Adjust positions so the "right" players end up in top 5 by MPG.

---

### **Scheduling: The Circle Method**

**The Problem:** With 23 teams (odd), simple shuffle caused same team appearing multiple times in consecutive games (e.g., 1965 Celtics playing 3 times in 8 games).

**The Solution:** Add 24th team (2008 Celtics) and use proper round-robin circle method.

**Algorithm (for even N teams):**
1. Fix one team in place
2. Arrange remaining N-1 teams in a circle
3. Each round: pair teams across from each other
4. Rotate the circle, repeat
5. After N-1 rounds, everyone has played everyone

**Result:**
- 23 rounds × 12 games per round = 276 total games
- Each team plays exactly once per round
- No duplicate appearances

---

### **Cross-Era Balance Philosophy**

**The Challenge:** How do you make 1965 Celtics competitive against 2024 Celtics?

**Our Approach:**
1. **Era-based defense adjustments** - Older defensive schemes penalized slightly
2. **Shooting penalties by decade** - 0.5% per decade gap, max 3.5%
3. **Shot distribution** - Players with 0% 3PT never attempt threes
4. **Playmaker boost** - +0.3% shooting per APG (rewards ball movement)

**Philosophy:** Balance > perfect historical accuracy. Any championship team should be able to win a season, but modern teams have natural advantages (athleticism, spacing, rules).

---

### **Testing Methodology**

**10-Sim Analysis:** Run 10 full seasons, track average finishing position.

**What We Look For:**
- Modern teams shouldn't dominate completely (2024 Celtics at 1.9 avg is fine)
- Historical teams should be competitive (1996 Bulls at 4.8 avg is good)
- No team should be unbeatable or hopeless
- Watch for "unnatural" behavior (star benching, weird shot distribution)

**Teams Flagged for Observation:**
- 2017 Warriors (avg 12.5) - Draymond outscoring Klay?
- 2016 Cavaliers (avg 19.0) - LeBron's team near bottom?
- 2011 Mavericks (avg 18.9) - Dirk getting touches?
- 1971 Bucks (avg 19.2) - Kareem/Oscar effective?
- 1965 Celtics (avg 23.7) - Era penalty too harsh?

---

## 📝 Future Devlog Topics

1. **How the simulation engine works**
   - Cross-era balance mechanics
   - Playmaker boost system
   - Rotation logic (comeback mode, crunch time)
   - Why instant sim was rebuilt

2. **Balancing eras: the hardest problem**
   - Athletic evolution vs nostalgia
   - Rule changes impact
   - Testing methodology

3. **Adding new teams**
   - Data collection process
   - Usage rate adjustments
   - Balance testing

4. **From idea to launch**
   - 80s nostalgia inspiration
   - Technical challenges
   - What I learned

---

## 🔗 Important Links

- **itch.io:** [Add URL]
- **GitHub:** [Add URL when public]
- **Discord/Community:** [If created]
- **Twitter/X:** [If promoting there]

---

## 💭 Developer Notes

### **What Works Well**
- Cross-era balance is pretty good (90s teams competitive)
- Playmaker system adds strategic depth
- Comeback mode rotation feels realistic
- Play descriptions add variety without being verbose
- Trademark-safe names are clear and descriptive

### **What Needs Improvement**
- Lineup selection edge cases
- Home court advantage missing
- More play description variations
- Pace impact on extreme teams (1972 Lakers, 1965 Celtics)
- Foul rate calibration across eras

### **Philosophy**
- "Simulation engine is a work in progress (probably always will be lol)"
- Balance > perfect realism
- Iterate based on user feedback
- Ship fast, improve based on data
- Transparency > marketing polish

---

## 🤝 Contributing / Feedback

**Users can:**
- Leave comments on itch.io
- Report bugs via itch.io comments
- Request features in devlog posts
- Suggest team additions
- Test cross-era balance

**Developer priorities:**
1. Fix game-breaking bugs ASAP
2. Balance adjustments based on testing
3. User-requested features (if aligned with vision)
4. New content (teams, modes)

---

## 📚 References

- **Player Stats:** Basketball Reference (https://basketball-reference.com)
- **Historical Data:** Official NBA statistics
- **Balance Methodology:** Iterative testing with diverse matchups

---

**Last Updated:** 2025-01-22
**Next Milestone:** Windows version live on itch.io, technical devlog published

---

## 🎯 How to Use This Document

**For new AI conversations:**
```
"I'm working on Classic NBA Text Basketball Simulator.
Here's the project context: [paste relevant sections]
Current issue: [your question]"
```

**For updates:**
- Keep this file current as features are added
- Note version changes
- Document new bugs/fixes
- Update metrics (downloads, revenue)

**For onboarding:**
- Share with collaborators
- Reference for technical decisions
- Preserve institutional knowledge
