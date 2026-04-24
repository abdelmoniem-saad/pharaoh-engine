# Explore project structure

Perfect! Now I have all the information needed. Let me create a comprehensive report:

## PHARAOH ENGINE - Complete Project Exploration Report

---

### 1. PROJECT OVERVIEW

**Name:** Pharaoh Engine
**Purpose:** Mobile-first Egyptian Football Management Simulation Game
**Version:** 0.3.0

**Description:**
A deeply authentic football management game centered on the Egyptian league ecosystem, combining casual mobile accessibility with hardcore simulation depth. Inspired by Football Manager and FIFA Career Mode but built specifically for Egyptian football culture. Designed for cross-platform deployment: Android, iOS, Web, and Desktop.

**Development Status:** Phase 3 (Culture) - currently in active development with mature features implemented.

---

### 2. PROJECT STRUCTURE

**Top-Level Directories:**

```
/pharaoh-engine/
├── src/                  # Main source code (3 major layers)
│   ├── core/            # Pure Python simulation engine (6,335 LOC) - NO UI deps
│   ├── data/            # Database & data layer (3,015 LOC)
│   ├── ui/              # Flet UI layer - mobile-first (9,970 LOC)
│   └── utils/           # Constants, config, RNG, localization
│
├── data/seed/           # JSON seed data for procedural generation
│   ├── clubs.json       # 18 Egyptian Premier League clubs
│   ├── governorates.json # 27 regional talent profiles
│   ├── competitions.json # League/cup structures
│   └── rivalries.json   # 5 derby rivalry definitions
│
├── tests/               # Test suite (1,257 LOC, ~45 tests)
├── saves/               # Save game directory (SQLite .db files)
├── assets/              # Game assets
├── build/               # Build artifacts
├── tools/               # Build/utility scripts
│
├── main.py              # App entry point
├── pyproject.toml       # Project metadata & build config
├── requirements.txt     # Python dependencies
└── README.md            # Comprehensive documentation
```

---

### 3. ARCHITECTURE OVERVIEW

**Three-Layer Clean Architecture:**

#### **Layer 1: Core Simulation Engine** (`src/core/`)
Pure Python simulation logic with NO UI dependencies. Fully testable and portable to mobile.

**Key Modules (20 files, 6,335 lines):**

| Module | Purpose | LOC |
|--------|---------|-----|
| `match_engine.py` | Minute-by-minute match simulation with goals, cards, injuries | 758 |
| `calendar.py` | Season calendar, day advancement, matchday orchestration | 1,046 |
| `transfers.py` | Async negotiations, loans, valuations, contract renewals | 850 |
| `competition.py` | Egypt Cup 32-team knockout tournament (draws, penalties) | 481 |
| `player.py` | Player ratings, fitness, form, morale, development | 200 |
| `board.py` | Objectives, confidence levels, season evaluation | 233 |
| `media.py` | Match reports, headlines, league roundups | 432 |
| `training.py` | Weekly training, 8 programs, 4 intensities | 169 |
| `league.py` | Fixture generation, standings, season checks | 182 |
| `tactics.py` | 7 formations, 6 presets, 7 mentality levels | 257 |
| `season.py` | End-of-season processing, new season creation | 425 |
| `events.py` | Random interactive events with player choices | 299 |
| `finance.py` | Income, expenses, cash flow tracking | 54 |
| `club.py` | Club management, AI manager logic | 104 |
| `fans.py` | Attendance, happiness, atmosphere | 109 |
| `commentary.py` | Contextual match event descriptions | 182 |
| `achievements.py` | Career stats, unlockable milestones | 10,082 |
| `regionalpy` | Governorate talent profiles & biases | 94 |
| `rivalries.py` | Derby rivalries with intensity multipliers | 142 |
| `youth.py` | Youth academy, annual intake | 101 |

#### **Layer 2: Data Layer** (`src/data/`)
SQLite persistence with Pydantic v2 models (3,015 LOC).

**Key Files:**

| File | Purpose | LOC |
|------|---------|-----|
| `database.py` | SQLite schema, migrations, connection management | 667 |
| `models.py` | 50+ Pydantic models for all game entities | 424 |
| `queries.py` | CRUD operations, standings, transfers, inbox queries | 1,315 |
| `seed.py` | Procedural player & club generation | 485 |
| `chart_queries.py` | Statistical query helpers for UI charts | 122 |

