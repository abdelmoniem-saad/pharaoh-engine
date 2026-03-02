# ⚽ Pharaoh Engine

**Mobile-first Egyptian Football Management Simulation Game**

A deeply authentic football management game centered on the Egyptian league ecosystem. Combines casual mobile accessibility with hardcore simulation depth — inspired by Football Manager and FIFA Career Mode but built specifically for Egyptian football culture.

Built with Python + Flet (Flutter-backed) for cross-platform deployment: Android, iOS, Web, and Desktop.

---

## 🎮 Features

### 🏟️ League & Season
- **18 fictionalized Egyptian Premier League clubs** with realistic reputations, finances, stadiums, and squad sizes
- **Full season simulation** — 34-matchday double round-robin league
- **Multi-season career mode** — season transitions with aging, retirements, contract renewals, and youth intake
- **Season summary & awards** — Champion, Golden Boot, Golden Glove, Young Player of the Season, Most Assists
- **Board evaluation** — end-of-season performance review against club-specific expectations

### ⚔️ Match Engine
- **Minute-by-minute simulation** producing goals, assists, cards, injuries, penalties, corners, and saves
- **Live match playback** — watch the match unfold from minute 0 to 90+ with real-time event feed and option to skip to end
- **Formation & position suitability** — players out of position lose 20-80% effectiveness; a CB playing ST will barely score
- **Tactical slider impact** — pressing, tempo, width, and defensive line all create real trade-offs (not cosmetic)
- **Fatigue system** — teams tire after minute 60 based on average squad stamina; substitutions genuinely help
- **Red card consequences** — sent-off players are removed from the XI; team plays at reduced strength (10 men = -9%)
- **Fan happiness → home advantage** — happy fans give +8% boost; furious fans give zero home advantage
- **Training focus → match bonuses** — players with "Shooting" or "Defending" focus get small in-match attack/defense boosts
- **Smart foul distribution** — higher-pressing teams foul more; low-composure, high-aggression defenders foul the most
- **Dynamic attendance & ticket revenue** — attendance varies by fan happiness, opponent reputation, and randomness; generates real income
- **Individual player ratings** (1-10) based on goals, assists, cards, clean sheets, and position suitability
- **Commentary system** — contextual match event descriptions

### 🧠 Tactics
- **7 formations**: 4-4-2, 4-3-3, 4-2-3-1, 3-5-2, 4-1-4-1, 5-3-2, 4-3-1-2
- **6 tactical presets** (casual mode): Park the Bus, Counter Attack, Balanced, Tiki-Taka, All-Out Attack, Direct Play
- **7 mentality levels**: Ultra Defensive → Ultra Attacking
- **4 tactical sliders** (advanced mode): Pressing Intensity, Tempo, Width, Defensive Line — each with meaningful trade-offs
- **Auto-selection AI** — best XI chosen by position suitability × fitness × morale × form
- **Substitution system** — swap players during matches; affects fitness, morale, and match outcome

### 👤 Player System
- **~450 procedurally generated players** with 32+ individual attributes across technical, physical, mental, and GK categories
- **Position-specific overall ratings** — a CM is rated differently from a ST using position-weighted attribute formulas
- **Dual positions** — players can have primary and secondary positions with suitability multipliers
- **Fitness, form, morale** — all dynamically tracked and impacting match performance
- **Injury system** — match injuries (7-42 days) with named types (hamstring, ACL, ankle, etc.) and daily recovery
- **Suspension system** — yellow card accumulation (5 = 1-match ban), red cards (1-3 match ban)
- **Player development** — weekly training with 8 focus programs (Shooting, Defending, Physical, Playmaking, Mental, Goalkeeping, Set Pieces, Balanced)
- **Age-based growth/decline** — young players (≤23) develop faster; players 32+ physically decline
- **Training intensity levels** — Light, Normal, Intense, Double Sessions (higher = faster growth but injury risk)
- **Morale system** — wins, personal ratings, playing time, captaincy, and benchwarming all affect morale
- **Player milestones** — tracked appearances, goals, and career achievements
- **All development persisted** — attribute gains, current ability changes, and training progress saved to database

