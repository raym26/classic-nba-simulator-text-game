# Changelog

All notable changes to Classic NBA Text Basketball Simulator will be documented in this file.

## [2.3.0] - 2025-01-25

### 🎯 Major Features

#### Instant Sim Engine Overhaul
- **Replaced mathematical instant sim with silent live sim engine**
  - Uses same possession-by-possession logic as live sim, just without UI
  - Fixed modern team dominance (Celtics went from 21-1, 135.8 PPG to 15-7, 107.3 PPG)
  - Any championship team can now win different seasons
  - 90s teams competitive (1993 Bulls won championship in test season)
  - Unpredictable season outcomes restored

#### Playmaker Value System
- **High-assist players now boost teammate shooting percentage**
  - Formula: +0.3% shooting boost per APG, capped at 3.5%
  - Magic Johnson (11.2 APG) → +3.5% boost to teammates
  - John Stockton (10.5 APG) → +3.2% boost
  - Jason Kidd (9.2 APG) → +2.8% boost
  - Tony Parker (5.7 APG) → +1.7% boost
  - Makes team construction strategic (scorers vs playmakers)
  - Adds 1-2 PPG to team scoring with elite playmaker on court

#### Starting Lineup Selection Change
- **Changed from PPG to MPG (minutes per game) for starting 5**
  - Ensures rotation players actually start games
  - Fixed DNP issues for high-minute, low-scoring players (Boris Diaw, Jason Kidd)
  - More realistic: starters = who plays most, not who scores most
  - Spurs example: Diaw (25.0 MPG, 9.1 PPG) now starts instead of being benched

### ⚖️ Balance Improvements

#### Rotation Restrictions Loosened
- **Increased restricted rotations from top 8 to top 10**
  - Comeback mode (down 8+): top 8 → top 10
  - Close games (Q4, within 6 points): top 9 → top 10
  - Crunch time (Q4 last 8 minutes): top 8 → top 10
  - Ensures 7th-10th men get proper playing time
  - Fixed Boris Diaw DNP issue (was playing only 3-6 games, now plays all 22)

### 🐛 Bug Fixes

#### Putback Possession Bug
- **Fixed possession not switching after putback scores**
  - After a putback score, possession now correctly switches to other team
  - Previously, possession stayed with same team due to "Offensive rebound" check
  - Now checks if scored BEFORE checking for offensive rebound

### 📊 Impact

**Season Sim Results (Before vs After):**

Version 2.2 (Old Instant Sim):
```
1. 2024 Celtics    21-1  135.8 PPG  (Unbeatable)
2. 2024 Thunder    17-5  111.0 PPG
13. 1996 Bulls     11-11  82.6 PPG  (Embarrassing)
20. 1993 Bulls      7-15  82.6 PPG  (Terrible)
```

Version 2.3 (New Silent Live Sim) - Season 1:
```
1. 2024 Thunder    17-5  111.0 PPG
2. 2023 Nuggets    17-5  109.0 PPG
4. 2024 Celtics    15-7  107.3 PPG  (Competitive, not dominant)
13. 1996 Bulls     11-11  82.6 PPG  (Respectable)
```

Version 2.3 - Season 2:
```
1. 1993 Bulls      17-5   83.9 PPG  (Champions!)
4. 1996 Bulls      14-8   87.7 PPG
8. 2024 Celtics    13-9  105.6 PPG
```

**Key Improvement:** Different teams win different seasons, era balance restored ✅

---

## [2.2.0] - 2024-12-XX

### 🎮 Major Features

#### Interactive Mode (User vs Computer)
- Full gameplay with manual control
- Choose your team and opponent
- Select starting lineup
- Make play-by-play decisions (pass, shoot 2PT/3PT)
- Substitutions between quarters
- Halftime stats review
- Complete box scores

#### Game Systems
- **Shot Clock System** - 24-second enforcement with 14-second reset on offensive rebounds
- **Complete Foul System** - Free throws, bonus, foul outs, crunch time logic
- **UX Polish** - Single keypress input, clean screen transitions
- **Play-by-Play Display** - Reduced to 3 most recent plays for clarity

---

## [2.1.0] - 2024-12-XX

### 🐛 Bug Fixes
- Fixed critical bug where non-3PT shooters were taking 3-pointers

### ⚖️ Balance Improvements
- Implemented cross-era balance system (shooting + defense adjustments)
- Added point differential tiebreaker to standings
- Improved rotation consistency for elite 6th men

### 🎨 UI Improvements
- Play-by-play now displays under score line
- Cinema mode speed increased to 3.5s for better readability
- Starting lineups now based on PPG instead of CSV order

---

## [2.0.0] - Initial Release
- Basic simulation engine
- 23 championship teams from 1965-2024
- Season mode with standings
- Live game simulation
- Cross-era matchups
