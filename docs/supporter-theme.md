# Gameplay fixes and optional Supporter theme

Classic remains the default navy/gold theme. In Settings > Appearance choose Supporter (المدرج) for the orange/teal candidate. The choice persists across launches and can be reversed without changing a career. Shared components resolve palette values at render time, including screens already imported before switching.

## Design and source boundaries

This is an unofficial, original UI interpretation inspired by public Erza3 graphics. No Erza3 logo, host likeness, thumbnail, photography, or other brand artwork is shipped. Official partnership and asset permission are not established.

The [official channel](https://www.youtube.com/@erza3ma3serry) and [Arcade Films](https://www.arcadeeg.com/) publicly show orange, teal, white and charcoal in the channel identity. Channel thumbnails use bold outlined Arabic titles, faces, collages and corner accents; these are observations, not an official design system. [Podcast example](https://www.youtube.com/watch?v=9bn2yVgejSs), [fantasy example](https://www.youtube.com/watch?v=Elc5qhunThE). The [related physical game](https://store.arcadeeg.com/products/raz3-el-gomhoor-%D8%B1%D8%B2%D8%B9-%D8%A7%D9%84%D8%AC%D9%85%D9%87%D9%88%D8%B1) provides context, not permission.

Exact brand colors and font families are unverified. Implemented colors are design choices: background #11191F, surface #23343E, orange text #FFAC7A, primary button #AA3D10, teal #69C5DD, text #F5F3ED. Roboto/system Arabic fallback remains; no claimed official font is included. The candidate uses teal header rules, opaque charcoal cards, restrained orange accents and original football copy. Semantic injury, fitness and position colors retain their meaning. Classic gains larger base text and clearer muted labels.

## Correctness changes

- Live substitutions now replay the same isolated match seed with validated commands. The already displayed history stays intact; future events, score, ratings and stats come from the same simulation. World randomness is untouched by a substitution.
- Only active players may leave and only unused submitted substitutes may enter, with a three-substitution limit. Dismissed players cannot return. Incoming players start fresh and affect team strength.
- Penalty goals count in the live scoreboard and player records. Appearance minutes and fatigue account for substitutes and dismissals.
- Navigation cancels old match playback; dismissing a substitute picker resumes it. The match retains the app root. Notification dismissal uses the page task lifecycle.
- Match speed is respected. Tutorial and empty-save controls use APIs available in the pinned Flet version. Settings without a career no longer creates a ghost save. Language and appearance persist independently of a career.
- Saves use Flet app storage when available, with PHARAOH_SAVE_DIR for explicit overrides. Tests isolate all saves from user careers.

## Running and validation

Use Python 3.11+ and install requirements.txt for desktop, or requirements-web.txt for the local web preview. Run `python main.py`; run `python -m pytest -q` for tests. Flet is pinned to 0.80.5 because the existing UI still uses legacy controls. The web requirements also pin FastAPI 0.115.12 for this Flet server compatibility.

140 tests pass, including seeded substitution replay regressions, persisted penalties/minutes, runtime theme switching, and construction of eleven career screens in both English/Arabic and both themes. A local browser smoke check covered menu, settings/theme switch, career creation/loading, tutorial, squad, kickoff, halftime and full time. Desktop browser screenshots are supplied separately. Android/iOS packaging, device performance, enlarged text, and full-season soak testing remain unverified.

## Framework decision

Keep Flet for this local single-player candidate while testing on the intended phone. The engine remains independent of Flet. Do not fork the framework merely to change branding. Next priorities are extracting match/day orchestration into a session service, completing translation coverage, and migrating legacy controls deliberately before upgrading Flet.

The application still uses process-global app/database/theme state. This branch is NOT a public multi-user hosting implementation: use one local player/session per process. A hosted version needs per-session state and database ownership before release. Existing Flet deprecation warnings remain. The replay context is in memory; resuming a partially played match after process exit is not implemented.