### 💰 Financial System
- **Realistic financial modeling** — balance, transfer budget, wage budget, wage bill all tracked
- **Monthly income/expenses** — matchday revenue, sponsorship, TV money vs. wages and facility costs
- **Dynamic matchday income** — attendance-based ticket revenue (50-80 EGP/ticket depending on opponent) credited to club balance
- **Transfer fees properly deducted** — buying reduces balance + transfer budget; selling increases both
- **Wage bill tracking** — transfers, contract renewals, and free agent signings all correctly update the club's weekly wage bill
- **Affordability checks** — can't spend beyond budget; events that cost money check if the club can actually afford it
- **Monthly financial reports** via inbox

### 🔄 Transfer Market
- **Async negotiations** — fee negotiation (up to 3 rounds of offers/counter-offers) then wage negotiation, each taking a game day
- **Counter-offers converge** — selling club's counter always goes DOWN with each attempt (never increases)
- **Player valuation engine** — based on current ability, potential, age, and contract length
- **Free agent signing** with wage negotiation
- **Transfer listing** — list players for sale; AI clubs bid with 10% daily chance
- **Loan system** — loan in/out with wage split and optional buy clause
- **Contract renewal** — acceptance based on wage offer, morale, age, playing time, and club reputation
- **Expiring contract warnings** — monthly alerts for contracts within 90 days of expiry
- **Transfer windows** — summer and winter windows with countdown to opening
- **Transfer history** tracking
- **AI inter-club transfers** during off-season — AI clubs buy/sell with proper financial handling (fees, wages, budgets all update)
- **Expired contracts auto-renewed** at season end for all clubs (not just cosmetic — actually updates the DB)

### 📋 Board & Objectives
- **Club-specific season expectations** — top clubs expected to win the league; smaller clubs expected to avoid relegation
- **Board confidence** (0-100) — rises with wins, drops with losses; bigger clubs are less patient
- **Season objectives** — primary (league position) and secondary (goals scored, youth development, goal difference)
- **End-of-season evaluation** — board reviews performance against objectives with confidence bonuses/penalties

### 📣 Fans & Atmosphere
- **Fan happiness** (0-100) — affected by results; bigger clubs' fans are more demanding
- **Attendance calculation** — based on stadium capacity, fan happiness, opponent draw, and randomness
- **Stadium atmosphere descriptions** — from "electric" to "protests expected"
- **Fan happiness affects home advantage** in match simulation

### 🏋️ Training System
- **8 training programs**: Shooting, Defending, Physical, Playmaking, Mental, Goalkeeping, Set Pieces, Balanced
- **4 intensity levels** with growth multiplier / fitness cost / injury risk trade-offs
- **Facility-quality bonus** — better facilities = faster player development
- **Position-based recommended focus** — auto-suggests appropriate training per position
- **Weekly training reports** via inbox
- **AI clubs also train** — all clubs develop their players weekly (prevents user squad from outpacing AI over multiple seasons)

### 🎯 Events & Achievements
- **Random interactive events** (~12% daily chance) — sponsorship offers, stadium upgrades, charity matches, fan protests, talent scouts, derby hype, and more
- **Player choice matters** — each event offers 2 options affecting finances, board confidence, fan happiness, and squad morale
- **Financial checks on events** — expensive choices verify the club can afford them before deducting
- **Career achievements** — unlockable milestones tracked across matches
- **Career statistics** — total wins, losses, draws, goals for/against, clean sheets

### 📱 Mobile-Optimized UI
- **Portrait-first layout** — designed for one-handed mobile play
- **Card-based interface** — tap-friendly containers with consistent spacing and rounded corners
- **Dark theme** — OLED-friendly color palette with accent highlights
- **Bottom navigation bar** — 5 tabs (Club, Squad, Match, Transfers, Inbox) with unread badge
- **Tab-based screens** — swipeable content areas within each screen
- **Compact data display** — player rows, standings, and fixtures all optimized for small screens
- **Snackbar notifications** — non-intrusive feedback for user actions
- **Mark all as read** — batch inbox management

### 📰 Media & Inbox
- **Match reports** — auto-generated post-match summaries with scoreline, goalscorers, and stats
- **League roundup** — consolidated gameweek results in a single message per matchday
- **Random mid-season news** — injury scares, training incidents, morale events
- **Transfer notifications** — offer received, fee agreed, wage negotiation, transfer complete
- **Contract warnings** — expiring contract alerts
- **Board communications** — seasonal objectives, evaluations, event outcomes
- **Categorized messages** — general, board, transfer, with visual category indicators

