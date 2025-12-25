# Universal Star Protection System

## Applied To ALL Simulation Modes

### 1. Live Simulation (Play-by-Play)
**Location:** `Team.time_based_substitutions()` (line 401-417)
**Method:** +2.0 minute buffer before substitution
- Normal player: Subbed at 0.5 min ahead of pace
- Star player: Subbed at 2.5+ min ahead of pace

### 2. Instant Simulation (Season Mode)
**Location:** `instant_sim_game()` (line 2541-2554)
**Method:** Tighter variance clamp
- Normal player: 85%-115% of base minutes
- Star player: 90%-110% of base minutes (tighter!)

### 3. Live Game Setup
**Location:** `Team.reset_for_new_game()` (line 168-186)
**Method:** Tighter variance clamp (same as instant sim)
- Ensures stars get consistent target minutes from the start

---

## Star Definition (Universal)
**Top 3 scorers by PPG on each team**
```python
top_3_ppg_threshold = sorted([p.ppg for p in team.players], reverse=True)[2]
is_star = player.ppg >= top_3_ppg_threshold
```

---

## Examples Across All Teams

**Duncan (29.2 MPG base):**
- Before: 21.7 - 36.7 minutes possible
- After (star): 26.3 - 32.1 minutes (90%-110%)
- After (role): 24.8 - 33.6 minutes (85%-115%)

**Jordan (37.7 MPG base):**
- Before: 32.0 - 43.4 minutes possible
- After (star): 33.9 - 41.5 minutes (90%-110%)

**Bench player (15 MPG base):**
- Before: 12.8 - 17.3 minutes
- After (role): 12.8 - 17.3 minutes (same - they need variance)

---

## Why Different Approaches?

**Live Sim:** Uses substitution buffer (can't retroactively change minutes)
**Instant Sim:** Uses variance clamp (determines minutes upfront)

Both achieve same goal: **Stars play more consistently**

---

## Benefits

✅ Universal - all 23 teams, all modes
✅ Dynamic - adapts to each team's roster
✅ Balanced - role players still get variance for realism
✅ Consistent - Duncan won't have 21-minute games anymore
