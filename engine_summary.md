# Explore core simulation layer

Perfect! Now I have read all the core files. Let me compile my detailed findings:

## COMPREHENSIVE CORE SIMULATION ENGINE ANALYSIS

### EXECUTIVE SUMMARY

The Pharaoh Engine is a **moderately deep football manager simulation** with sophisticated minute-by-minute match simulation, async transfer negotiations, and layered management systems. However, it exhibits a **mixed implementation maturity**: some modules are production-ready while others are explicitly marked as "stubs" or "Phase 2" placeholders. Below are detailed findings for each module.

---

## FILE-BY-FILE DETAILED FINDINGS

### 1. **match_engine.py** (32.4 KB) — FULLY IMPLEMENTED, SOPHISTICATED

**Status**: 🟢 Production-ready, genuine depth

**What's Implemented:**
- **Minute-by-minute simulation** (lines 161-376): Every minute from 0-90+ is iterated with dynamic probabilities
- **Fatigue mechanics** (lines 174-178): Teams tire progressively after minute 60; stamina affects the penalty curve (teams with stamina 10 lose up to 25%, stamina 20 lose up to 15%)
- **Red card system with live impact** (lines 350-375): Sends players off instantly, reducing team to 10 men, affecting all calculations for remaining minutes
- **Home advantage with fan scaling** (lines 59-73): Base 1.05x bonus, scaled by fan happiness (70+ happiness adds +0.03 more, <20 happiness nullifies it)
- **Possession calculation** (lines 133-138): Based on midfield strength with Gaussian clamping (5.0 std deviation)
- **Tactical impact on chance creation** (lines 192-195): Tempo affects action_chance (base 0.08 + tempo * 0.008)
- **Position suitability penalties** (lines 518-530): Out-of-position players get heavy finishing penalties; a CB as ST loses 60-80% effectiveness
- **Training focus micro-bonuses** (lines 81-106): Each player with training focus adds small bonuses to attack/defense
- **Ramadan stamina penalty** (lines 152-158): 10% stamina reduction during Ramadan period
- **Realistic penalty conversion** (lines 288-312): 75-90% conversion based on composure + finishing
- **Varied card probabilities** (lines 330-375): 15% yellow per foul, 1% red; pressing intensity affects foul rate
- **Injury system** (lines 377-408): ~1.5% total chance per match, 7-42 day recovery
- **Individual player ratings** (lines 702-756): Base rating from match result + adjustments for goals, assists, yellows, position suitability, clean sheets

**Sophistication Level: HIGH**
- Penalties are a real mechanism with ~3% chance per foul
- Fatigue is genuinely time-dependent with formula: `max(0.75, 1.0 - (mins_tired / 30.0) * (1.0 - avg_stamina / 25.0) * 0.15)`
- Red cards permanently alter match dynamics
- Position mismatch has massive impact (20-80% penalty)

**Issues/Limitations:**
- **Hardcoded values**: HOME_ADVANTAGE_BONUS is a constant; could be dynamic
- **No set pieces simulation**: Corners don't generate extra danger (just low % chance of shots from them)
- **No substitutions during simulation**: bench players never enter during the match
- **No extra-time/penalties**: Draws are final (no mechanism for cup tie resolution in matches, only at DB level in competition.py)
- **Assist chance is fixed at 60%** (line 634): could vary by play pattern
- **Action chance is simple linear** (line 195): doesn't account for match state (winning teams might play more defensively)

**Realistic?**: **Yes, moderately.** The minute-by-minute loop is realistic. The fatigue, home advantage, and positional penalties create real tactical depth. However, the system lacks set-piece realism and substitution mechanics.

---

### 2. **transfers.py** (33.2 KB) — FULLY IMPLEMENTED, MODERATELY SMART AI

**Status**: 🟢 Production-ready