**Database:**
- SQLite with WAL mode for reliability
- Foreign key constraints enabled
- Schema migrations with drift repair
- Multiple save slots supported

**Pydantic Models (50+):**
- `Player` - with 32+ attributes across technical, physical, mental, goalkeeper categories
- `Club` - finances, squad, reputation, facilities
- `MatchResult`, `MatchEvent`, `MatchStats` - match simulation output
- `GameState`, `Fixture`, `InboxMessage` - core game entities

#### **Layer 3: UI Layer** (`src/ui/`)
Flet (Flutter-backed) for cross-platform mobile-first design (9,970 LOC).

**Structure:**
- `app.py` - Navigation, shared state, lifecycle (386 LOC)
- `theme.py` - Colors, sizing, dark theme (331 LOC)
- `screens/` - 14 game screens (8,331 LOC)
- `widgets/` - Reusable components (1,251 LOC)

**Screen List:**
- `main_menu.py` - New game, load, club selection
- `match_day.py` - Match preview, advance day, season end
- `live_match.py` - Real-time playback with minute-by-minute events
- `post_match.py` - Results, player ratings, statistics
- `pre_match.py` - Team sheet, opponent info
- `squad.py` - Squad list, player details, captain designation
- `tactics.py` - Formation picker, tactical sliders
- `transfers.py` - Transfer market, negotiations, search
- `table.py` - League standings, top scorers, form
- `fixtures.py` - Past results, matchday history
- `inbox.py` - Messages, transfer actions, mark read
- `club_overview.py` - Club dashboard, finances, board
- `season_summary.py` - Awards, standings, board review
- `settings.py` - Game settings, save/load
- `history.py` - Career history & statistics

**Widgets:**
- `cards.py` - Section cards, info tiles (589 LOC)
- `charts.py` - Statistical visualizations (313 LOC)
- `match_result.py`, `player_card.py`, `nav_bar.py`, `stat_bar.py`, `news.py`

---

### 4. TECHNOLOGY STACK

| Layer | Technology | Version |
|-------|-----------|---------|
| **Language** | Python | 3.11+ (requires 3.13+ for type hints) |
| **UI Framework** | Flet (Flutter-backed) | ≥0.80 |
| **Database** | SQLite | stdlib |
| **Data Validation** | Pydantic | v2 (≥2.5.0) |
| **Testing** | pytest + pytest-cov | 7.4.0+, 4.1.0+ |
| **Build System** | setuptools | 68.0+ |
| **Mobile Build** | flet build apk/ipa | - |
| **Web Deployment** | flet run --web | - |

**Dependencies (minimal):**
```
flet>=0.80.0
pydantic>=2.5.0
pytest>=7.4.0
pytest-cov>=4.1.0
```

---

### 5. KEY CONFIGURATION FILES

#### **pyproject.toml**
- Project metadata (name, version 0.1.0, description)
- Build system: setuptools backend
- Python requirement: ≥3.11
- Minimal dependencies: flet, pydantic
- Optional dev dependencies: pytest, pytest-cov
- Flet app configuration (exclude files like tests, saves, .db)
- Android target: arm64-v8a only

#### **src/utils/config.py**
**Constants & Enums (347 lines):**

- **Game Constants:**
  - 18 teams, 34 matchdays, 18-35 squad size
  - Attributes: 1-20 scale
  - Ability: 1-200 scale

- **Positions (12):** GK, CB, LB, RB, CDM, CM, CAM, LW, RW, LM, RM, ST

- **Position Groups:** Goalkeeper, Defender, Midfielder, Attacker

- **Mentality Levels (7):** Ultra Defensive → Ultra Attacking

- **Formations (7):** 4-4-2, 4-3-3, 4-2-3-1, 3-5-2, 4-1-4-1, 5-3-2, 4-3-1-2

- **Governorates (27):** Each with talent pool, style bias, attribute bonuses, player volume

- **Match Events (14):** Goal, assist, yellow/red card, substitution, injury, penalty, shot, save, corner, free kick, etc.

- **Ramadan Calendar (2025-2035):** With date mappings and stamina/training impact

- **Season Expectations:** Win League, Title Challenge, Top 4, Top Half, Mid-Table, Avoid Relegation

---

### 6. CORE GAME SYSTEMS