### 🌍 Egyptian Authenticity
- **27 Egyptian governorate profiles** — each with population-weighted talent generation and attribute biases
- **Regional talent dynamics** — Cairo/Alexandria produce more players; Upper Egypt produces physically strong players
- **Culturally appropriate club names** — fictionalized but recognizable Egyptian league structure
- **Egyptian-scale finances** — realistic EGP-denominated budgets, wages, and transfer fees

### 💾 Save System
- **SQLite-based persistence** — full game state saved to `.db` files
- **Auto-save** — configurable interval
- **Multiple save slots** — create, load, and manage different career saves
- **New game wizard** — manager name entry → club selection with governorate grouping

---

## 🏗️ Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.13+ |
| UI Framework | Flet ≥0.80 (Flutter-backed, pure Python) |
| Database | SQLite (stdlib) |
| Data Models | Pydantic v2 |
| Testing | pytest + pytest-cov |
| Mobile Build | `flet build apk` / `flet build ipa` |
| Web Deploy | `flet run --web` |

---

## 📁 Project Structure

```
pharaoh-engine/
├── main.py                    # App entry point
├── requirements.txt           # Python dependencies
├── pyproject.toml             # Project metadata
├── buildozer.spec             # Android/iOS build config
├── src/
│   ├── core/                  # Simulation engine (pure Python, no UI deps)
│   │   ├── match_engine.py    # Minute-by-minute match simulation
│   │   ├── player.py          # Ratings, fitness, form, morale, development
│   │   ├── tactics.py         # Formations, presets, team strength calculation
│   │   ├── club.py            # Club management, AI manager logic
│   │   ├── league.py          # Fixture generation, standings, season checks
│   │   ├── calendar.py        # Game loop, day advancement, matchday orchestration
│   │   ├── season.py          # End-of-season processing, new season creation
│   │   ├── training.py        # Weekly training, intensity, attribute growth/decline
│   │   ├── transfers.py       # Async negotiations, loans, valuations, contracts
│   │   ├── finance.py         # Income, expenses, cash flow, budget checks
│   │   ├── board.py           # Objectives, confidence, season evaluation
│   │   ├── fans.py            # Attendance, happiness, atmosphere
│   │   ├── events.py          # Random interactive events with player choices
│   │   ├── achievements.py    # Career stats, unlockable achievements
│   │   ├── media.py           # Match reports, headlines, league roundups
│   │   ├── commentary.py      # Contextual match event commentary
│   │   ├── youth.py           # Youth academy, annual intake
│   │   ├── regional.py        # Governorate talent profiles & attribute biases
│   │   └── competition.py     # Cup/continental stubs (future)
│   ├── data/                  # Database & data layer
│   │   ├── database.py        # SQLite schema & connection management
│   │   ├── models.py          # Pydantic data models (50+ model classes)
│   │   ├── queries.py         # CRUD operations, standings, transfers, inbox
│   │   └── seed.py            # Procedural player & club generation
│   ├── ui/                    # Flet UI layer (mobile-first)
│   │   ├── app.py             # App entry, navigation, global state
│   │   ├── theme.py           # Color palette, sizing constants
│   │   ├── screens/           # Game screens
│   │   │   ├── main_menu.py   # New game, load game, club selection
│   │   │   ├── match_day.py   # Pre-match preview, advance day, season end
│   │   │   ├── live_match.py  # Real-time match playback with events
│   │   │   ├── post_match.py  # Post-match results, ratings, stats
│   │   │   ├── pre_match.py   # Team sheet, opponent info
│   │   │   ├── squad.py       # Squad list, player details, captain, shirts
│   │   │   ├── tactics.py     # Formation picker, presets, sliders
│   │   │   ├── transfers.py   # Transfer market, search, buy/sell, loans
│   │   │   ├── table.py       # League standings, top scorers, form
│   │   │   ├── fixtures.py    # Past results, matchday history
│   │   │   ├── inbox.py       # Messages, transfer actions, mark all read
│   │   │   ├── club_overview.py  # Club dashboard, finances, board
│   │   │   ├── season_summary.py # Awards, standings, board review
│   │   │   └── settings.py    # Game settings, save/load
│   │   └── widgets/           # Reusable UI components
│   │       ├── cards.py       # Section cards, info tiles, action cards
│   │       ├── nav_bar.py     # Bottom navigation with unread badge
│   │       ├── player_card.py # Player detail card
│   │       ├── match_result.py # Match score display
│   │       └── stat_bar.py    # Statistical bar chart widget
│   └── utils/                 # Utilities
│       ├── config.py          # Constants, enums, formations, governorates
│       ├── rng.py             # Seeded deterministic RNG system
│       └── localization.py    # English/Arabic string tables (future)
├── data/seed/                 # JSON seed data
│   ├── clubs.json             # 18 EPL club definitions
│   ├── governorates.json      # Regional talent profiles
│   └── competitions.json      # League/cup structures
├── saves/                     # Save game directory
│   └── default.db             # Default save file
└── tests/                     # Test suite (45 tests)
    ├── test_match_engine.py   # Match simulation tests
    ├── test_player.py         # Player rating & development tests
    ├── test_tactics.py        # Formation & team strength tests
    ├── test_league.py         # Fixture generation & standings tests
    ├── test_finance.py        # Financial modeling tests
    └── test_training.py       # Training system tests
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- pip

### Installation
```bash
# Clone the repository
git clone https://github.com/yourusername/pharaoh-engine.git
cd pharaoh-engine