**What's Implemented:**
- **Two-phase negotiation** (lines 289-316): Fee phase → Wage phase, with async responses next day
- **Counter-offer logic** (lines 304-316): Clubs accept at 90% of asking price; otherwise counter down by 5-7% per attempt
- **Fee convergence** (lines 308): Attempt 1 = asking * 0.95, Attempt 2 = asking * 0.88, Attempt 3 = asking * 0.82
- **Wage acceptance** (lines 585-637): Player accepts if offer >= 85% of current wage, otherwise counters at 95% of current
- **Player valuation** (lines 240-274): Base = current_ability * 50k; multiplied by age modifier (1.5x for ≤21, 0.3x for 38+), PA modifier (1.0 + (PA-CA)/200), contract modifier (0.3-1.0x based on days left)
- **Max attempts enforcement** (lines 231-232): 3 fee attempts, then deal collapses
- **Loan system** (lines 104-209): Full loan mechanics with wage split and buy option
- **Loan return processing** (lines 157-188): Auto-returns expired loans
- **AI bids on listed players** (lines 642-686): ~10% daily chance; AI picks eligible clubs with 70% of valuation offer
- **Contract renewal system** (lines 725-834): Acceptance based on wage delta, morale, age, playing time, club reputation
- **Expiring contract warnings** (lines 689-720): Monthly check for contracts expiring within 90 days

**AI Sophistication: MODERATE**
- **Smart**: Valuation formula accounts for age, potential, contract duration
- **Smart**: Counter-offers converge toward acceptance threshold, not random
- **Smart**: AI bids only from clubs with budget
- **Naive**: Counter-offer formula is deterministic (no randomness, no "tough negotiator" personalities)
- **Naive**: No player agent playing "both sides" or leveraging offers
- **Naive**: No wage inflation over time (wage_weekly stays same on renewal offer)

**Issues/Limitations:**
- **No marketplace discovery**: Player must be listed or offered explicitly; no scouting recommendations
- **No negotiation deadlines**: Can negotiate indefinitely (3 attempts, but no window close logic)
- **Transfer window ignored outside fee phase**: Wage phase can complete outside windows
- **AI doesn't simulate buying**: line 333-370 in season.py shows AI can trade, but only once per offseason in a random loop
- **No player preferences**: All players respond identically to wages; no "wants to join big club" logic
- **Wage renewal doesn't use playmaking bonus** (line 825): Just "wants higher wages" or "wants new challenge" — no nuance
- **Loan deals are 6 months fixed** (line 106): No flexibility

**Realistic?**: **Yes, moderately.** Async negotiations with counter-offers feel authentic. The fee convergence is sensible. However, player personality and leverage are missing.

---

### 3. **calendar.py** (43.1 KB) — FULLY IMPLEMENTED, COMPREHENSIVE

**Status**: 🟢 Production-ready

**What's Implemented:**
- **Daily progression** (lines 38-164): Advance day, trigger match days, process negotiations, handle injuries, etc.
- **Matchday simulation** (lines 191-217): Simulates all non-user fixtures on matchday
- **User match control** (lines 243-532): Player can set custom XI; system validates availability, fills gaps
- **Live match finalization** (lines 535-744): Applies substitution corrections from live play, persists stats
- **Player stat updates** (lines 747-882): Goals, assists, yellows, red cards, injuries, suspensions tracked per event
- **Daily recovery** (lines 884-915): ALL players (all clubs) recover fitness and heal injuries daily
- **Weekly development** (lines 918-962): Calls training system for all players, sends consolidated message
- **Monthly finances** (lines 965-981): Process income/expenses
- **Automatic board briefings** (lines 984-1029): Weekly summary of objectives progress
- **Ramadan notices** (lines 86-96): Special message when Ramadan period begins
- **Season completion detection** (lines 142-152): Detects when league is done, sends championship message
- **Cup integration** (lines 62-84): Checks for cup matches, advances cup rounds

**Flow Quality: EXCELLENT**
- Proper separation of concerns (match sim, player stat updates, board feedback)
- Correct order of operations (fixtures → AI transfers → board message)
- Non-user AI matches auto-simulate daily
- All injury/suspension logic in one place

**Issues/Limitations:**
- **Cup exception handling** (line 83): `pass` silently if cup not available—no notification to player
- **Ramadan check frequency** (line 88): Only checks every 30 days; could miss period start
- **Attendance calculation occurs at finalization, not scheduling**: Could be precalculated for better UX
- **No substitution mechanic during auto-simulated AI matches**: Only works for user matches
- **Weekly board brief references undefined `app_state`** (lines 134-139): Will crash if UI unavailable
- **Yellow card suspension at 5**: hardcoded line 873, should be configurable
- **Red card suspension is 1-3 matches** (line 880): Could be more severe for violent conduct