#### **Match Engine** (`match_engine.py` - 758 LOC)
- **Minute-by-minute simulation** (0-90+) with realistic event generation
- **Tactical Impact:** Formation, position suitability, mentality, pressing, tempo, width all affect team strength
- **Player Ratings:** Based on position, fitness, form, morale
- **Stamina System:** Teams tire after minute 60 based on squad average stamina
- **Red Card Consequences:** 10 men = -9% strength reduction
- **Fan Happiness:** Affects home advantage (+8% for happy fans, 0% for furious)
- **Training Focus Bonuses:** Small in-match attack/defense boosts
- **Derby Modifiers:** Amplified morale/atmosphere effects
- **Ramadan Impact:** 10% stamina reduction for fasting players

#### **Season Calendar** (`calendar.py` - 1,046 LOC)
- **Day-by-day progression** with automatic fixture scheduling
- **Matchday Orchestration:** Simulates all AI matches, updates standings, distributes messages
- **Cup Integration:** Interleaved Egypt Cup matches (5 rounds, Oct-Apr)
- **Monthly Processing:** Finances, training, transfers, contract expirations
- **Random Events:** ~12% daily chance of interactive events (sponsorship, stadium upgrades, protests, etc.)
- **AI Club Updates:** Training, recovery, transfers, negotiations for all clubs

#### **Transfer Market** (`transfers.py` - 850 LOC)
- **Async Negotiations:** Fee negotiation (up to 3 rounds) then wage negotiation
- **Counter-Offers:** Selling club's counter-offer always decreases with each attempt
- **Player Valuation:** Based on current ability, potential, age, contract length
- **Free Agent Signing** with wage negotiation
- **Transfer Listing:** List players for sale; AI clubs bid with 10% daily chance
- **Loan System:** In/out with wage split and optional buy clause
- **Contract Renewal:** Acceptance logic based on wage, morale, age, playing time, club reputation
- **Expiring Contract Alerts:** Monthly inbox warnings for contracts within 90 days
- **Transfer Windows:** Summer (Jun 1 - Aug 31) and Winter (Jan 1 - Jan 31)
- **AI Inter-Club Transfers:** During off-season with proper financial handling

#### **Training System** (`training.py` - 169 LOC)
- **8 Focus Programs:** Shooting, Defending, Physical, Playmaking, Mental, Goalkeeping, Set Pieces, Balanced
- **4 Intensity Levels:** Light, Normal, Intense, Double Sessions
- **Growth Multiplier Trade-offs:** Higher intensity = faster growth but higher injury risk
- **Facility Bonus:** Better facilities = faster development
- **Age-Based Development:** Young players (≤23) develop faster; 32+ decline
- **AI Training:** All clubs train weekly (prevents player squad from outpacing AI over seasons)

#### **Board System** (`board.py` - 233 LOC)
- **Season Expectations:** Tier-based (derived from club reputation)
- **Board Confidence:** 0-100 scale, rises with wins, drops with losses
- **End-of-Season Evaluation:** Reviews performance against objectives
- **Confidence Penalties/Bonuses:** Applied based on league finish and objectives met

#### **Financial System** (`finance.py` - 54 LOC)
- **Realistic EGP-scale finances**
- **Monthly Income/Expenses:** Matchday revenue, sponsorship, TV money vs. wages, facility costs
- **Dynamic Attendance:** Varies by fan happiness, opponent reputation, randomness
- **Ticket Revenue:** 50-80 EGP per ticket depending on opponent
- **Transfer Fees:** Properly deducted from balance & transfer budget
- **Wage Bill Tracking:** Updated on transfers, contracts, free agent signings
- **Affordability Checks:** Events verify clubs can afford financial decisions

#### **Egypt Cup** (`competition.py` - 481 LOC)
- **32-team knockout tournament** (14 lower-division virtual clubs + 18 EPL clubs)
- **Seeded Draw:** Top 8 EPL clubs seeded into separate halves
- **5 Rounds:** Round of 32, 16, Quarter-finals, Semi-finals, Final
- **Interleaved Scheduling:** Cup rounds between league matchdays (Oct-Apr)
- **Penalty Shootouts:** Drawn matches resolved via penalties
- **AI Simulation:** Non-user cup matches auto-simulated
- **Cup-specific Inbox:** Draw announcements, results, eliminations

