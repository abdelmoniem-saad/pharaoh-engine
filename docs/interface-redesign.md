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
