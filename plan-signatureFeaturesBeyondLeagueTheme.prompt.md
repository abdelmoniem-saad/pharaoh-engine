## Plan: Signature Features Beyond League Theme

Build four “must-talk-about” systems that feel uniquely Egyptian and drive retention: Ultras Politics, Promises & Press Heat, Street Football Talent Hunts, and Derby Week Drama. Each system plugs into your existing `fans`, `events`, `media`, `board`, and `inbox` loops, so it is practical (not a rewrite) and creates meaningful decisions with delayed consequences, not one-click flavor text.

### Steps
1. Add **Ultras Politics** state in [src/data/database.py](src/data/database.py) and logic in [src/core/fans.py](src/core/fans.py) via `ultras_trust`, `choreo_momentum`, `protest_risk`.
2. Implement weekly **Ultras actions** in [src/core/events.py](src/core/events.py) where choices affect atmosphere, attendance, injuries, and home boost in `calculate_attendance`.
3. Add **Manager Promises System** in [src/core/board.py](src/core/board.py) and [src/core/media.py](src/core/media.py) with promise deadlines and credibility penalties/rewards.
4. Create **Street Tournament Scouting** in [src/core/youth.py](src/core/youth.py) and [src/core/regional.py](src/core/regional.py): discover raw players, choose risky/cheap development paths.
5. Build **Derby Week Mode** in [src/core/rivalries.py](src/core/rivalries.py), [src/ui/screens/match_day.py](src/ui/screens/match_day.py), [src/ui/screens/live_match.py](src/ui/screens/live_match.py): 5-day narrative arc before derby kickoff.
6. Present all consequences in one **Club Pulse feed** in [src/ui/screens/club_overview.py](src/ui/screens/club_overview.py) and [src/ui/screens/inbox.py](src/ui/screens/inbox.py) using clear “this choice caused this outcome” chains.
7. Make the manager play fantasy for his league, this will force player to know the competitors players more.