#### **Derby Rivalries** (`rivalries.py` - 142 LOC)
- **5 Named Rivalries:** Cairo Derby, Canal Derby, Mediterranean Derby, etc.
- **Intensity Levels (1-5):** Affect atmosphere and consequences
- **Attendance Boost:** 1.1x-1.5x more fans for derby matches
- **Fan Happiness Amplification:** 2.5x multiplier for wins/losses
- **Derby-specific Headlines:** Unique media coverage
- **Arabic Bilingual Names**

#### **Media & Inbox System** (`media.py` - 432 LOC)
- **Match Reports:** Auto-generated post-match summaries with scorelines, goalscorers
- **League Roundup:** Consolidated gameweek results (one message per matchday)
- **Random Mid-Season News:** Injury scares, training incidents, morale events
- **Transfer Notifications:** Offer received, fee agreed, wage negotiations, completion
- **Contract Warnings:** Expiring contract alerts
- **Board Communications:** Seasonal objectives, evaluations, event outcomes
- **Categorized Messages:** General, board, transfer with visual indicators
- **Bilingual Support:** English/Arabic messages

#### **Youth Academy** (`youth.py` - 101 LOC)
- **Annual Intake:** New young players generated each season
- **Procedural Generation:** Based on regional talent profiles
- **Development Tracking:** Youth players develop through training

#### **Regional System** (`regional.py` - 94 LOC)
- **27 Governorates:** Each with talent pool, style bias, attribute bonuses
- **Population-Weighted Generation:** Cairo/Alexandria produce more players
- **Regional Attribute Biases:** Cairo technical, Alexandria physical, Upper Egypt strong, etc.

#### **Achievements & Statistics** (`achievements.py` - 10,082 LOC)
- **Career Milestones:** Tracked appearances, goals, achievements
- **Career Statistics:** Total wins, losses, draws, goals for/against, clean sheets
- **Unlockable Achievements:** Long-term progression tracking

---

### 7. DATA MODELS & PERSISTENCE

**Key Pydantic Models (50+ classes in `models.py`):**

**Player Entity:**
- `PlayerAttributes` - 27 attributes (technical, physical, mental, GK-specific)
- `Player` - complete model with contract, stats, morale, fitness, form, injury status
- `PlayerSeasonStats` - appearances, goals, assists, clean sheets, cards, rating

**Club Entity:**
- `Club` - name, facilities, finances, reputation, stadium, colors
- `ClubFinance` - balance, budgets, wage bill, income sources

**Match Entities:**
- `TeamTactics` - formation, mentality, tactical sliders, starting XI, bench
- `MatchEvent` - minute, type, player, description
- `MatchResult` - home/away scores, events, stats, attendance, revenue
- `MatchStats` - shots, possession, fouls, corners, saves

**Game State:**
- `GameState` - current season, date, user club, RNG seed, day count
- `Fixture` - home/away clubs, date, result, competition
- `InboxMessage` - category, subject, body, read status, action data

**Database Schema:**
- **tables:** game_state, clubs, players, fixtures, matches, transfers, contracts, messages, competitions, etc.
- **Features:** WAL mode, foreign keys enabled, schema migrations with drift repair

---

### 8. LOCALIZATION & INTERNATIONALIZATION

**200+ Translated Strings** (`localization.py` - 59,962 LOC)

**Supported Languages:**
- English (default)
- Arabic (العربية) with RTL layout support

**Coverage:**
- Navigation, match events, league table headers
- Player attributes, positions, tactics
- Transfers, board/finance, training
- Cup-specific messages, Ramadan notifications, settings
- Bilingual club & player names in database

**Language Toggle:** In Settings, with persistent preference saved to database

---

### 9. TESTING SUITE

**Test Files (1,257 LOC total, 11 files):**

| Test File | Focus | LOC |
|-----------|-------|-----|
| `test_match_engine.py` | Match simulation, event generation | 218 |
| `test_league.py` | Fixture generation, standings | 134 |
| `test_database_connection.py` | SQLite connection, schema | 89 |
| `test_fixture_lineup_persistence.py` | XI/bench persistence across matches | 123 |
| `test_match_flow_reliability.py` | Match flow consistency | 145 |
| `test_player.py` | Player rating, development | 113 |
| `test_tactics.py` | Formation, team strength | 111 |
| `test_training.py` | Training system, development | 125 |
| `test_gameplay_depth.py` | Integration gameplay | 112 |
| `test_finance.py` | Financial modeling | 53 |
| `test_live_ticker_responsiveness.py` | Live match UI responsiveness | 32 |