**Realistic?**: **Yes, very.** The calendar flow is logical and handles most manager sim requirements. The daily loop encompasses match sim, training, finances, board feedback.

---

### 4. **season.py** (18.2 KB) — FULLY IMPLEMENTED, THOROUGH

**Status**: 🟢 Production-ready

**What's Implemented:**
- **Awards calculation** (lines 16-89): Champion, top scorers, golden boot, golden glove (clean sheets), young player of the season (U21, ≥10 apps), most assists
- **Season archive** (lines 108-116): Saves historical stats to DB
- **Contract auto-renewal** (lines 148-173): Expired contracts extended 1 year at same wage
- **Player retirement** (lines 273-297): Age 38+ with 50% + (age-38)*15% chance to retire
- **AI inter-club transfers** (lines 300-389): Each AI club makes 0-3 offseason transfers based on squad size
- **Youth intake** (lines 392-425): Each club gets youth_rating//3 new young players (ages 16-18, PA varies)
- **Stats reset** (lines 191-199): All season stats and standings cleared
- **Fixtures generation** (lines 206-209): New league season created
- **Season expectation recalculation** (lines 237-240): Updates based on current reputation
- **Board objectives generation** (lines 242-257): Primary + secondary objectives set

**Sophistication: HIGH**
- Retirement logic scales with age (older = more likely)
- AI transfers check budget constraints
- Youth players inherit parent club reputation for rating generation
- Awards include young player filter (≥10 appearances) to prevent inflated ratings

**Issues/Limitations:**
- **AI transfers are random walk**: No negotiation, just instant transfer (line 333-370)
- **No player morale decay at end of season**: Everyone's morale stays same
- **No manager performance review**: Board doesn't evaluate manager in relation to objectives
- **Contract auto-renewal is forced**: Players can't leave on free transfers
- **Retirement only reduces squad**: No replacement logic (AI clubs may fall below 18 players)
- **Youth generation ignores position demand**: Random positions, not weighted by formation needs
- **No trophy bonus to reputation**: Winning the league doesn't boost rep for next season

**Realistic?**: **Mostly.** Season transitions are comprehensive. However, auto-contract renewals and forced AI transfers are unrealistic.

---

### 5. **board.py** (8.9 KB) — FULLY IMPLEMENTED, LAYERED

**Status**: 🟢 Production-ready

**What's Implemented:**
- **Confidence system** (lines 115-144): Win = +2, Draw = 0, Loss = -3; higher-expectation clubs lose more on losses
- **Objective generation** (lines 147-183): Primary (league position target) + 1 secondary (goals/youth/positive GD)
- **Objective evaluation** (lines 186-232): End-of-season check; penalties based on overshoot
- **Season expectation mapping** (line 205): `expectation_target_position()` converts expectation string to required finish
- **Mid-season progress tracking** (lines 29-112): Snapshot of each objective's status (achieved/on_track/at_risk/off_track)
- **Table slack in early season** (lines 40-41): Position targets allow ±1-4 position variance early in season

**Sophistication: GOOD**
- Confidence is volatile (±2-3 per match) and reflects league expectations
- Objectives scale with club reputation (big clubs get harder targets)
- Progress snapshots allow projected pace calculations

**Issues/Limitations:**
- **Only 2-3 objectives max**: No "consecutive wins" or "player development" sub-objectives
- **No "manager on the brink" dismissal threat**: Confidence can drop to 0 but no consequence
- **Secondary objectives are generic**: Always same 3 types (goals/youth/GD), no variety
- **Table slack formula is simple**: `max(1, int((1.0 - progress) * 4) + 1)` doesn't account for point deficit
- **No board spending pressure**: Budget isn't tied to expectations

**Realistic?**: **Yes.** Board pressure systems work well. Confidence swings are reasonable.

---

