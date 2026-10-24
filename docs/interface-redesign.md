# Interface redesign review

The earlier theme pass retained too much of the original card layout. This revision changes the interface structure as well as its colors.

## Implemented

- A new opening screen with editorial typography, an original pitch diagram, and a prominent resume/new-career action. New players see New Game as the primary action.
- A squad workspace with visible summary metrics, football-order position groups, aligned player/rating/condition columns, and meaningful status icons. Other sorting modes produce a continuous ranked list instead of repeated position headings. Player detail and comparison actions remain.
- A match fixture with club monograms, clear competition/date hierarchy and one prominent action. Supporting analysis and guidance are progressively disclosed below it.
- Shared opaque panels, quieter borders, larger headings, consistent spacing, and flatter navigation in both themes. Classic uses slate and muted gold; Supporter uses charcoal, orange and teal. They remain selectable in Settings.
- Cleaner settings, expanded theme selectors with palette swatches, roomier table rows, and a less cramped live-match scoreboard. Large displays use a centered 800px workspace rather than stretching mobile rows across the entire window.
- Corrected a squad sort fallback crash and repeated position grouping. Returning to the main menu no longer invokes legacy save migration while a career connection is open.

## Validation and limits

142 tests pass, with expanded smoke coverage for the main menu and every squad sort mode in both languages and palettes. Actual browser renders were checked at 390px for Classic squad and Supporter match, and 360px for Arabic Supporter. The comparison screenshot shows actual running game controls, not an image mockup.

No match simulation or career schema changes are part of this revision. No third-party logo, photography, or host likeness is included. Existing brand-source and unofficial-concept caveats still apply.

This is a substantially revised interface candidate, not evidence of store readiness. Secondary dialogs retain parts of the older UI; a full Arabic editorial pass, accessibility/text-scaling checks, device performance and player usability testing remain necessary before a commercial release. Desktop uses a bounded workspace rather than a separate desktop navigation architecture.

## Career screens — 23 October 2026

This revision adds a projected-XI tactics board with actual player names, shirt numbers and clickable dossiers. Final team selection remains in the pre-match screen. Tactical sliders save on release instead of rebuilding the screen during a drag, and preset selection reflects all tactical settings.

Player dossiers now separate overview, attributes and development. Existing captain, conversation, transfer-list, contract, training and development actions remain accessible under Development. Arabic overlays explicitly use RTL, and core profile labels have translations. Attribute bars adapt to available width.

The club screen has a club identity panel, board/fan/position metrics and a compact next-fixture brief. The result screen now prioritizes the score and next action, with separate Report, Top Performers and Elsewhere sections. Penalty scorers are included in the report.

Fonts are bundled with their OFL licenses: Barlow Condensed Bold for English display text and Noto Sans Arabic for Arabic text. These are original UI choices, not official Erza3 typography. Source links and licenses are in assets/fonts. Launch through python main.py so the configured assets directory is served; custom Flet launchers must also supply the repository assets directory.

Validation: 142 tests pass with expanded coverage for dossier tabs, post-match penalty events and slider persistence. Browser previews verify the actual tactics, club and Arabic dossier screens at 390px. Existing limitations around multi-user hosting, mobile build verification and untranslated secondary dialogue content still apply.


## Complete screen pass — 24 October 2026

All 15 screen modules and shared widgets now set direction explicitly. Flet's per-control RTL default is false: setting only page.rtl did not mirror nested rows, fields, dialog content or navigation. Arabic layouts put labels and leading content on the right and trailing values/actions on the left. Physical text alignment, back arrows and leading borders are mirrored. Scoreline ordering is handled separately so home/away scores remain next to the correct clubs.

The secondary screens received these additional changes:

- Transfers: prominent budget, consistent form surfaces, readable labeled tabs, larger player rows and wrapped metadata. The Any-position option now uses a stable empty key, fixing Arabic search.
- Fixtures: rebuilt fixture cards, synchronized competition selection, and a working Flet on_select matchday callback. Names use localized data when available.
- Competition: compact, aligned standings with room for team names. Tap a team for its complete played/won/drawn/lost/goal-difference/points record. Cup rows and labels follow the same direction.
- Inbox: larger message rows and filter targets, mirrored navigation and category markers.
- History: localized tab labels and empty states, larger record rows.
- Season summary: club metrics, primary next-season action, and separate review/awards tabs.
- Every screen: explicit control direction, consistent form styling and themed dialogs. Profile attribute values are on the left in Arabic, with complete category labels on the right.

### Screen coverage

| Screen | Work checked |
|---|---|
| Main menu / new and load career dialogs | Direction, forms and actions |
| Squad / player profiles | Mirrored roster, numbers, attributes and tabs |
| Tactics | Formation selectors, pitch labels, sliders and presets |
| Club | Identity, finance/stat rows and tabs |
| Transfers | Search, shortlist, sell/free-agent/negotiation panels and dialog direction |
| Competition | League/cup layout and team detail |
| Fixtures | Competition/matchday selection and score pairing |
| Matchday | Fixture cards, supporting rows and direction |
| Pre-match | Lineup, bench, fields and primary action |
| Live match | Score pairing, event feed, actions and substitution dialog direction |
| Post-match | Report, ratings, results and score pairing |
| Inbox | Filters, rows and message/offer dialogs |
| History | Tabs, records and empty states |
| Season summary | Metrics, review, awards and next-season confirmation |
| Settings | Language/theme controls, fields, switches and confirmation dialogs |

Automated validation constructs every screen in both languages and both themes, checks nested layout direction, exercises fixture selectors and transfer search, and checks asymmetric score ordering. Browser checks use disposable QA saves. A code/control audit is not exhaustive testing of every career state: long generated messages, native packaging, screen-reader behavior, text scaling and device performance still need release testing. Existing saved news and club names can remain English when Arabic content is absent; this pass does not machine-translate stored career data. No simulation or save-schema changes and no third-party brand assets are included.

Final validation: 145 tests passed. All 15 screen types were rendered in the browser during this review; the final preview includes the transfer market, Arabic attributes, revised lineup pitch and an asymmetric match result. Rendering checks used 390px content widths; these are not native-device or exhaustive career-state tests.