**Run Tests:**
```bash
pytest tests/ -v                                    # All tests
pytest tests/ --cov=src --cov-report=term-missing  # With coverage
```

---

### 10. SEED DATA & INITIAL SETUP

**`data/seed/clubs.json`** - 18 Fictionalized Egyptian Premier League Clubs
- Examples: Nile United FC, Pharaohs SC, Sphinx Athletic
- Each with reputation, facilities, youth rating, stadium info, finances
- Bilingual names (Arabic العربية)

**`data/seed/governorates.json`** - 27 Regional Talent Profiles
- Talent pool levels (very_high, high, medium, low, very_low)
- Style biases (technical, physical, defensive, creative, pacy, etc.)
- Attribute bonuses (Cairo: dribbling+2, first_touch+2, vision+1)
- Player volume multipliers (Cairo 1.5x, Alexandria 1.2x, Suez 0.6x)

**`data/seed/competitions.json`** - League & Cup Structures

**`data/seed/rivalries.json`** - 5 Derby Rivalries with intensity profiles

---

### 11. KEY ARCHITECTURAL DECISIONS

1. **Clean Separation:** Core simulation layer completely decoupled from UI (uses Pydantic, not Flet)
2. **Deterministic RNG:** Seeded random number system for reproducible results
3. **SQLite Portability:** Lightweight database that runs on mobile without external dependencies
4. **Pydantic v2:** Type-safe, validated data models throughout
5. **No External Graphics:** Pure Flet UI (Flutter-backed) - no GPU dependencies
6. **Realistic Financial Tracking:** Every EGP accounted for across transfers, wages, events, attendance
7. **AI Parity:** AI clubs train, transfer, and develop like the player's club
8. **Mobile-First Design:** Portrait layout, card-based UI, one-handed navigation, dark OLED-friendly theme

---

### 12. ENTRY POINTS

**Main Entry:** `/A/Projects/pharaoh-engine/pharaoh-engine/main.py`
- Applies Windows asyncio shutdown patch (benign error suppression)
- Imports and runs `src.ui.app.run_app()`

**Run the Game:**
```bash
python main.py                    # Desktop window
flet run --web main.py           # Web app
flet build apk                   # Android
flet build ipa                   # iOS
```

---

### 13. FILE SIZE & SCOPE SUMMARY

| Layer | Files | LOC | Purpose |
|-------|-------|-----|---------|
| **Core Simulation** | 20 | 6,335 | Pure Python logic (no UI deps) |
| **Data Layer** | 5 | 3,015 | SQLite, Pydantic models, queries |
| **UI Layer** | 27 | 9,970 | Flet screens, widgets, navigation |
| **Utils** | 4 | 13,363 | Config, RNG, localization |
| **Tests** | 11 | 1,257 | Comprehensive test coverage |
| **Total** | 67 | ~33,940 | Complete game simulation & UI |

---

### 14. PROJECT MATURITY & FEATURES

**Completion Status:**
- ✅ Phase 1 (MVP) - Single-season league simulation
- ✅ Phase 2 (Depth) - Multi-season career, transfers, training, events, AI management
- ✅ Phase 3 (Culture) - Egypt Cup, derby rivalries, Ramadan integration, full Arabic localization
- 🔄 Phase 4 (Launch) - Mobile deployment, enhanced fan ultras, CAF Champions League, etc.

**Key Achievements:**
- 450+ procedurally generated players with 32+ attributes
- 18 fictionalized clubs with realistic budgets and facilities
- 34-matchday double round-robin league with standings
- 32-team Egypt Cup knockout tournament
- 5 named derby rivalries
- 8 training programs with realistic growth mechanics
- Full financial system with EGP-scale transactions
- Complete contract/transfer market simulation
- Board objectives and season evaluation
- 200+ translated Arabic strings with RTL support
- Ramadan calendar integration (2025-2035)
- Career achievements and statistics tracking
- Mobile-optimized Flet UI with bottom navigation

---

This is a **sophisticated, well-architected football management simulation** with emphasis on Egyptian authenticity, clean code separation, and mobile deployment. The three-layer architecture (core simulation, data persistence, UI) demonstrates professional software design patterns suitable for scaling to mobile platforms and additional game modes.