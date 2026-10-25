# Launch readiness — updated 25 October 2026

Recommendation: private single-player playtest; do not announce a public release yet.
This is a scoped code and interface review, not certification of every game system.

## Initial fixes — 24 October 2026

- Inbox rows and message details now translate known stored English templates into Arabic at display time. Existing careers benefit without rewriting their archive or transfer payloads. Daily, medical, training, standard match reports, board, finance and negotiation templates are covered. Unrecognized prose remains visible with an explicit original-language notice. User-entered names remain intact.
- Settings now prioritize language, appearance and match playback, save speed immediately, show persistence failures, and offer a real backup for active careers. Destructive career management is separated and collapsed.
- Removed misleading difficulty and autosave controls from the screen. Difficulty had no simulation consumer; the calendar already saves state every advance. Legacy fields remain compatible with existing saves.
- Transfer execution now rejects an outdated seller/player relationship before changing any balances. The inbox displays an unavailable-offer message instead of crashing. This prevents accepting the same completed offer twice while the player belongs to the buyer; it is not a complete persistent offer-lifecycle solution.

## Release gates

| Priority | Gap | Evidence / required completion |
|---|---|---|
| Implemented; retain coverage checks | Bilingual news/event content | The catalog now covers all current random news, derby/cup headlines, interactive choices/outcomes, press conferences, board reviews, season transitions, loan/transfer and development news. Source-driven checks exercise every random/interactive/press variant and a real season transition. Unrecognized historical/custom prose is retained with a notice. Future wording changes must add reviewed translations; stable template IDs remain a possible architectural improvement. |
| Implemented | Durable incoming-offer lifecycle | Schema migration 16 adds independent pending/accepted/declined/expired records. Decisions persist across reloads. Offers expire after seven days or at window close, with ownership/buyer funds rechecked. The player move, both balances and decision commit together. Legacy letters are imported once; old read flags never imply a decision. Outgoing multi-round negotiations retain their separate existing workflow. |
| Must verify | Career reliability | Run multiple complete seasons, promotion/relegation, cup progression, expiring contracts, financial stress and reloads. Verify interrupted writes, backup restore and save migration on the release build. Existing unit tests do not establish these guarantees. |
| Must verify | Actual target-device experience | Test the packaged application on intended devices: small screens, Arabic long names, text scaling, keyboard navigation, resume after interruption and performance during simulation. Browser rendering is not packaging/device validation. |
| Conditional blocker | Shared web hosting | `src/ui/app.py` holds module-global app_state; locale/theme and database connections also use shared process state. Do not host independent users in one process without per-session state/storage isolation. Local single-player distribution has a different risk profile. |

## Why the experience still feels unfinished

This is a product-design judgment, not a claim that these features are entirely absent. The screens now have a shared visual system, but the next pass should strengthen the manager's decision loop:

1. A clear daily briefing: the next fixture, the most urgent squad issue, the board expectation, and one obvious next action.
2. Better decision feedback: explain why a negotiation failed, what a training change affects, and what a result means for the season. Link a relevant message directly to its task.
3. A guided first week, so a new player can select a lineup, understand tactics, play, and interpret the result without needing outside explanations.
4. A meaningful season arc: escalating objectives, visible consequences, and satisfying milestones. Validate balance with people playing complete careers before adding more menus.

Do not replace Flet merely to resolve these issues: translation coverage, durable decisions, onboarding and playtesting are product/architecture work regardless of UI framework. Reconsider it only against measured target-device performance and interaction requirements.

## Validation — 24 October baseline

152 automated tests passed after the settings, inbox and transfer guard changes. Regression coverage includes existing-message translation, English restoration, action-payload preservation, unsupported-text notices, immediate setting persistence, write failure recovery and repeat-transfer rejection. Existing all-screen theme/RTL checks remain green. Actual Arabic settings and inbox were rendered using a disposable career; screenshots are supplied separately. No official logo or endorsement is included, and the default branch remains unchanged.


## First pair completed — 25 October 2026

Changes are on `codex/gameplay-fixes-supporter-theme`; main is untouched.

- Existing saved English messages are translated for display without rewriting their archived source or action payload. Known player/club names and club abbreviations use available Arabic names; user-entered proper names are preserved.
- Live event and press-conference dialogs use the same catalog as the inbox, including choices and reactions. Player-talk feedback and breaking-news banners also use it.
- Terminal incoming bids show status in the inbox and have no accept/decline buttons. A completed decision is immutable. Accepting one bid expires competing pending bids for that player. An old save cannot tell us whether a historically read offer was declined; we do not invent that history. Already-stale offers expire on import.
- The free-agent path remains valid when the seller is represented as zero and the player's club is null.
- 243 tests passed, including migration/import, expiry/window boundaries, insufficient balance/budget, immutable decisions after reload, competing bids, concurrent accept callbacks, write rollback, both-language resolved dialogs, every authored random/interactive/press branch, parameter preservation, and a generated season transition. Existing theme/RTL screen tests remain green.
- An Arabic event dialog was visually checked in the browser. The subsequent resolved-offer screenshot could not be captured because browser control timed out; its actual Flet controls were verified in both languages by tests. This does not replace the packaged-device testing in item 3.

Next pair remains: multi-season/recovery/packaged-device testing, then guided first-week priorities. No public launch recommendation yet.
