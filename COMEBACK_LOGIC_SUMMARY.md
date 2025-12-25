# Comeback Urgency Substitution Logic

## What Changed
Added **score-aware rotation management** to `time_based_substitutions()` (lines 350-392)

## How It Works

### Normal Game (Within 6 points or before halftime)
- Standard rotation based on `game_target_minutes`
- All players get their expected minutes
- 11-man rotation as designed

### Comeback Mode (Down 8+ after halftime)
- **Automatically shortens rotation to top 10 players**
- Ignores deep bench (11th-12th men)
- Stars get extra minutes even if ahead of pace
- Triggered when: `score_diff <= -8 AND game_progress >= 50%`

### Close Game (Within 6 points in 4th quarter)
- Tightens rotation to top 10 players
- Keeps stars fresh for final minutes
- Triggered when: `abs(score_diff) <= 6 AND game_progress >= 75%`

### Blowout (Down 20+ with <5 min left)
- **Reverts to normal rotation** (rest starters)
- Game is over, no point burning star minutes
- Triggered when: `score_diff <= -20 AND time_remaining < 5`

## Real Basketball Examples

**Scenario 1: Down 10 in Q3**
- Before: Duncan rests at 6:00 mark (ahead of minute target)
- After: Duncan STAYS IN (comeback mode activated)

**Scenario 2: Close game, 5 min left**
- Before: 11-man rotation, deep bench still playing
- After: Only top 10 players, shortened rotation

**Scenario 3: Down 25 with 3 min left**
- Before: Stars still playing
- After: Bench plays it out, rest starters for next game

## Code Location
- **Function:** `Team.time_based_substitutions()` (basketball_sim_v2.py:350-392)
- **Called from:** `GameSimulation.simulate_quarter()` at 6:00 and 3:00 marks

## Expected Impact
- **More realistic coaching** - matches NBA strategy
- **Stars get more minutes when needed** - addresses user's observation
- **Better late-game management** - appropriate rotation tightening
- **No more "watching the lead slip away with bench in"**
