# ⚽ Pharaoh Engine

**Mobile-first Egyptian Football Management Simulation Game**

A deeply authentic football management game centered on the Egyptian league ecosystem. Combines casual accessibility with hardcore simulation depth — inspired by Football Manager but built specifically for Egyptian football culture.

## 🎮 Features (MVP / Phase 1)

- **18 fictionalized Egyptian Premier League clubs** with realistic reputations, finances, and squad sizes
- **Procedurally generated ~450 players** with position-specific attributes, governorate origins, and varied potential
- **Full season simulation** — 34-matchday double round-robin league
- **Minute-by-minute match engine** producing goals, assists, cards, and match statistics
- **Tactical system** with 7 formations, 6 casual presets, and adjustable mentality
- **Auto-selection AI** for team lineups weighted by position suitability, form, and fitness
- **League table** with proper points, goal difference, and standings sorting
- **Player fitness, form, and morale** tracking with match impact
- **Financial modeling** with income, expenses, and budget management
- **Board confidence and objectives** system
- **Fan happiness and attendance** mechanics
- **Regional talent dynamics** — 17 Egyptian governorate profiles with attribute biases
- **Save/load** via SQLite
- **Deterministic RNG** — seeded randomness for reproducible simulations
- **Inbox/news system** with match reports

## 🏗️ Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11+ |
| Mobile UI | Kivy + KivyMD |
| Database | SQLite (stdlib) |
| Data Models | Pydantic v2 |
| Android Build | Buildozer |
| iOS Build | kivy-ios |
| Testing | pytest |

## 📁 Project Structure

```
pharaoh-engine/
├── main.py                  # App entry point
├── buildozer.spec           # Android/iOS build config
├── src/
│   ├── core/                # Simulation engine (pure Python, no UI deps)
│   │   ├── match_engine.py  # Match simulation
│   │   ├── player.py        # Player ratings, fitness, form
│   │   ├── tactics.py       # Formations, presets, team selection
│   │   ├── club.py          # Club management, AI tactics
│   │   ├── league.py        # Fixture generation, standings
│   │   ├── calendar.py      # Game loop, day advancement
│   │   ├── finance.py       # Income, expenses, budgets
│   │   ├── youth.py         # Player development pipeline
│   │   ├── board.py         # Board objectives, confidence
│   │   ├── media.py         # Headlines, press system
│   │   ├── fans.py          # Ultras, attendance, atmosphere
│   │   ├── transfers.py     # Transfer market
│   │   ├── regional.py      # Governorate talent profiles
│   │   └── competition.py   # Cup/continental stubs
│   ├── data/                # Database & data layer
│   │   ├── database.py      # SQLite schema & connection
│   │   ├── models.py        # Pydantic data models
│   │   ├── queries.py       # CRUD operations
│   │   └── seed.py          # Player/club generation
│   ├── ui/                  # Kivy UI layer
│   │   ├── app.py           # App class, screen manager
│   │   ├── screens/         # Game screens
│   │   └── widgets/         # Reusable UI components
│   └── utils/               # Utilities
│       ├── config.py        # Constants, enums, settings
│       ├── rng.py           # Seeded RNG system
│       └── localization.py  # English/Arabic string tables
├── data/seed/               # JSON seed data
│   ├── clubs.json           # 18 EPL clubs
│   ├── governorates.json    # Regional talent profiles
│   └── competitions.json    # League/cup structures
└── tests/                   # Test suite
```

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

# Run the game (desktop)
python main.py

# Run tests
pytest tests/ -v
```

### Build for Android
```bash
pip install buildozer
buildozer android debug
```

## 🗺️ Development Roadmap

### Phase 1 — MVP ✅ (Current)
Single-season league simulation with squad management, tactical presets, and match engine.

### Phase 2 — Depth (Next)
Transfers, youth academy, save/load, Egypt Cup, board objectives, detailed financial modeling.

### Phase 3 — Culture
Fan ultras system, Arabic localization, governorate talent dynamics, CAF Champions League, enhanced match narratives.

### Phase 4 — Launch
Mobile deployment (Play Store/App Store), onboarding tutorial, ethical F2P monetization, community features.

## 🎯 Design Philosophy

1. **Casual surface, deep core** — Easy to pick up with presets and auto-select; advanced users can tweak every tactical slider
2. **Egyptian authenticity** — Governorate-specific talent, realistic financial scale, culturally accurate fan dynamics
3. **Lean architecture** — Pure Python simulation engine separated from UI; runs fast on mobile hardware
4. **Deterministic simulation** — Seeded RNG ensures reproducible results for testing and fairness
5. **Unlicensed start** — Fictionalized names with accurate structures; official licensing as traction grows

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