### 6. **finance.py** (1.9 KB) — STUB/MINIMAL IMPLEMENTATION

**Status**: 🟡 Placeholder only

**What's Implemented:**
- **Monthly income calculation** (lines 11-17): matchday_income * 2 + sponsorship/12 + tv_revenue/12
- **Monthly expenses** (lines 20-24): wage_bill_weekly * 4 + facilities_level * 50k
- **Net cash flow** (lines 27-29): Income - expenses
- **Budget checks** (lines 46-53): `can_afford_transfer()` and `can_afford_wage()`

**What's NOT Implemented:**
- ❌ No stadium expansion mechanics
- ❌ No sponsorship renegotiation
- ❌ No TV deal tiers
- ❌ No debt/loan system
- ❌ No transfer profit/loss tracking
- ❌ No balance sheet warnings
- ❌ No spending caps enforcement
- ❌ No facilities upgrade system (reads level but doesn't update)
- ❌ No competitive balance deductions for big spending

**Sophistication: VERY LOW**
- Assumes matchday income is exactly same every month (no variance)
- Facilities cost is flat 50k * level (no scaling)
- No youth academy operating costs

**Issues/Limitations:**
- **Line 14**: `f.matchday_income * 2` assumes exactly 2 home matches per month (incorrect—some months have 3)
- **Wage bill multiplication** (line 22): `wage_bill_weekly * 4` treats all months as exactly 4 weeks (should be 4.33 average)
- **No reserve fund logic**: Clubs can go deeply negative
- **Sponsorship is yearly static**: No renegotiation or tier changes

**Realistic?**: **No.** This is a stub. Real football finances include FFP rules, squad cost limits, asset depreciation, and complex revenue streams.

---

### 7. **training.py** (6.3 KB) — FULLY IMPLEMENTED, DETAILED

**Status**: 🟢 Production-ready

**What's Implemented:**
- **7 training intensity levels** (lines 14-27): Light (0.5x growth), Normal (1.0x), Intense (1.6x, -3 fitness), Double (2.2x, -5 fitness)
- **8 training programs** (lines 30-39): Shooting, Defending, Physical, Playmaking, Mental, Goalkeeping, Set Pieces, Balanced
- **Growth calculation** (lines 106-127): Base chance = max(0.02, min(0.40, CA_gap / 150.0)); multiplied by age_mult (1.8 for ≤20, 0.1 for >30), facility_mult (0.5 to 1.3), growth_mult (intensity-based)
- **Attribute improvement** (lines 110-120): 75% chance to improve focused attribute, 25% random
- **Age decline** (lines 130-139): Age 32+; decline_chance = 0.03 * (age - 31); physical attributes decline first
- **Ramadan penalty** (lines 54-61): 20% growth reduction during Ramadan
- **Injury risk from training** (lines 68-78): Risk scales with intensity (0.002 to 0.020); injury is 3-14 days

**Sophistication: GOOD**
- Growth formula respects potential cap
- Age curves are realistic (young peak, old decline)
- Training focus biases attribute selection
- Facilities scale training effectiveness (50% to 130% boost)

**Issues/Limitations:**
- **Hardcoded ATTR_MIN/MAX**: No dynamic scaling for legend players
- **Injury types are random** (line 69): Should weight by position (strikers -> knee, keepers -> hand)
- **No overtraining fatigue**: Intensity just subtracts fitness, doesn't compound
- **Facilities bonus is simple linear**: `0.5 + (facilities_level / 10.0) * 0.8`; doesn't account for club budget pressures
- **No mentality interaction with training**: A defensive player doesn't train differently under offensive systems

**Realistic?**: **Yes.** Training system reflects real talent development with aging curves and facility impact.

---

### 8. **youth.py** (3.7 KB) — MINIMAL STUB

**Status**: 🟡 Basic stub with core logic

**What's Implemented:**
- **Young player growth** (lines 29-61): CA_gap-based chance (up to 30%), biased by training focus (70%), capped at ATTR_MAX
- **Old player decline** (lines 64-80): Age 31+; 2% base decline chance per year; physical attributes only
- **Youth player generation** (lines 83-100): Random position, age 16-18, attributes scaled by club reputation

**What's NOT Implemented:**
- ❌ No academy staff/coaching quality
- ❌ No player progression tiers (academy → reserve → first team)
- ❌ No morale/homesickness for academy loanees
- ❌ No scout findings system
- ❌ No parent club loan-back mechanics
- ❌ No youth league simulation
- ❌ No talent discovery events

**Sophistication: MINIMAL**
- Reuses training logic (line 47 calls TRAINING_FOCUSES which doesn't exist — **BUG** likely)
- Generation is pure randomness

**Issues/Limitations:**
- **Line 47**: `TRAINING_FOCUSES.get(player.training_focus, [])` — this variable is undefined in youth.py; should import from training.py
- **Growth chance calculation is loose** (line 38): `min(0.3, ca_gap / 200.0 + club.facilities_level / 50.0)` can exceed 0.3
- **No salary impact**: Youth players have same wage structure as senior players
- **No loan market**: Youth aren't loaned to other clubs for development

**Realistic?**: **No.** This is explicitly marked as "Phase 2" stub. Real football has academy hierarchies.

---

### 9. **achievements.py** (10.1 KB) — FULLY IMPLEMENTED

**Status**: 🟢 Production-ready

**What's Implemented:**
- **24 achievement definitions** (lines 13-34): First win, clean sheet, win streaks (3/5/10), unbeaten (5/10), match counts (10/50/100), goals (50/100), league title, top 4, avoid relegation, youth goal, comeback win, big win, transfer profit, press master
- **Career tracking** (lines 91-107): Total W/D/L, trophies, win/unbeaten streaks, clean sheets, total goals for/against, best signing name/fee, manager rating
- **Achievement unlock logic** (lines 110-214): Iterates through all achievements after each match, checks conditions
- **Manager rating calculation** (line 151): `win_pct * 0.4 + board_confidence * 0.3 + fan_happiness * 0.3`

**Sophistication: GOOD**
- Achievements are contextual (win streaks require actual consecutive wins, not just total)
- Unbeaten tracking is separate from wins
- Career stats accumulate properly

**Issues/Limitations:**
- **Only 24 achievements**: Could be 50+ (team stats, individual player milestones, etc.)
- **No "secret" achievements**: All are disclosed
- **No difficulty scaling**: Same achievements for all clubs
- **Transfer profit not implemented** (achievement exists but unlock logic is missing)
- **Press master achievement**: No press conference system exists
- **Youth goal achievement**: Only checks if player age ≤21; doesn't track youth academy breakthrough

**Realistic?**: **Yes.** Achievements are reasonable milestones. Career stats feel authentic.

---

### 10. **events.py** (13.7 KB) — FULLY IMPLEMENTED

**Status**: 🟢 Production-ready

**What's Implemented:**
- **10 interactive event types** (lines 45-206): Sponsorship, stadium upgrade, player interview, fan protest, charity match, transfer rumor, youth breakthrough, rival provocation, training injury, community event
- **Multi-choice system** (lines 20-26): Each event has 2-3 choices with board/fan/morale/finance deltas
- **Context-aware filtering** (lines 230-235): Hides stadium upgrade if balance < 1.2M
- **Choice application** (lines 240-297): Applies deltas, validates affordability, generates inbox message
- **Daily trigger** (lines 211-237): ~12% daily chance per event pool

**Sophistication: MODERATE**
- Choices have multi-dimensional impact (not just finance)
- Transfer rumor response affects morale (realistic)
- Choices are mutually exclusive per event

**Issues/Limitations:**
- **Only 10 event types**: Feels repetitive after 5 seasons
- **No "random injury" events**: All injuries happen in match sim
- **No player-specific events**: Events never reference specific squad members (except charity/team dinner, which randomize)
- **No chain events**: Sponsor offer doesn't lead to follow-up negotiation
- **Finance affordability check is generous** (line 260): Allows balance to drop to -500k (unrealistic)
- **No event consequence tracking**: Rejected stadium doesn't reduce board confidence long-term

**Realistic?**: **Moderately.** Events feel like authentic manager dilemmas (sponsor vs. integrity, stadium investment). However, they're disconnected from season performance.

---

### 11. **tactics.py** (9.9 KB) — FULLY IMPLEMENTED, TACTICAL DEPTH

**Status**: 🟢 Production-ready

**What's Implemented:**
- **6 tactical presets** (lines 13-74): Park the Bus, Counter Attack, Balanced, Tiki-Taka, All-Out Attack, Direct Play
- **Formation auto-select** (lines 104-143): Picks best 11 + 7 subs based on formation and effective ability × match readiness
- **Team strength calculation** (lines 146-256): Composite attack/midfield/defense/GK ratings with:
  - Position suitability multiplier (0.2-1.0) applied per player
  - Mentality modifiers (±20% attack/defense)
  - Pressing intensity modifier: midfield ±15%, defense ±8% (high press = risky)
  - Tempo modifier: midfield ±2%, attack ±1%
  - Width modifier: attack ±10%, midfield ±10%
  - Defensive line: defense ±8%, midfield ±10%

**Sophistication: EXCELLENT**
- Position suitability is **load-bearing**: A CB at ST is 0.2-0.3 multiplier
- Tactical sliders create meaningful tradeoffs (high press boosts midfield but weakens defense)
- Formation slots matter; wrong positioning is penalized
- Mentality affects risk/reward (ultra-attacking boosts attack 20% but defense 20%)

**Issues/Limitations:**
- **Sliders are hardcoded 1-10 ranges**: No explanation for what each value means to end user
- **Formation positions are fixed**: 4-2-3-1 always returns same 11 positions; no flexibility for 4-2-3-1 vs 4-1-4-1 variants
- **Pressing intensity doesn't affect GK rating**: Only attack/midfield/defense
- **Width only affects attack/midfield**: Not defense (realistic for some, but not all)
- **Tempo doesn't scale fatigue**: High tempo teams don't tire faster in match sim
- **No inter-tactic synergies**: Tiki-Taka (low tempo, high press, high line) isn't explicitly rewarded for cohesion

**Realistic?**: **Yes, very.** Tactical systems create real strategic choices. Position mismatch is genuinely punishing.

---

### 12. **competition.py** (17.2 KB) — FULLY IMPLEMENTED, SOPHISTICATED

**Status**: 🟢 Production-ready

**What's Implemented:**
- **Egypt Cup structure** (lines 21-40): 32-team knockout; 5 rounds (R32, R16, QF, SF, Final) over 36 weeks
- **Seeded draw** (lines 147-165): Top 8 EPL clubs seeded; others randomized
- **Fixture scheduling** (lines 167-186): Fixtures created with dates offset from season start
- **Round advancement** (lines 223-343): Auto-detects when round is complete; draws next round; handles final
- **Penalty resolution** (lines 464-468): Draws resolved via "coin flip" (random)
- **Poisson goal generation** (lines 471-480): Realistic goal scoring for AI vs AI
- **Lower-division teams** (lines 42-58): 14 fictional clubs to pad to 32 (negative IDs = virtual)
- **Virtual club strength** (lines 453-461): EPL clubs = reputation * 0.6; lower-division = 40-60 rating

**Sophistication: HIGH**
- Poisson distribution is realistic for goal generation
- Seeded draw prevents all top teams meeting early
- Fixture persistence in DB allows resumption after reload

**Issues/Limitations:**
- **Virtual clubs can't be selected for play**: If user's team draws a virtual club, simulation is hardcoded to break (line 358)
- **Penalty resolution is coin flip**: No tactical advantage; should use XG or shot quality
- **No first-leg/second-leg format**: All rounds single match
- **Lower-division teams have no real players**: Can't simulate properly if user plays them
- **No upset tracking**: Doesn't flag when a virtual club beats an EPL team (unrealistic probability)
- **Cup success doesn't boost reputation**: Winning Egypt Cup doesn't reward the champion club

**Realistic?**: **Moderately.** Cup structure is authentic. However, virtual lower-division teams are a UX hack that breaks realism.

---

### 13. **fans.py** (3.9 KB) — BASIC IMPLEMENTATION

**Status**: 🟡 Functional stub

**What's Implemented:**
- **Attendance calculation** (lines 13-49): Base 50% stadium capacity × happiness_mod (0.5-1.2) × opponent_draw (1.0-1.5) × derby_multiplier × random ±10%
- **Fan happiness updates** (lines 52-80): Win = +3, Draw = -1, Loss = -5; big clubs lose more on losses; derby amplification
- **Atmosphere descriptions** (lines 83-94): 5-tier text (Ecstatic → Furious)
- **Happiness levels** (lines 97-108): Named categories (Ecstatic/Happy/Content/Unhappy/Furious)

**What's NOT Implemented:**
- ❌ No ultras faction system (aggressive vs. passive)
- ❌ No protest mechanics (fans can't force manager out)
- ❌ No ticket price scaling (always base 50 EGP, 65-80 for big matches)
- ❌ No season ticket revenue
- ❌ No merchandise income
- ❌ No traveling fans attendance (away fans in calculation)
- ❌ No stadium incidents/violence

**Sophistication: LOW**
- Happiness calculation is simple linear (outcome only)
- No momentum (winning streaks don't compound happiness gains)
- No rivalry context beyond derby modifier

**Issues/Limitations:**
- **Attendance can exceed capacity** (line 49): `clamp()` is used, but base calculation might already exceed stadium_capacity
- **Derby multiplier not defined in module**: Called from rivalries.py (line 42) but imported dynamically
- **Happiness doesn't decay**: Season-long misery doesn't accumulate naturally
- **No unhappy player transfers**: Low fan happiness should cause player morale hits, linked to transfer requests

**Realistic?**: **Partially.** Attendance and happiness swing with results. However, ultras culture and protest mechanics are missing.

---

### 14. **commentary.py** (9.8 KB) — FULLY IMPLEMENTED

**Status**: 🟢 Production-ready

**What's Implemented:**
- **Bilingual commentary** (lines 10-164): English + Arabic templates for 7 event types
- **Template system** (lines 167-181): Substitutes player/club/detail placeholders
- **Varied templates per event** (lines 10-86): 8-12 different phrasings per event
- **Injury detail substitution** (lines 69-71, 147-149): Injury type inserted into narrative

**Sophistication: GOOD**
- Commentary feels alive with varied phrasings
- Bilingual support is rare in sports sims
- Event-specific language (e.g., red card text emphasizes sent-off)

**Issues/Limitations:**
- **No context awareness**: Commentary doesn't know if goal is early/late, for winning/losing team, or against expected opponent
- **No cumulative narrative**: Each event is isolated; no "he's on fire" after hat-trick
- **Arabic translation accuracy unclear**: Not verified by native speaker
- **Only 7 event types covered**: Substitutions, injuries mid-play, near-misses not described
- **No variance based on match state**: 1-0 goal and 5-0 goal use same templates

**Realistic?**: **Yes.** Commentary is varied and appropriate. Not sophisticated, but authentic.

---

### 15. **media.py** (17.9 KB) — FULLY IMPLEMENTED

**Status**: 🟢 Production-ready

**What's Implemented:**
- **22 headline templates** (lines 17-80): Categorized by result type (big win, narrow win, draw, loss, big loss, derby variants, cup variants)
- **Match reports** (lines 210-302): Includes scorers, stats, cards, injuries, man of the match
- **League roundup** (lines 337-376): Matchday summary with table snapshot and big results
- **Board briefs** (lines 379-430): Weekly objective progress tracking with color-coded status (✅ 🟢 🟠 🔴)
- **Random events** (lines 83-175): 15 mid-season narrative events (12% chance)

**Sophistication: EXCELLENT**
- Headlines are context-aware (big_win = ≥3 goal diff, derby_win checks rivalry)
- Reports include narrative texture (e.g., "comprehensive victory" vs "hard-earned")
- Board briefs show projected progress, not just snapshots

**Issues/Limitations:**
- **Headline logic is result-only**: Doesn't account for opponent strength (beating relegation favorite = same headline as beating champion)
- **Man of the Match selection is weak** (line 254): Just picks max rating; doesn't verify player actually played 90 minutes
- **Random events lack follow-up**: Sponsorship offer doesn't lead to contract negotiations
- **Team dinner event names random player each time** (line 159): Could be more cohesive (same player if recurring event)
- **No controversial headlines**: Ref decisions, injuries to key players aren't flagged as narrative hooks

**Realistic?**: **Yes.** Media system provides authentic narrative texture. Headlines feel like sport journalism.

---

## SUMMARY TABLE

| Module | Status | Implementation | AI Sophistication | Realism |
|--------|--------|-----------------|-------------------|---------|
| match_engine | 🟢 | 95% | Moderate | High |
| transfers | 🟢 | 100% | Moderate | Moderate |
| calendar | 🟢 | 100% | N/A | High |
| season | 🟢 | 100% | Low | Moderate |
| board | 🟢 | 100% | Low | High |
| finance | 🟡 | 20% | N/A | Low |
| training | 🟢 | 100% | N/A | High |
| youth | 🟡 | 40% | Low | Low |
| achievements | 🟢 | 100% | N/A | High |
| events | 🟢 | 90% | Low | Moderate |
| tactics | 🟢 | 100% | N/A | High |
| competition | 🟢 | 95% | Moderate | Moderate |
| fans | 🟡 | 60% | Low | Moderate |
| commentary | 🟢 | 100% | N/A | High |
| media | 🟢 | 100% | N/A | High |

---

## CRITICAL FINDINGS

### Strengths
1. **Match simulation is minute-by-minute and realistic**: Fatigue, red cards, position mismatch all have real impact
2. **Tactical depth is genuine**: Sliders create meaningful tradeoffs; position suitability is load-bearing
3. **Async transfer negotiations feel authentic**: Two-phase with counter-offers and convergence
4. **Calendar flow is comprehensive**: Handles all daily operations logically
5. **Board objectives scale with expectations**: Higher-rep clubs face harder targets
6. **Bilingual support** in commentary and messages is excellent

### Weaknesses
1. **Financial system is a stub**: No FFP, no budget caps, no realistic income scaling
2. **Youth system is minimal**: No academy tiers, no scouting, no loan mechanics
3. **AI clubstill dump-level**: Doesn't scout, doesn't negotiate mid-season, transfers are instant post-season
4. **No player personalities**: All respond identically to wages and opportunities
5. **Season progression lacks narrative**: No "manager on the brink" threat, no player morale decay
6. **Match substitutions not simulated**: Users can set XI, but bench never enters during play

### Hidden Bugs/Shortcomings
1. **youth.py line 47**: `TRAINING_FOCUSES` is undefined; should import from training.py
2. **calendar.py line 83**: Cup exception silently passes; player unaware if cup unavailable
3. **competition.py**: Virtual lower-division clubs crash if user plays them
4. **match_engine.py**: No mechanism for user substitutions mid-match
5. **finance.py**: Matchday income assumes exactly 2 home games per month (incorrect)
6. **board_objectives**: Secondary objectives are hard-coded and generic

### Realism Assessment
- **Match simulation**: 8/10 (realistic but lacks set pieces, substitutions, injury severity scaling)
- **Transfer market**: 6/10 (negotiation logic is good, but AI behavior is passive)
- **Training/development**: 8/10 (growth curves and facility impact are authentic)
- **Season progression**: 6/10 (calendar flow is good, but player morale doesn't decay)
- **Financial model**: 2/10 (stub only)
- **Youth system**: 3/10 (minimal, placeholder)
- **Overall**: **6/10** — Strong core simulation with gaps in financial realism and AI sophistication

---

## RECOMMENDATION

The engine is **production-ready for a beta** with these caveats:

1. **Finish the financial system** (Phase 2 blocker): Implement FFP rules, realistic income, and budget caps
2. **Expand youth mechanics**: Add academy tiers, scouting, and loan-back rules
3. **Increase AI sophistication**: Give clubs personalities (big spenders, youth developers, balance-sheet focused)
4. **Add substitution mechanic**: Bench players should be usable mid-match
5. **Implement player personalities**: Some players should demand moves, refuse wage cuts, etc.

The **match engine is genuinely good** and could stand alone as a sports simulation. The **transfer system is solid**. The **calendar is comprehensive**. The gaps are in secondary systems (finance, youth, AI behavior).