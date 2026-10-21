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

This is a substantially revised interface candidate, not evidence of store readiness. Secondary dialogs retain parts of the older UI; a dedicated font system, full Arabic editorial pass, accessibility/text-scaling checks, device performance and player usability testing remain necessary before a commercial release. Desktop uses a bounded workspace rather than a separate desktop navigation architecture.