# Install dependencies
pip install -r requirements.txt

# Run the game (desktop window)
python main.py

# Run as web app
flet run --web main.py

# Run tests
pytest tests/ -v
```

### Build for Mobile
```bash
# Android
flet build apk

# iOS
flet build ipa
```

---

## 🧪 Testing

```bash
# Run all 45 tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=term-missing
```

Test coverage includes:
- Match engine simulation & event generation
- Player overall rating calculation by position
- Tactical team strength computation with formation suitability
- League fixture generation & standings management
- Financial modeling (income, expenses, cash flow)
- Training system (attribute growth, age decline, injury risk)

---

## 🗺️ Development Roadmap

### Phase 1 — MVP ✅
Single-season league simulation with squad management, tactical presets, match engine, and basic UI.

### Phase 2 — Depth ✅ (Current)
- ✅ Multi-season career with aging, retirements, and youth intake
- ✅ Full transfer market with async negotiations, loans, and free agents
- ✅ Training system with 8 programs, 4 intensities, and weekly development
- ✅ Interactive random events with financial/morale consequences
- ✅ Board objectives and season evaluation
- ✅ Career achievements and statistics
- ✅ Season awards (Golden Boot, Golden Glove, Young Player)
- ✅ Live match playback with minute-by-minute events
- ✅ Contract renewal system with realistic acceptance logic
- ✅ AI club management (transfers, training, tactics, recovery)
- ✅ Proper financial tracking across all systems (transfers, wages, attendance, events)

### Phase 3 — Culture (Next)
- Arabic localization and right-to-left UI support
- Enhanced fan ultras system with tifo, chants, and supporter groups
- Deeper governorate talent dynamics with regional rivalries
- Egypt Cup knockout competition
- CAF Champions League group stage
- Enhanced match narratives and press conferences
- Manager reputation system

### Phase 4 — Launch
- Mobile deployment (Google Play Store / Apple App Store)
- Onboarding tutorial and guided first season
- Ethical free-to-play monetization (cosmetics only)
- Community features and leaderboards
- Official licensing partnerships

---

## 🎯 Design Philosophy

1. **Casual surface, deep core** — Easy to pick up with presets and auto-select; advanced users can tweak every tactical slider and training program
2. **Every decision matters** — Formation, tactics, training, transfers, substitutions, and events all have real, measurable impact on match outcomes and long-term progression
3. **Egyptian authenticity** — Governorate-specific talent, EGP-scale finances, culturally accurate fan dynamics, and recognizable league structure
4. **Lean architecture** — Pure Python simulation engine fully separated from UI; runs on mobile hardware without GPU dependencies
5. **Deterministic simulation** — Seeded RNG ensures reproducible results for testing and fair gameplay
6. **Financial integrity** — Every EGP is tracked: transfers deduct budgets and update wage bills, attendance generates real income, events check affordability
7. **AI parity** — AI clubs train, develop, transfer, recover from injuries, and renew contracts just like the player's club — no hidden advantages

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
